"""Chain: 字幕段落化 - 基于LLM分析给字幕文本划分段落"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ..services.llm_service import create_llm

PARAGRAPH_SYSTEM = """你是一个专业的文本结构化分析师。请将以下视频字幕文本按主题划分为有意义的段落。

## 要求

1. 分析字幕文本的内容，识别出不同的主题/话题切换点
2. 在每个话题切换处插入 `---` 分隔线
3. 为每个段落添加一个简短的标题（用 `### 标题` 格式）
4. 保持原始字幕文本不变，只添加标题和分隔线

## 输出格式

### 第一段标题
[该段的字幕文本内容...]

---

### 第二段标题
[该段的字幕文本内容...]

---

### 第三段标题
[该段的字幕文本内容...]

注意事项：
- 段落标题和所有输出都必须使用简体中文，严禁繁体中文
- 段落标题要简洁明了（5-10个字）
- 不要在段落之间添加额外评论
- 保持原始文本的时间戳和格式"""

PARAGRAPH_PROMPT = ChatPromptTemplate.from_messages([
    ("system", PARAGRAPH_SYSTEM),
    ("human", "请将以下字幕文本划分为段落：\n\n{subtitle_text}"),
])


def run_paragraph_chain(transcript_text: str) -> str:
    """运行字幕段落化 chain"""
    # 截断长文本
    MAX_INPUT = 6000
    if len(transcript_text) > MAX_INPUT:
        text = transcript_text[:MAX_INPUT * 3 // 5] + "\n...(中间内容省略)...\n" + transcript_text[-MAX_INPUT * 2 // 5:]
    else:
        text = transcript_text
    llm = create_llm(temperature=0.3, max_tokens=4096)
    chain = PARAGRAPH_PROMPT | llm | StrOutputParser()
    return chain.invoke({"subtitle_text": text})
