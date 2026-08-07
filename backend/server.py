"""
FastAPI 后端服务 - 智能视频助手
提供：视频上传、处理、结果查询、历史记录管理、WebSocket进度推送
"""
import os
import json
import uuid
import shutil
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from config import UPLOAD_DIR, RESULT_DIR, MAX_UPLOAD_SIZE_MB, MAX_CONCURRENT_VIDEOS
from whisper_manager import load_whisper_model
from orchestrator import VideoProcessingOrchestrator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# 全局编排器
orchestrator = VideoProcessingOrchestrator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭生命周期"""
    logger.info("正在初始化Whisper模型...")
    try:
        whisper_model = load_whisper_model()
        orchestrator.init_models(whisper_model)
        logger.info("所有模型初始化完成，服务就绪！")
    except Exception as e:
        logger.error(f"模型初始化失败: {e}")
        logger.warning("服务将在无模型状态下启动，部分功能可能不可用")
    yield
    orchestrator.executor.shutdown(wait=True)


app = FastAPI(
    title="智能视频助手",
    description="基于LangChain的多智能体视频分析系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== REST API ====================

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "max_concurrent": MAX_CONCURRENT_VIDEOS,
    }


@app.post("/api/videos/upload")
async def upload_videos(files: List[UploadFile] = File(...)):
    """
    上传一个或多个视频文件
    返回每个视频的任务ID列表
    """
    if not files:
        raise HTTPException(status_code=400, detail="请上传至少一个视频文件")

    tasks = []

    for file in files:
        # 验证文件类型
        valid_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v')
        if not file.filename.lower().endswith(valid_extensions):
            continue  # 跳过不支持的文件

        # 保存视频文件
        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = UPLOAD_DIR / safe_name

        # 写入文件
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)

        if file_size_mb > MAX_UPLOAD_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"文件 {file.filename} 大小 {file_size_mb:.1f}MB 超过限制 {MAX_UPLOAD_SIZE_MB}MB"
            )

        with open(file_path, "wb") as f:
            f.write(content)

        # 创建处理任务
        task_id = orchestrator.create_task(str(file_path), file.filename)
        tasks.append({
            "task_id": task_id,
            "filename": file.filename,
            "size_mb": round(file_size_mb, 2),
            "status": "pending",
        })

        # 异步开始处理
        orchestrator.process_async(task_id)

        logger.info(f"视频已接收: {file.filename} -> {task_id}")

    return {
        "message": f"已接收 {len(tasks)} 个视频文件，开始处理",
        "tasks": tasks,
    }


@app.get("/api/tasks")
async def get_all_tasks():
    """获取所有任务状态"""
    return {"tasks": orchestrator.get_all_tasks()}


@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取单个任务状态"""
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task.to_dict()


@app.get("/api/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    """获取任务分析结果"""
    result = orchestrator.get_result(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="结果不存在或尚未完成")
    return result


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除/取消任务"""
    success = orchestrator.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"message": "任务已删除"}


@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消正在处理的任务"""
    success = orchestrator.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在或无法取消")
    return {"message": "任务已取消"}


@app.get("/api/history")
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取历史记录（分页）"""
    history = orchestrator.get_history()
    total = len(history)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": history[start:end],
    }


@app.delete("/api/history/{task_id}")
async def delete_history(task_id: str):
    """删除历史记录"""
    success = orchestrator.delete_history_entry(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    return {"message": "历史记录已删除"}


@app.get("/api/results/{task_id}")
async def get_full_result(task_id: str):
    """获取完整的分析结果（用于展示页面）"""
    result = orchestrator.get_result(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="结果不存在")

    return {
        "task_id": result["task_id"],
        "filename": result["filename"],
        "language": result["language"],
        "duration": result["duration"],
        "segments": result["segments"],
        "summary": result["result"].get("summary", ""),
        "meeting_notes": result["result"].get("meeting_notes", ""),
        "action_items": result["result"].get("action_items", ""),
        "translation": result["result"].get("translation"),
        "created_at": result["created_at"],
        "completed_at": result["completed_at"],
    }


# ==================== WebSocket（进度推送） ====================

@app.websocket("/ws/progress/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    """WebSocket - 实时推送处理进度"""
    await websocket.accept()

    # 发送当前状态
    task = orchestrator.get_task(task_id)
    if task:
        await websocket.send_json(task.to_dict())

    # 注册进度回调
    async def progress_callback(data):
        try:
            await websocket.send_json(data)
        except Exception:
            pass

    orchestrator.register_callback(task_id, progress_callback)

    try:
        while True:
            # 保持连接，接收客户端消息（如取消请求）
            data = await websocket.receive_text()
            if data == "cancel":
                orchestrator.cancel_task(task_id)
                await websocket.send_json({"status": "cancelled"})
                break
    except WebSocketDisconnect:
        pass
    finally:
        orchestrator.unregister_callbacks(task_id)


# ==================== 静态文件服务（生产环境） ====================

frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
