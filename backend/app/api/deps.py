"""FastAPI 依赖注入 — 全局单例管理"""

from ..services.orchestrator import VideoProcessingOrchestrator

_orchestrator: VideoProcessingOrchestrator | None = None


def get_orchestrator() -> VideoProcessingOrchestrator:
    """获取全局编排器单例"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = VideoProcessingOrchestrator()
    return _orchestrator


def set_orchestrator(orch: VideoProcessingOrchestrator) -> None:
    """设置全局编排器（用于启动时初始化）"""
    global _orchestrator
    _orchestrator = orch
