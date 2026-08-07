"""Chain: 视频要点提取 - 基于转录片段提取时间标注的一句话要点"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ..services.llm_service import create_llm

HIGHLIGHTS_SYSTEM = """你是一个专业的视频内容分析师。请根据转录文本提取关键要点。

## 要求

1. 将转录文本按内容分成若干个逻辑段落（通常 5-10 个段落）
2. 每个段落标注该段落**开头的时间戳**
3. 用一句话概括该段落的关键信息
4. 时间戳必须来自转录文本中真实存在的 `[MM:SS]` 标记，不要编造

按以下格式输出：

## 视频要点

| 时间 | 关键信息 |
|------|----------|
| [00:00] | 视频开场，介绍主题 |
| [02:15] | 第二个重要节点 |
| [05:30] | 第三个重要节点 |

注意：
- 时间戳必须从转录文本中选取真实存在的时间点
- 每个要点严格用一句话表达
- 总共提取 5-10 个关键要点
- 优先选择内容转折处的时间点
- 所有输出必须使用简体中文，严禁使用繁体中文"""

HIGHLIGHTS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", HIGHLIGHTS_SYSTEM),
    ("human", "请提取以下视频转录的要点（使用简体中文输出），注意时间戳必须来自文本中真实存在的标记：\n\n转录内容：\n{transcript}"),
])


def run_highlights_chain(transcript: str) -> str:
    """运行视频要点提取 chain — 传入带时间戳的完整转录文本"""
    llm = create_llm(temperature=0.3, max_tokens=4096)
    chain = HIGHLIGHTS_PROMPT | llm | StrOutputParser()
    return chain.invoke({"transcript": transcript})
