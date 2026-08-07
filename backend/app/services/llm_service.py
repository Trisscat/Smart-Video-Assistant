"""LLM 服务 — 统一 LLM 创建入口，支持 OpenAI 兼容协议

Model selection strategy:
  - 通过 LLM_MODEL_ID 或 DEEPSEEK_MODEL 环境变量指定模型
  - 默认使用 deepseek-chat
  - 兼容 DeepSeek / OpenAI / 智谱 等所有 OpenAI 兼容厂商
"""

from __future__ import annotations

import os
import httpx
from langchain_openai import ChatOpenAI

from ..config import get_settings


_DEFAULT_MODEL = "deepseek-chat"


def create_llm(
    temperature: float | None = None,
    max_tokens: int | None = None,
    streaming: bool = False,
) -> ChatOpenAI:
    """创建 ChatOpenAI 实例

    自动从 Settings 读取 api_key / base_url / model，
    支持 DeepSeek、OpenAI、智谱等所有 OpenAI 兼容厂商。
    """
    s = get_settings()

    explicit_model = (
        os.getenv("LLM_MODEL_ID", "")
        or os.getenv("DEEPSEEK_MODEL", "")
    )
    model = explicit_model if explicit_model else _DEFAULT_MODEL

    http_client = httpx.AsyncClient(trust_env=False, timeout=httpx.Timeout(s.llm_timeout))

    return ChatOpenAI(
        model=model,
        api_key=s.llm_api_key_effective,
        base_url=s.llm_base_url_effective,
        temperature=temperature if temperature is not None else s.llm_temperature,
        max_tokens=max_tokens if max_tokens is not None else s.llm_max_tokens,
        http_async_client=http_client,
        streaming=streaming,
    )
