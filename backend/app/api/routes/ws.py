"""WebSocket 进度推送路由"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..deps import get_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ws"])


@router.websocket("/ws/progress/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    """WebSocket - 实时推送处理进度"""
    orchestrator = get_orchestrator()
    await websocket.accept()

    task = orchestrator.get_task(task_id)
    if task:
        await websocket.send_json(task.to_dict())

    async def progress_callback(data):
        try:
            await websocket.send_json(data)
        except Exception:
            pass

    orchestrator.register_callback(task_id, progress_callback)

    try:
        while True:
            data = await websocket.receive_text()
            if data == "cancel":
                orchestrator.cancel_task(task_id)
                await websocket.send_json({"status": "cancelled"})
                break
    except WebSocketDisconnect:
        pass
    finally:
        orchestrator.unregister_callbacks(task_id)
