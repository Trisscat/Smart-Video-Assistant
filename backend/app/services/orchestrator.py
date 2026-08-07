"""
视频处理调度器 - 多线程并发处理视频
支持：上传、排队、并行处理、进度追踪、取消操作
"""
import os
import json
import uuid
import shutil
import logging
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field

from ..config import get_settings
from .audio_utils import extract_audio
from .transcriber import VideoTranscriber
from ..chains.video_analysis import analyze_video

logger = logging.getLogger(__name__)


@dataclass
class VideoTask:
    """视频处理任务"""
    task_id: str
    filename: str
    original_filename: str
    status: str  # pending / extracting / transcribing / analyzing / completed / failed / cancelled
    progress: int = 0
    progress_message: str = ""
    error_message: Optional[str] = None
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    duration: Optional[float] = None
    language: Optional[str] = None
    segments: Optional[List[Dict]] = None
    cancelled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "filename": self.original_filename,
            "status": self.status,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "duration": self.duration,
            "language": self.language,
        }

    def to_result_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "filename": self.original_filename,
            "language": self.language,
            "duration": self.duration,
            "segments": self.segments,
            "result": self.result,
            "video_path": self.video_path,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class VideoProcessingOrchestrator:
    """视频处理编排器"""

    def __init__(self):
        self.settings = get_settings()
        self.transcriber: Optional[VideoTranscriber] = None
        self.executor = ThreadPoolExecutor(
            max_workers=self.settings.max_concurrent_videos,
            thread_name_prefix="video-worker",
        )
        self.tasks: Dict[str, VideoTask] = {}
        self.futures: Dict[str, Future] = {}
        self.progress_callbacks: Dict[str, List] = {}  # task_id -> [callbacks]

        # 加载历史记录
        self._load_history()

    def init_models(self, whisper_model):
        """初始化模型"""
        self.transcriber = VideoTranscriber(whisper_model)

    # ==================== 任务管理 ====================

    def create_task(self, video_path: str, original_filename: str) -> str:
        """创建处理任务"""
        task_id = str(uuid.uuid4())
        task = VideoTask(
            task_id=task_id,
            filename=Path(video_path).name,
            original_filename=original_filename,
            status="pending",
            video_path=video_path,
        )
        self.tasks[task_id] = task
        return task_id

    def get_task(self, task_id: str) -> Optional[VideoTask]:
        """获取任务"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务"""
        return [t.to_dict() for t in self.tasks.values()]

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.cancelled = True
        if task.status in ("pending", "extracting", "transcribing"):
            task.status = "cancelled"
            task.progress_message = "任务已取消"

            # 取消Future
            future = self.futures.get(task_id)
            if future and not future.done():
                future.cancel()

            # 清理临时文件
            self._cleanup_task_files(task)
            return True

        return False

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False

        # 如果正在处理，先取消
        if task.status in ("pending", "extracting", "transcribing", "analyzing"):
            self.cancel_task(task_id)

        self._cleanup_task_files(task)
        del self.tasks[task_id]
        self.futures.pop(task_id, None)
        return True

    def _cleanup_task_files(self, task: VideoTask):
        """清理任务临时文件（保留视频，只删音频）"""
        # 保留视频文件 — 结果页需要播放
        # 只清理提取的临时音频
        if task.audio_path and os.path.exists(task.audio_path):
            try:
                os.remove(task.audio_path)
            except Exception as e:
                logger.warning(f"清理音频文件失败: {e}")

    # ==================== 进度回调 ====================

    def register_callback(self, task_id: str, callback):
        """注册进度回调"""
        if task_id not in self.progress_callbacks:
            self.progress_callbacks[task_id] = []
        self.progress_callbacks[task_id].append(callback)

    def unregister_callbacks(self, task_id: str):
        """取消注册回调"""
        self.progress_callbacks.pop(task_id, None)

    def _update_progress(self, task_id: str, progress: int, message: str, status: str = None):
        """更新进度并通知回调"""
        task = self.tasks.get(task_id)
        if not task:
            return

        task.progress = progress
        task.progress_message = message
        if status:
            task.status = status

        # 通知回调 — 同步/异步兼容
        callbacks = self.progress_callbacks.get(task_id, [])
        data = task.to_dict()
        for cb in callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    # 异步回调（WebSocket）— 在事件循环中调度
                    try:
                        loop = asyncio.get_running_loop()
                        asyncio.run_coroutine_threadsafe(cb(data), loop)
                    except RuntimeError:
                        # 没有运行中的事件循环，降级处理
                        pass
                else:
                    cb(data)
            except Exception as e:
                logger.error(f"进度回调执行失败: {e}")

    # ==================== 处理流程 ====================

    def process_async(self, task_id: str):
        """异步处理视频"""
        future = self.executor.submit(self._process_video, task_id)
        self.futures[task_id] = future
        future.add_done_callback(lambda f: self._on_task_done(task_id, f))

    def _on_task_done(self, task_id: str, future: Future):
        """任务完成回调"""
        try:
            future.result()
        except Exception as e:
            task = self.tasks.get(task_id)
            if task and task.status not in ("cancelled", "completed"):
                task.status = "failed"
                task.error_message = str(e)
                task.progress_message = f"处理失败: {e}"
                logger.error(f"任务 {task_id} 失败: {e}")
            self._update_progress(task_id, 100, f"处理失败: {e}", "failed")

    def _check_cancelled(self, task_id: str) -> bool:
        """检查是否已取消"""
        task = self.tasks.get(task_id)
        return task and task.cancelled

    def _process_video(self, task_id: str):
        """
        完整的视频处理流程：
        1. 提取音频
        2. 语音识别（带时间戳）
        3. 多智能体分析
        4. 保存结果
        """
        task = self.tasks.get(task_id)
        if not task:
            return

        # === 第1步：提取音频 ===
        if self._check_cancelled(task_id):
            return
        self._update_progress(task_id, 5, "正在提取音频...", "extracting")

        try:
            audio_path, duration = extract_audio(task.video_path)
            task.audio_path = audio_path
            task.duration = duration
        except Exception as e:
            task.status = "failed"
            task.error_message = f"音频提取失败: {e}"
            logger.error(f"音频提取失败: {e}")
            self._update_progress(task_id, 0, f"音频提取失败: {e}", "failed")
            return

        # === 第2步：语音识别 ===
        if self._check_cancelled(task_id):
            return
        self._update_progress(task_id, 20, "正在进行语音识别...", "transcribing")

        try:
            transcribe_result = self.transcriber.transcribe_for_analysis(audio_path)
            task.segments = transcribe_result["segments"]
            task.language = transcribe_result["language"]
            self._update_progress(task_id, 50, "语音识别完成，开始智能分析...", "transcribing")
        except Exception as e:
            task.status = "failed"
            task.error_message = f"语音识别失败: {e}"
            logger.error(f"语音识别失败: {e}")
            self._update_progress(task_id, 0, f"语音识别失败: {e}", "failed")
            return

        # === 第3步：智能分析（渐进式进度更新） ===
        if self._check_cancelled(task_id):
            return
        self._update_progress(task_id, 55, "正在生成视频总结...", "analyzing")

        try:
            analysis_result = analyze_video(
                transcript=transcribe_result["full_text"],
                language=transcribe_result["language"],
                plain_text=transcribe_result["plain_text"],
                duration=task.duration or 0,
            )
            task.result = analysis_result
            self._update_progress(task_id, 90, "分析完成，正在保存结果...", "analyzing")
        except Exception as e:
            task.status = "failed"
            task.error_message = f"智能分析失败: {e}"
            logger.error(f"智能分析失败: {e}")
            self._update_progress(task_id, 0, f"智能分析失败: {e}", "failed")
            return

        # === 第4步：保存结果 ===
        if self._check_cancelled(task_id):
            return

        try:
            result_data = task.to_result_dict()
            result_file = self.settings.result_path / f"{task_id}.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

            task.completed_at = datetime.now().isoformat()
            task.status = "completed"
            task.progress = 100
            task.progress_message = "处理完成！"

            # 保存到历史记录
            self._save_to_history(task)

            self._update_progress(task_id, 100, "处理完成！点击查看结果", "completed")
            logger.info(f"任务 {task_id} 处理完成")

        except Exception as e:
            task.status = "failed"
            task.error_message = f"结果保存失败: {e}"
            logger.error(f"结果保存失败: {e}")
            self._update_progress(task_id, 0, f"保存失败: {e}", "failed")

        finally:
            # 清理临时文件（临时处理模式）
            self._cleanup_task_files(task)

    # ==================== 历史记录 ====================

    def _load_history(self):
        """加载历史记录"""
        self.history: List[Dict] = []
        history_file = Path(self.settings.history_file)
        if history_file.exists():
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception as e:
                logger.warning(f"加载历史记录失败: {e}")

    def _save_to_history(self, task: VideoTask):
        """保存到历史记录"""
        entry = {
            "task_id": task.task_id,
            "filename": task.original_filename,
            "language": task.language,
            "duration": task.duration,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
            "status": task.status,
        }
        self.history.insert(0, entry)
        self._save_history()

    def _save_history(self):
        """保存历史记录到文件"""
        history_file = Path(self.settings.history_file)
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")

    def get_history(self) -> List[Dict]:
        """获取历史记录"""
        return self.history

    def get_result(self, task_id: str) -> Optional[Dict]:
        """获取分析结果"""
        # 先从内存中查找
        task = self.tasks.get(task_id)
        if task and task.result:
            return task.to_result_dict()

        # 从文件加载
        result_file = self.settings.result_path / f"{task_id}.json"
        if result_file.exists():
            with open(result_file, "r", encoding="utf-8") as f:
                return json.load(f)

        return None

    def delete_history_entry(self, task_id: str) -> bool:
        """删除历史记录"""
        self.history = [h for h in self.history if h.get("task_id") != task_id]
        self._save_history()

        # 删除结果文件
        result_file = self.settings.result_path / f"{task_id}.json"
        if result_file.exists():
            result_file.unlink()

        return True
