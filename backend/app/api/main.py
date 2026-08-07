"""FastAPI 主应用 — 智能视频助手 API

架构参考 HelloAgents trip-planner:
  - 薄路由层 (routes/) → 链式管道 (chains/) → 外部服务 (services/)
  - 配置通过 pydantic-settings 单例管理
  - LLM 通过统一的工厂函数创建
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from ..config import get_settings, validate_config
from ..services.whisper_manager import load_whisper_model
from .deps import set_orchestrator, get_orchestrator
from .routes import videos, tasks, history, ws

settings = get_settings()

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭生命周期"""
    logger.info("=" * 60)
    logger.info(f"[STARTUP] {settings.app_name} v{settings.app_version}")
    logger.info(f"   LLM: {settings.llm_model_effective}")
    logger.info(f"   Endpoint: http://{settings.host}:{settings.port}")
    logger.info(f"   API docs: http://localhost:{settings.port}/docs")
    logger.info("=" * 60)

    # 校验配置
    validate_config()

    # 初始化 Whisper 模型
    logger.info("正在初始化 Whisper 模型...")
    try:
        whisper_model = load_whisper_model()
        orch = get_orchestrator()
        orch.init_models(whisper_model)
        logger.info("所有模型初始化完成，服务就绪！")
    except Exception as e:
        logger.error(f"模型初始化失败: {e}")
        logger.warning("服务将在无模型状态下启动，部分功能可能不可用")

    yield

    # 关闭线程池
    orch = get_orchestrator()
    orch.executor.shutdown(wait=True)
    logger.info("[SHUTDOWN] Application closing")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于 Chain 框架的多智能体视频分析系统（LangChain 管道架构）",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由（前缀 /api）
app.include_router(videos.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(ws.router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "architecture": "Chain Pipeline (LangChain)",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "max_concurrent": settings.max_concurrent_videos,
    }


# 生产环境：serve 前端 dist
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.main:app", host=settings.host, port=settings.port, reload=True)
