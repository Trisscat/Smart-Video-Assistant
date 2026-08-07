"""配置管理 — 从环境变量读取，基于 pydantic-settings（参考 HelloAgents 框架）"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 项目根目录：backend/app/config.py → parent → parent → parent = 项目根
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 显式加载项目根目录的 .env
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    """应用配置 — 单例模式"""

    # --- 应用 ---
    app_name: str = "智能视频助手"
    app_version: str = "2.0.0"
    debug: bool = False

    # --- 服务器 ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- CORS ---
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # --- LLM (OpenAI 兼容协议，支持 DeepSeek / OpenAI 等) ---
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""
    llm_temperature: float = 0.3
    llm_max_tokens: int = 4096
    llm_timeout: int = 60

    # --- Whisper ---
    whisper_model_size: str = "medium"
    whisper_model_cache: str = str(BASE_DIR / "models")

    # --- 存储 ---
    upload_dir: str = str(BASE_DIR / "uploads")
    result_dir: str = str(BASE_DIR / "results")
    history_file: str = str(BASE_DIR / "history.json")

    # --- 处理 ---
    max_concurrent_videos: int = 4
    max_upload_size_mb: int = 500
    video_segment_length: int = 30

    # --- 日志 ---
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    def get_cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def llm_api_key_effective(self) -> str:
        """从多个可能的环境变量中获取 API Key"""
        return (
            self.llm_api_key
            or os.getenv("LLM_API_KEY", "")
            or os.getenv("DEEPSEEK_API_KEY", "")
            or os.getenv("OPENAI_API_KEY", "")
        )

    @property
    def llm_base_url_effective(self) -> str:
        """自动补全 /v1 后缀"""
        url = (
            self.llm_base_url
            or os.getenv("LLM_BASE_URL", "")
            or os.getenv("DEEPSEEK_BASE_URL", "")
            or "https://api.deepseek.com/v1"
        )
        if not url.rstrip("/").endswith("/v1"):
            url = url.rstrip("/") + "/v1"
        return url

    @property
    def llm_model_effective(self) -> str:
        """从环境变量读取模型名"""
        return (
            os.getenv("LLM_MODEL_ID", "")
            or os.getenv("DEEPSEEK_MODEL", "")
            or self.llm_model
            or "deepseek-chat"
        )

    # --- 便捷路径属性 ---
    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)

    @property
    def result_path(self) -> Path:
        return Path(self.result_dir)

    @property
    def models_path(self) -> Path:
        return Path(self.whisper_model_cache)


# --- 全局单例 ---
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# --- 启动校验 ---
def validate_config() -> bool:
    s = get_settings()
    warnings: List[str] = []

    if not s.llm_api_key_effective:
        warnings.append("LLM_API_KEY / DEEPSEEK_API_KEY 未配置，LLM 功能将不可用")

    for w in warnings:
        print(f"  [WARN]  {w}")

    # 确保目录存在
    for d in [s.upload_path, s.result_path, s.models_path]:
        d.mkdir(parents=True, exist_ok=True)

    return True
