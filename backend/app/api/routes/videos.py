"""视频上传与分析路由"""

import uuid
import logging
import os

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from typing import List

from ...config import get_settings
from ...models.schemas import VideoUploadResponse, BatchUploadResponse
from ..deps import get_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter(tags=["videos"])
settings = get_settings()


@router.post("/videos/upload", response_model=BatchUploadResponse)
async def upload_videos(files: List[UploadFile] = File(...)):
    """上传一个或多个视频文件"""
    if not files:
        raise HTTPException(status_code=400, detail="请上传至少一个视频文件")

    orchestrator = get_orchestrator()
    tasks = []

    for file in files:
        valid_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v')
        if not file.filename.lower().endswith(valid_extensions):
            continue

        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = settings.upload_path / safe_name

        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)

        if file_size_mb > settings.max_upload_size_mb:
            raise HTTPException(
                status_code=413,
                detail=f"文件 {file.filename} 大小 {file_size_mb:.1f}MB 超过限制 {settings.max_upload_size_mb}MB"
            )

        with open(file_path, "wb") as f:
            f.write(content)

        task_id = orchestrator.create_task(str(file_path), file.filename)
        tasks.append(VideoUploadResponse(
            task_id=task_id,
            filename=file.filename,
            size_mb=round(file_size_mb, 2),
        ))

        orchestrator.process_async(task_id)
        logger.info(f"视频已接收: {file.filename} -> {task_id}")

    return BatchUploadResponse(
        message=f"已接收 {len(tasks)} 个视频文件，开始处理",
        tasks=tasks,
    )


@router.get("/video/{task_id}")
def serve_video(task_id: str):
    """Serve original video file for a task — fallback to result JSON if not in memory"""
    orchestrator = get_orchestrator()
    task = orchestrator.get_task(task_id)

    # 1) 内存中的任务
    if task and task.video_path and os.path.exists(task.video_path):
        return FileResponse(task.video_path)

    # 2) 从结果 JSON 中查找 video_path
    import json
    result_file = orchestrator.settings.result_path / f"{task_id}.json"
    if result_file.exists():
        try:
            with open(result_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            vp = data.get("video_path")
            if vp and os.path.exists(vp):
                return FileResponse(vp)
        except Exception:
            pass

    raise HTTPException(status_code=404, detail="视频文件不存在")
