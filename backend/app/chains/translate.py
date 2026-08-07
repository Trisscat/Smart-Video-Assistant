"""Chain 4: 翻译智能体"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ..services.llm_service import create_llm

TRANSLATE_SYSTEM = """你是一个专业翻译助手。将非中文内容翻译为简体中文，同时保留英文原文。

输出格式：
### 英文原文
[保留的英文原文]

### 简体中文翻译
[准确流畅的简体中文翻译 — 严禁使用繁体中文]

翻译要求：
- 翻译准确、流畅、自然，必须使用简体中文
- 保留专业术语的准确性
- 如有时间戳保留不变"""

TRANSLATE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", TRANSLATE_SYSTEM),
    ("human", "请翻译以下内容：\n\n{text}"),
])


def run_translate_chain(text: str) -> str:
    """运行翻译 chain"""
    llm = create_llm(temperature=0.3, max_tokens=4096)
    chain = TRANSLATE_PROMPT | llm | StrOutputParser()
    return chain.invoke({"text": text})
