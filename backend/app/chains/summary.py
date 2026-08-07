"""Chain 1: 视频内容总结智能体"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ..services.llm_service import create_llm

SUMMARY_SYSTEM = """你是一个专业的视频内容分析师。你的任务是根据视频转录文本生成全面的视频内容总结。

请按照以下结构输出总结：

## 视频主题
用一句话概括视频的核心主题

## 内容概述
3-5句话全面概括视频的主要内容

## 关键要点
- 列出3-7个最重要的关键信息点
- 每个要点简洁明了

## 详细内容
分段详细描述视频中讲述的内容，确保不遗漏重要信息

## 总结
视频的最终结论或核心启示

注意事项：
- 转录文本中的时间戳（如 [00:30]）仅作为参考，请严格基于转录文本的长度来估算内容的时间范围，不要编造超出转录文本范围的时间戳。
- 如果转录文本总时长约N分钟，所有引用的时间点都必须在 00:00 到 N 分钟以内。
- 保持客观准确，不要添加推测内容。
- 语言：如果原视频是中文，则必须使用简体中文输出，严禁使用繁体中文；其他语言则同时保留英文原文并用简体中文总结"""

SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SUMMARY_SYSTEM),
    ("human", "请分析以下视频转录内容。注意：转录文本的总时长约为{total_duration}分钟，所有时间引用请不要超过这个范围。\n\n视频语言：{language}\n\n转录内容：\n{transcript}"),
])


def run_summary_chain(transcript: str, language: str, total_duration: float = 0) -> str:
    """运行视频总结 chain"""
    duration_mins = round(total_duration / 60, 1) if total_duration > 0 else "未知"
    llm = create_llm(temperature=0.3, max_tokens=4096)
    chain = SUMMARY_PROMPT | llm | StrOutputParser()
    return chain.invoke({
        "transcript": transcript,
        "language": language,
        "total_duration": f"{duration_mins}分钟",
    })
