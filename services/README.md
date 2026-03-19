# FusionMark Services

PDF 智能解析与高亮系统 - 后端服务

## 简介

这是一个独立的 Python 服务层，提供 PDF 文档的智能解析、实体提取和高亮渲染功能。

## 功能特性

- 📄 **多模态文档解析** - 支持 PDF、Word、PPT、图片、HTML 等格式
- 🤖 **智能实体提取** - 基于 LLM 自动识别文档中的关键信息
- 🎨 **可视化高亮** - 将提取结果以彩色形式标注并生成 PDF
- ⚡ **异步任务处理** - 支持 WebSocket 实时进度推送
- 📝 **配置驱动** - YAML 配置文件支持，灵活适配不同场景

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填写：

```env
# MinerU API 配置 (必需)
MINERU_API_KEY=your_mineru_api_key

# DeepSeek API 配置 (用于 LangExtract)
DS_API_KEY=your_deepseek_api_key
DS_API_BASE_URL=https://api.deepseek.com

# Redis 配置 (可选)
REDIS_URL=redis://localhost:6379/0
```

### 3. 启动服务

```bash
# 方式 1: 使用启动脚本
python start.py api

# 方式 2: 直接使用 uvicorn
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问服务

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 项目结构

```
services/
├── api/                  # API 层 (FastAPI)
│   └── server.py         # FastAPI 主服务入口
├── core/                 # 核心业务逻辑
│   ├── full_pipeline.py  # 完整流程服务
│   └── highlight.py      # MD 高亮服务
├── clients/              # 第三方客户端
│   └── mineru.py         # MinerU API 客户端
├── pipelines/            # 处理管道
│   └── highlight.py      # 高亮 Pipeline
├── utils/                # 工具模块
│   └── renderer.py       # Markdown 渲染器
├── legacy/               # 待废弃代码 (Celery)
├── profiles/             # 配置文件目录
├── mineru_output/        # MinerU 输出目录
├── highlight_output/     # 高亮输出目录
├── start.py              # 服务启动脚本
├── requirements.txt      # Python 依赖
├── .env                  # 环境变量配置
└── README.md             # 本文件
```

## 核心模块说明

| 模块 | 功能描述 |
|------|----------|
| `api/server.py` | FastAPI Web 服务，提供 RESTful API 和 WebSocket |
| `core/full_pipeline.py` | 完整流程服务，整合 MinerU + LangExtract + 渲染 |
| `core/highlight.py` | Markdown 高亮服务，LangExtract 集成与配置管理 |
| `clients/mineru.py` | MinerU API 客户端，文档解析与结果获取 |
| `utils/renderer.py` | Markdown 渲染器，将高亮结果转为 PDF |

## 数据流

```
PDF URL → MinerU API → Markdown → LangExtract → 高亮渲染 → PDF
```

## 配置文件

配置文件存放在 `profiles/` 目录，支持 YAML 格式：

```yaml
description: "智能手机市场报告专用配置"

mineru_model: "vlm"
mineru_enable_ocr: true
mineru_enable_formula: true
mineru_enable_table: true
mineru_language: "ch"

highlight_config:
  extraction_prompt: |
    从文档中提取以下信息...
  
  category_colors:
    - name: "company_name"
      color: "#2ecc71"
      description: "公司名称"
  
  examples:
    - text: "苹果出货量 240.6 百万部"
      extractions:
        - class: "company_name"
          text: "苹果"

final_output_dir: "highlight_output"
```

## API 接口

### 提交任务

```bash
POST /api/v1/tasks

{
  "document_url": "https://example.com/report.pdf",
  "output_filename": "result.pdf",
  "custom_title": "智能分析报告",
  "model": "vlm",
  "enable_ocr": true,
  "enable_formula": true,
  "enable_table": true,
  "language": "ch"
}
```

### WebSocket 实时进度

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{task_id}');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('进度更新:', data);
};
```

## 依赖说明

主要依赖：
- **FastAPI** - Web 框架
- **Uvicorn** - ASGI 服务器
- **LangExtract** - 实体提取
- **WeasyPrint** - PDF 渲染
- **python-dotenv** - 环境变量管理

## 许可证

MIT
