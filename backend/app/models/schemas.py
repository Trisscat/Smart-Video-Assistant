"""数据模型 — 与前端 API 契约对齐"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════
# 请求模型
# ═══════════════════════════════════════════════════════════════

class VideoUploadResponse(BaseModel):
    """单个视频上传结果"""
    task_id: str
    filename: str
    size_mb: float
    status: str = "pending"


class BatchUploadResponse(BaseModel):
    """批量上传响应"""
    message: str
    tasks: List[VideoUploadResponse]


# ═══════════════════════════════════════════════════════════════
# 任务模型
# ═══════════════════════════════════════════════════════════════

class TaskStatus(BaseModel):
    """任务状态"""
    task_id: str
    filename: str
    status: str  # pending / extracting / transcribing / analyzing / completed / failed / cancelled
    progress: int = 0
    progress_message: str = ""
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration: Optional[float] = None
    language: Optional[str] = None


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[TaskStatus]


# ═══════════════════════════════════════════════════════════════
# 转录模型
# ═══════════════════════════════════════════════════════════════

class TranscriptSegment(BaseModel):
    """转录片段"""
    start: float
    end: float
    text: str


class TranscriptResult(BaseModel):
    """转录结果"""
    segments: List[TranscriptSegment] = Field(default_factory=list)
    full_text: str = ""
    plain_text: str = ""
    language: str = "zh"
    total_segments: int = 0


# ═══════════════════════════════════════════════════════════════
# 分析结果模型
# ═══════════════════════════════════════════════════════════════

class AnalysisResult(BaseModel):
    """多智能体分析结果"""
    summary: str = ""
    meeting_notes: str = ""
    action_items: str = ""
    translation: Optional[str] = None


class FullResult(BaseModel):
    """完整的分析结果（展示页面用）"""
    task_id: str
    filename: str
    language: Optional[str] = None
    duration: Optional[float] = None
    segments: Optional[List[Dict[str, Any]]] = None
    summary: str = ""
    meeting_notes: str = ""
    action_items: str = ""
    translation: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# 历史记录模型
# ═══════════════════════════════════════════════════════════════

class HistoryEntry(BaseModel):
    """历史记录条目"""
    task_id: str
    filename: str
    language: Optional[str] = None
    duration: Optional[float] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "completed"


class HistoryResponse(BaseModel):
    """历史记录分页响应"""
    total: int
    page: int
    page_size: int
    items: List[HistoryEntry]


# ═══════════════════════════════════════════════════════════════
# 通用响应
# ═══════════════════════════════════════════════════════════════

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "ok"
    timestamp: Optional[str] = None
    max_concurrent: int = 4
    version: str = "2.0.0"


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    message: str = ""
    error_code: Optional[str] = None
