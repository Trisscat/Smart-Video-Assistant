"""历史记录与结果查询路由"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ...models.schemas import HistoryResponse, MessageResponse
from ..deps import get_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter(tags=["history"])


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取历史记录（分页）"""
    orchestrator = get_orchestrator()
    history = orchestrator.get_history()
    total = len(history)
    start = (page - 1) * page_size
    end = start + page_size
    return HistoryResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=history[start:end],
    )


@router.delete("/history/{task_id}", response_model=MessageResponse)
async def delete_history(task_id: str):
    """删除历史记录"""
    orchestrator = get_orchestrator()
    success = orchestrator.delete_history_entry(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    return MessageResponse(message="历史记录已删除")


@router.get("/results/{task_id}")
async def get_full_result(task_id: str):
    """获取完整的分析结果（用于展示页面）"""
    orchestrator = get_orchestrator()
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
        "highlights": result["result"].get("highlights", ""),
        "paragraphs": result["result"].get("paragraphs", ""),
        "translation": result["result"].get("translation"),
        "video_path": result.get("video_path", ""),
        "created_at": result["created_at"],
        "completed_at": result["completed_at"],
    }
