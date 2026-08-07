"""
LangChain 多智能体视频分析系统
包含三个专业智能体：
1. 视频总结智能体 - 全面概括视频内容
2. 会议纪要智能体 - 生成结构化会议纪要
3. 行动项提取智能体 - 识别并提取待办事项
"""
import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

logger = logging.getLogger(__name__)


class VideoAnalysisAgents:
    """多智能体视频分析系统"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=DEEPSEEK_MODEL,
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            temperature=0.3,
            max_tokens=4096,
        )

        # === 智能体1: 视频内容总结 ===
        self.summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的视频内容分析师。你的任务是根据视频转录文本生成全面的视频内容总结。

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

注意：
- 转录文本包含时间戳标记（如[00:30]），请在每个部分注明相关时间范围
- 保持客观准确，不要添加推测内容
- 语言：如果原视频是中文则用中文输出，其他语言则同时保留英文并用简体中文总结"""),
            ("human", """请分析以下视频转录内容：

视频语言：{language}

转录内容：
{transcript}"""),
        ])

        self.summary_chain = self.summary_prompt | self.llm | StrOutputParser()

        # === 智能体2: 会议纪要 ===
        self.meeting_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的会议记录员。如果确认视频内容是会议，请生成标准化的会议纪要；如果不是会议，请说明"本视频非会议内容，无需生成会议纪要"。

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

注意：转录文本中的时间戳如[00:30]是视频时间点，请在纪要中保留"""),
            ("human", """请分析以下内容是否属于会议，如果是则生成会议纪要：

转录内容：
{transcript}"""),
        ])

        self.meeting_chain = self.meeting_prompt | self.llm | StrOutputParser()

        # === 智能体3: 行动项提取 ===
        self.action_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的行动项提取助手。从视频内容中识别所有行动项、待办事项和任务分配。

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
- 尽量保留视频时间戳以追溯来源"""),
            ("human", """请从以下内容中提取行动项：

转录内容：
{transcript}"""),
        ])

        self.action_chain = self.action_prompt | self.llm | StrOutputParser()

        # === 翻译智能体 ===
        self.translate_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业翻译助手。将非中文内容翻译为简体中文，同时保留英文原文。

输出格式：
### 英文原文
[保留的英文原文]

### 简体中文翻译
[准确流畅的中文翻译]

翻译要求：
- 翻译准确、流畅、自然
- 保留专业术语的准确性
- 如有时间戳保留不变"""),
            ("human", """请翻译以下内容：

{text}"""),
        ])

        self.translate_chain = self.translate_prompt | self.llm | StrOutputParser()

    def analyze_video(
        self,
        transcript: str,
        language: str,
        plain_text: str,
    ) -> Dict[str, Any]:
        """
        多智能体并行分析视频

        Returns:
            包含 summary, meeting_notes, action_items 的分析结果
        """
        logger.info(f"开始多智能体分析视频（语言: {language}）")

        # 如果文本很长，截断处理（DeepSeek上下文限制）
        MAX_LENGTH = 8000
        if len(plain_text) > MAX_LENGTH:
            # 智能截断：保留开头和结尾，中间均匀采样
            transcript_for_analysis = (
                plain_text[:MAX_LENGTH * 3 // 5] +
                "\n...(中间内容省略)...\n" +
                plain_text[-MAX_LENGTH * 2 // 5:]
            )
        else:
            transcript_for_analysis = plain_text

        results = {}

        # === 1. 内容总结 ===
        try:
            logger.info("智能体1: 生成视频总结...")
            summary = self.summary_chain.invoke({
                "transcript": transcript_for_analysis,
                "language": language,
            })
            results["summary"] = summary
            logger.info("视频总结生成完成")
        except Exception as e:
            logger.error(f"视频总结生成失败: {e}")
            results["summary"] = f"总结生成失败: {str(e)}"

        # === 2. 会议纪要 ===
        try:
            logger.info("智能体2: 生成会议纪要...")
            meeting = self.meeting_chain.invoke({
                "transcript": transcript_for_analysis,
            })
            results["meeting_notes"] = meeting
            logger.info("会议纪要生成完成")
        except Exception as e:
            logger.error(f"会议纪要生成失败: {e}")
            results["meeting_notes"] = f"会议纪要生成失败: {str(e)}"

        # === 3. 行动项提取 ===
        try:
            logger.info("智能体3: 提取行动项...")
            actions = self.action_chain.invoke({
                "transcript": transcript_for_analysis,
            })
            results["action_items"] = actions
            logger.info("行动项提取完成")
        except Exception as e:
            logger.error(f"行动项提取失败: {e}")
            results["action_items"] = f"行动项提取失败: {str(e)}"

        # === 4. 如果需要翻译（非中文内容） ===
        if language != "zh":
            try:
                logger.info(f"翻译智能体: 翻译{language}内容为中文...")
                translate_input = transcript_for_analysis[:4000]
                translation = self.translate_chain.invoke({
                    "text": translate_input,
                })
                results["translation"] = translation
                logger.info("翻译完成")
            except Exception as e:
                logger.error(f"翻译失败: {e}")
                results["translation"] = f"翻译失败: {str(e)}"
        else:
            results["translation"] = None

        return results
