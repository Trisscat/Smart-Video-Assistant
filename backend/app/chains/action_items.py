"""Chain 3: 行动项提取智能体"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ..services.llm_service import create_llm

ACTION_SYSTEM = """你是一个专业的行动项提取助手。从视频内容中识别所有行动项、待办事项和任务分配。

请按以下格式输出：

## 行动项清单

| 序号 | 行动项 | 负责人 | 截止时间 | 优先级 | 相关时间点 |
|------|--------|--------|----------|--------|------------|
| 1 | 具体行动描述 | 负责人（如有） | 截止时间（如有） | 高/中/低 | 视频时间戳 |

## 未明确分配的行动项
如果有任务被提及但未指定负责人，在此列出

## 紧急事项
需要优先处理的紧急行动项

注意事项：
- 如果没有明确的行动项，请说明"本视频/会议未涉及明确的行动项"
- 优先级判断标准：高=紧急且重要，中=重要但不紧急，低=一般事项
- 尽量保留视频时间戳以追溯来源"""

ACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", ACTION_SYSTEM),
    ("human", "请从以下内容中提取行动项：\n\n转录内容：\n{transcript}"),
])


def run_action_items_chain(transcript: str) -> str:
    """运行行动项提取 chain"""
    llm = create_llm(temperature=0.3, max_tokens=4096)
    chain = ACTION_PROMPT | llm | StrOutputParser()
    return chain.invoke({"transcript": transcript})
