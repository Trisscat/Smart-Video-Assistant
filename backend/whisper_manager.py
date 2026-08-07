"""
Whisper模型管理 - 通过ModelScope国内镜像下载
"""
import os
import sys
import logging
from pathlib import Path
from config import WHISPER_MODEL_SIZE, WHISPER_MODEL_CACHE, MODELSCOPE_BASE_URL

logger = logging.getLogger(__name__)


def get_model_dir():
    """获取模型目录"""
    model_dir = Path(WHISPER_MODEL_CACHE)
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir


def download_model_from_modelscope():
    """
    从ModelScope国内镜像下载faster-whisper模型
    """
    model_dir = get_model_dir()
    model_name = f"faster-whisper-{WHISPER_MODEL_SIZE}"
    model_path = model_dir / model_name

    if model_path.exists() and any(model_path.iterdir()):
        logger.info(f"模型已存在: {model_path}")
        return str(model_path)

    logger.info(f"开始从ModelScope下载模型: {WHISPER_MODEL_SIZE}")

    try:
        from modelscope.hub.snapshot_download import snapshot_download

        repo_map = {
            "tiny": "keepitsimple/faster-whisper-tiny",
            "base": "keepitsimple/faster-whisper-base",
            "small": "keepitsimple/faster-whisper-small",
            "medium": "keepitsimple/faster-whisper-medium",
            "large-v3": "keepitsimple/faster-whisper-large-v3",
            "large-v2": "keepitsimple/faster-whisper-large-v2",
        }

        repo_id = repo_map.get(WHISPER_MODEL_SIZE, repo_map["medium"])
        logger.info(f"下载模型: {repo_id}")

        snapshot_download(
            repo_id,
            cache_dir=str(model_dir),
            local_dir=str(model_path),
        )
        logger.info(f"模型下载完成: {model_path}")
        return str(model_path)

    except ImportError:
        logger.warning("modelscope未安装，尝试使用huggingface镜像...")
        return download_from_hf_mirror(model_path)
    except Exception as e:
        logger.error(f"ModelScope下载失败: {e}")
        return download_from_hf_mirror(model_path)


def download_from_hf_mirror(model_path: Path):
    """从HuggingFace镜像下载模型"""
    try:
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

        from huggingface_hub import snapshot_download

        repo_id = f"Systran/faster-whisper-{WHISPER_MODEL_SIZE}"

        snapshot_download(
            repo_id,
            cache_dir=str(model_path.parent),
            local_dir=str(model_path),
            local_dir_use_symlinks=False,
        )
        logger.info(f"从HF镜像下载完成: {model_path}")
        return str(model_path)
    except Exception as e:
        logger.error(f"HF镜像下载也失败: {e}")
        logger.info("将使用在线模式，首次运行时会自动下载...")
        return None


def load_whisper_model():
    """
    加载Whisper模型
    优先使用本地缓存，否则自动下载
    """
    from faster_whisper import WhisperModel

    model_dir = get_model_dir()

    # 尝试查找已下载的模型
    local_models = list(model_dir.glob("faster-whisper-*"))
    if local_models:
        model_path = str(local_models[0])
        logger.info(f"使用本地模型: {model_path}")
    else:
        model_path = None

    if model_path and Path(model_path).exists():
        try:
            model = WhisperModel(
                model_path,
                device="auto",
                compute_type="int8",
            )
            logger.info("Whisper模型加载成功")
            return model
        except Exception as e:
            logger.warning(f"本地模型加载失败: {e}")

    # 尝试在线加载（会自动下载）
    logger.info(f"尝试在线加载模型: {WHISPER_MODEL_SIZE}")
    try:
        # 设置环境变量使用hf镜像
        if "HF_ENDPOINT" not in os.environ:
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

        model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device="auto",
            compute_type="int8",
            download_root=str(model_dir),
        )
        logger.info("Whisper模型在线加载成功")
        return model
    except Exception as e:
        logger.error(f"模型加载完全失败: {e}")
        raise RuntimeError(f"无法加载Whisper模型: {e}")
