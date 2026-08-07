"""
Whisper模型管理 - 通过ModelScope国内镜像下载
"""
import os
import sys
import logging
from pathlib import Path
from ..config import get_settings

_settings = get_settings()
WHISPER_MODEL_SIZE = _settings.whisper_model_size
WHISPER_MODEL_CACHE = _settings.whisper_model_cache
MODELSCOPE_BASE_URL = "https://www.modelscope.cn"

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

    # 尝试查找已下载的模型 — 优先匹配 faster-whisper-{size} 目录
    local_models = list(model_dir.glob(f"faster-whisper-{WHISPER_MODEL_SIZE}"))
    if local_models:
        model_path = str(local_models[0])
        logger.info(f"使用本地模型: {model_path}")

        # 如果是 HF 快照目录（没有直接的 model.bin），尝试直接加载
        try:
            model = WhisperModel(
                model_path,
                device="auto",
                compute_type="int8",
            )
            logger.info("Whisper模型加载成功")
            return model
        except Exception as e:
            logger.warning(f"本地模型路径加载失败: {e}")
    else:
        logger.info(f"未找到本地模型目录 faster-whisper-{WHISPER_MODEL_SIZE}，尝试从 HF 缓存加载...")

    # 尝试用 HF cache 中的模型
    hf_cache_models = list(model_dir.glob(f"models--Systran--faster-whisper-{WHISPER_MODEL_SIZE}"))
    if hf_cache_models:
        snapshots_dir = hf_cache_models[0] / "snapshots"
        snapshots = list(snapshots_dir.iterdir()) if snapshots_dir.exists() else []
        if snapshots:
            # 直接复制到 faster-whisper-{size} 目录供后续使用
            import shutil
            target = model_dir / f"faster-whisper-{WHISPER_MODEL_SIZE}"
            if not target.exists():
                shutil.copytree(str(snapshots[0]), str(target))
                logger.info(f"模型已从 HF 缓存复制到: {target}")
            model_path = str(target)
            try:
                model = WhisperModel(model_path, device="auto", compute_type="int8")
                logger.info("Whisper模型加载成功")
                return model
            except Exception as e:
                logger.warning(f"从 HF 缓存加载失败: {e}")

    # 尝试在线加载（会自动下载）
    logger.info(f"尝试在线加载模型: {WHISPER_MODEL_SIZE}")
    try:
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
