"""Chain 2: 会议纪要智能体"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ..services.llm_service import create_llm

MEETING_SYSTEM = """你是一个专业的会议记录员。如果确认视频内容是会议，请生成标准化的会议纪要；如果不是会议，请说明\"本视频非会议内容，无需生成会议纪要\"。

## 如果确认为会议，请按以下格式输出：

### 会议信息
- 会议主题：
- 与会人员（从内容中推断）：
- 会议时间（从内容中推断）：

### 议题讨论
按议题逐一记录讨论要点，标注时间范围

### 决策事项
列出会议中确定的所有决策

### 待解决问题
列出尚未解决、需要后续讨论的问题

### 下次会议
如果有提及下次会议安排，请记录

注意：转录文本中的时间戳如[00:30]是视频时间点，请在纪要中保留"""

MEETING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", MEETING_SYSTEM),
    ("human", "请分析以下内容是否属于会议，如果是则生成会议纪要：\n\n转录内容：\n{transcript}"),
])


def run_meeting_chain(transcript: str) -> str:
    """运行会议纪要 chain"""
    llm = create_llm(temperature=0.3, max_tokens=4096)
    chain = MEETING_PROMPT | llm | StrOutputParser()
    return chain.invoke({"transcript": transcript})
