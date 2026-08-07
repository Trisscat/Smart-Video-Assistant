"""任务管理路由"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ...models.schemas import (
    TaskStatus,
    TaskListResponse,
    FullResult,
    HistoryResponse,
    MessageResponse,
)
from ..deps import get_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tasks"])


@router.get("/tasks", response_model=TaskListResponse)
async def get_all_tasks():
    """获取所有任务状态"""
    orchestrator = get_orchestrator()
    return TaskListResponse(tasks=orchestrator.get_all_tasks())


@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """获取单个任务状态"""
    orchestrator = get_orchestrator()
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task.to_dict()


@router.get("/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    """获取任务分析结果"""
    orchestrator = get_orchestrator()
    result = orchestrator.get_result(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="结果不存在或尚未完成")
    return result


@router.delete("/tasks/{task_id}", response_model=MessageResponse)
async def delete_task(task_id: str):
    """删除/取消任务"""
    orchestrator = get_orchestrator()
    success = orchestrator.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return MessageResponse(message="任务已删除")


@router.post("/tasks/{task_id}/cancel", response_model=MessageResponse)
async def cancel_task(task_id: str):
    """取消正在处理的任务"""
    orchestrator = get_orchestrator()
    success = orchestrator.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在或无法取消")
    return MessageResponse(message="任务已取消")
