# 智能视频助手 🎬

基于 **LangChain + Whisper + DeepSeek** 的智能视频分析系统。

## ✨ 功能特点

- 📤 **多视频并行上传** — 支持同时上传多个视频文件，多线程并行处理
- 🎯 **多智能体分析** — 三大专业智能体协同工作：
  - **视频总结智能体** — 全面概括视频内容，提取关键要点
  - **会议纪要智能体** — 自动识别会议内容，生成结构化纪要
  - **行动项提取智能体** — 识别待办事项，按优先级分类
- ⏱️ **精确时间戳** — 每条分析结果都标注视频时间点，可溯源
- 🌐 **多语言支持** — 自动检测视频语言，非中文内容自动翻译为简体中文
- 📋 **历史记录** — 保存所有分析记录，随时回顾
- 🎛️ **处理控制** — 支持处理过程中取消、删除视频
- 🖥️ **现代化UI** — Vue 3 构建的响应式前端界面

## 🏗️ 技术架构

```
smart-video-assistant/
├── backend/
│   ├── server.py           # FastAPI 后端服务
│   ├── config.py           # 配置文件
│   ├── orchestrator.py     # 视频处理编排器（多线程调度）
│   ├── whisper_manager.py  # Whisper模型管理（国内镜像下载）
│   ├── audio_utils.py      # 音频提取工具
│   ├── transcriber.py      # 语音识别（带时间戳）
│   ├── agents.py           # LangChain多智能体
│   └── requirements.txt    # Python依赖
├── frontend/
│   ├── src/
│   │   ├── App.vue         # 主布局
│   │   ├── views/
│   │   │   ├── UploadPage.vue   # 上传页面
│   │   │   ├── ResultPage.vue   # 结果展示页面
│   │   │   └── HistoryPage.vue  # 历史记录页面
│   │   ├── api/index.js    # API接口层
│   │   ├── router/index.js # 路由配置
│   │   └── assets/style.css # 全局样式
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── run.py                  # 一键启动入口
└── README.md
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+
- Node.js 18+
- FFmpeg（用于音频提取）

### 2. 配置 API Key

```bash
# Linux/Mac
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# Windows (PowerShell)
$env:DEEPSEEK_API_KEY="your-deepseek-api-key"

# Windows (CMD)
set DEEPSEEK_API_KEY=your-deepseek-api-key
```

你也可以直接在 `backend/config.py` 中修改 `DEEPSEEK_API_KEY`。

### 3. 启动后端

```bash
# 方式一：使用启动脚本（推荐）
python run.py

# 方式二：直接启动
cd backend
pip install -r requirements.txt
python server.py
```

首次运行会自动从 **ModelScope 国内镜像** 下载 Whisper 模型，后续运行使用本地缓存。

后端服务运行在: **http://localhost:8000**
API 文档: **http://localhost:8000/docs**

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在: **http://localhost:3000**

### 5. 使用流程

1. 打开浏览器访问 http://localhost:3000
2. 拖拽或选择视频文件上传（支持多选）
3. 实时查看处理进度（音频提取 → 语音识别 → 智能分析）
4. 分析完成后点击"查看结果"跳转到结果页面
5. 在结果页切换选项卡查看：转录文本、视频总结、会议纪要、行动项、翻译

## ⚙️ 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API密钥 | - |
| `DEEPSEEK_BASE_URL` | DeepSeek API地址 | `https://api.deepseek.com/v1` |
| `DEEPSEEK_MODEL` | 模型名称 | `deepseek-chat` |
| `WHISPER_MODEL_SIZE` | Whisper模型大小 | `medium` |
| `MAX_CONCURRENT_VIDEOS` | 最大并行处理数 | `4` |

## 📝 Whisper模型选择

| 模型 | 参数量 | 速度 | 准确度 | 适用场景 |
|------|--------|------|--------|----------|
| tiny | 39M | 极快 | 基础 | 测试/低资源 |
| base | 74M | 快 | 一般 | 简单场景 |
| small | 244M | 中等 | 较好 | 日常使用 |
| **medium** | 769M | 较慢 | 好 | **推荐** |
| large-v3 | 1.55B | 慢 | 最好 | 专业使用 |

## 🔧 故障排查

**模型下载失败**: 系统会自动降级到 HuggingFace 国内镜像下载，如仍失败，手动下载后放到 `backend/models/` 目录。

**音频提取失败**: 确保系统已安装 FFmpeg。Ubuntu: `apt install ffmpeg`，Mac: `brew install ffmpeg`，Windows: 下载 ffmpeg 并添加到 PATH。

**API调用失败**: 检查 DeepSeek API Key 是否正确设置，网络是否能访问 api.deepseek.com。
