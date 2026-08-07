"""
视频音频提取工具 - 从视频文件中提取音频
"""
import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def extract_audio(video_path: str, output_dir: Optional[str] = None) -> str:
    """
    从视频文件中提取音频为WAV格式

    Args:
        video_path: 视频文件路径
        output_dir: 输出目录，默认为系统临时目录

    Returns:
        提取的音频文件路径
    """
    from moviepy.editor import VideoFileClip

    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"视频文件不存在: {video_path}")

    # 确定输出路径
    if output_dir:
        output = Path(output_dir) / f"{video_path.stem}_audio.wav"
    else:
        output = Path(tempfile.gettempdir()) / f"{video_path.stem}_audio.wav"

    logger.info(f"正在从视频提取音频: {video_path.name}")

    try:
        clip = VideoFileClip(str(video_path))
        if clip.audio is None:
            raise ValueError("视频没有音频轨道")

        # 提取音频
        clip.audio.write_audiofile(
            str(output),
            codec="pcm_s16le",
            fps=16000,  # 16kHz采样率，Whisper推荐
            nbytes=2,
            verbose=False,
            logger=None,
        )
        clip.close()

        # 获取音频时长
        from pydub import AudioSegment
        audio = AudioSegment.from_wav(str(output))
        duration_seconds = len(audio) / 1000.0

        logger.info(f"音频提取完成: {output.name}, 时长: {duration_seconds:.1f}秒")
        return str(output), duration_seconds

    except Exception as e:
        logger.error(f"音频提取失败: {e}")
        raise


def get_video_metadata(video_path: str) -> dict:
    """获取视频元数据"""
    from moviepy.editor import VideoFileClip

    try:
        clip = VideoFileClip(str(video_path))
        metadata = {
            "duration": clip.duration,
            "fps": clip.fps,
            "size": f"{clip.size[0]}x{clip.size[1]}",
            "has_audio": clip.audio is not None,
        }
        clip.close()
        return metadata
    except Exception as e:
        logger.warning(f"获取视频元数据失败: {e}")
        return {}
