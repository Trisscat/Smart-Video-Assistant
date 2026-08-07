"""
视频转录器 - 使用faster-whisper进行语音识别，带时间戳
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class VideoTranscriber:
    """视频转录器 - 带精确时间戳的分段转录"""

    def __init__(self, whisper_model):
        self.model = whisper_model
        self.segment_length = 30  # 每段30秒

    def transcribe(self, audio_path: str, duration: float = None) -> List[Dict[str, Any]]:
        """
        转录音频，返回带时间戳的片段列表

        Args:
            audio_path: 音频文件路径
            duration: 音频总时长（秒）

        Returns:
            转录片段列表，每个片段包含 start, end, text
        """
        logger.info(f"开始转录音频: {audio_path}")

        segments, info = self.model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True,  # 过滤静音
            vad_parameters=dict(
                min_silence_duration_ms=500,
            ),
            language=None,  # 自动检测语言
            task="transcribe",
        )

        detected_language = info.language
        language_probability = info.language_probability

        logger.info(
            f"检测到语言: {detected_language} "
            f"(置信度: {language_probability:.2f})"
        )

        result = []
        for segment in segments:
            result.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip(),
            })

        logger.info(f"转录完成，共 {len(result)} 个片段，"
                     f"总时长: {result[-1]['end']:.1f}s" if result else "转录完成")

        return result, detected_language

    def transcribe_for_analysis(self, audio_path: str) -> Dict[str, Any]:
        """
        转录音频并返回适用于分析的结构化数据
        """
        segments, language = self.transcribe(audio_path)

        # 组装完整文本（用于分析）
        full_text = ""
        for seg in segments:
            timestamp = self._format_timestamp(seg["start"])
            full_text += f"[{timestamp}] {seg['text']}\n"

        # 按自然段分组（无时间戳的纯文本）
        plain_text = " ".join(seg["text"] for seg in segments)

        return {
            "segments": segments,
            "full_text": full_text,
            "plain_text": plain_text,
            "language": language,
            "total_segments": len(segments),
        }

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """格式化时间戳为 HH:MM:SS"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
