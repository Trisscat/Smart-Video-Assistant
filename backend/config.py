"""
智能视频助手 - 配置文件
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "your-deepseek-api-key")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# 模型下载配置（使用国内镜像 - modelscope）
MODELSCOPE_BASE_URL = "https://www.modelscope.cn"
WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "medium")  # tiny/base/small/medium/large-v3
WHISPER_MODEL_CACHE = os.environ.get("WHISPER_MODEL_CACHE", str(BASE_DIR / "models"))

# 上传和结果存储
UPLOAD_DIR = BASE_DIR / "uploads"
RESULT_DIR = BASE_DIR / "results"
HISTORY_FILE = BASE_DIR / "history.json"
MAX_UPLOAD_SIZE_MB = 500  # 最大上传文件大小

# 处理配置
MAX_CONCURRENT_VIDEOS = os.environ.get("MAX_CONCURRENT_VIDEOS", 4)  # 最大并行处理数
VIDEO_SEGMENT_LENGTH = 30  # 每段音频长度（秒），用于分段转录获取时间戳

# 支持的语言
SUPPORTED_LANGUAGES = {
    "zh": "中文",
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
    "fr": "Français",
    "de": "Deutsch",
    "es": "Español",
    "ru": "Русский",
    "ar": "العربية",
    "pt": "Português",
    "it": "Italiano",
}

# 确保目录存在
for d in [UPLOAD_DIR, RESULT_DIR, Path(WHISPER_MODEL_CACHE)]:
    d.mkdir(parents=True, exist_ok=True)
