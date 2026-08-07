"""视频分析链 — 多智能体分析管道

架构：
  1. 文本预处理
  2. 顺序 Chain：总结 / 视频要点 / 字幕段落化
  3. 可选的翻译 Chain
  4. 结果聚合

返回 {summary, highlights, paragraphs, translation}
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from .summary import run_summary_chain
from .highlights import run_highlights_chain
from .paragraph import run_paragraph_chain
from .translate import run_translate_chain

logger = logging.getLogger(__name__)

_MAX_LENGTH = 8000


def _truncate(plain_text: str) -> str:
    if len(plain_text) <= _MAX_LENGTH:
        return plain_text
    return (
        plain_text[:_MAX_LENGTH * 3 // 5]
        + "\n...(中间内容省略)...\n"
        + plain_text[-_MAX_LENGTH * 2 // 5:]
    )


def analyze_video(
    transcript: str,
    language: str,
    plain_text: str,
    duration: float = 0,
) -> Dict[str, Any]:
    """多智能体分析管道"""
    logger.info(f"开始多智能体分析（语言: {language}，时长: {duration:.0f}秒）")

    transcript_for_analysis = _truncate(plain_text)
    results: Dict[str, Any] = {}

    # --- 1. 视频总结 ---
    try:
        logger.info("Chain 1/4: 生成视频总结...")
        results["summary"] = run_summary_chain(transcript_for_analysis, language, duration)
        logger.info("视频总结完成")
    except Exception as e:
        logger.error(f"视频总结失败: {e}")
        results["summary"] = f"总结生成失败: {str(e)}"

    # --- 2. 视频要点（传入带时间戳的完整 transcript，确保 LLM 看到真实时间点）---
    try:
        logger.info("Chain 2/4: 生成视频要点...")
        # 对要点提取，使用带时间戳的 transcript 而非 plain_text
        transcript_for_highlights = transcript
        if len(transcript_for_highlights) > _MAX_LENGTH:
            transcript_for_highlights = (
                transcript_for_highlights[:_MAX_LENGTH * 3 // 5]
                + "\n...(中间内容省略)...\n"
                + transcript_for_highlights[-_MAX_LENGTH * 2 // 5:]
            )
        results["highlights"] = run_highlights_chain(transcript_for_highlights)
        logger.info("视频要点完成")
    except Exception as e:
        logger.error(f"视频要点失败: {e}")
        results["highlights"] = f"视频要点生成失败: {str(e)}"

    # --- 3. 字幕段落化 ---
    try:
        logger.info("Chain 3/4: 生成字幕段落...")
        results["paragraphs"] = run_paragraph_chain(transcript_for_analysis)
        logger.info("字幕段落完成")
    except Exception as e:
        logger.error(f"字幕段落失败: {e}")
        results["paragraphs"] = f"字幕段落生成失败: {str(e)}"

    # --- 4. 翻译 ---
    if language != "zh":
        try:
            logger.info(f"Chain 4/4: 翻译 {language} → 中文...")
            translate_input = transcript_for_analysis[:4000]
            results["translation"] = run_translate_chain(translate_input)
            logger.info("翻译完成")
        except Exception as e:
            logger.error(f"翻译失败: {e}")
            results["translation"] = f"翻译失败: {str(e)}"
    else:
        results["translation"] = None

    return results
