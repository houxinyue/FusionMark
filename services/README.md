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
MINERU_CLIENT_MODE=open_sdk          # 仅支持 open_sdk（legacy_v4 已移除）
MINERU_SDK_BASE_URL=https://mineru.net/api/v4
MINERU_SDK_TOKEN_ENV=MINERU_API_KEY
MINERU_SDK_EXTRA_FORMATS=html,docx   # 可选
MINERU_ENABLE_STORAGE_INPUT=true
MINERU_ENABLE_LOCAL_INPUT=true

# DeepSeek API 配置 (用于 LangExtract)
DS_API_KEY=your_deepseek_api_key
DS_API_BASE_URL=https://api.deepseek.com

# Redis 配置 (可选)
REDIS_URL=redis://localhost:6379/0

# ===== Storage Provider 配置 =====
STORAGE_PROVIDER=local              # local 或 minio
LOCAL_STORAGE_ROOT=storage          # 本地存储根目录

# MinIO 配置（STORAGE_PROVIDER=minio 时生效）
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=fusion-mark
MINIO_SECURE=false
MINIO_PREFIX=fusion-mark

# Workspace 配置
WORKSPACE_ROOT=workspaces
CLEAN_WORKSPACE_AFTER_UPLOAD=true   # 上传后自动清理工作区

# 产物持久化开关
STORE_MINERU_EXTRACTED=true
STORE_LANGEXTRACT_ARTIFACTS=true
STORE_HIGHLIGHT_ARTIFACTS=true
```

### MinerU Provider 与输入源

后端通过 `MINERU_CLIENT_MODE` 选择 MinerU 连接层：

- `open_sdk`：使用官方 `mineru-open-sdk`，支持 HTTP(S) URL 与本地文件输入。

任务输入除原 `document_url` URL 外，还可解析：

- `storage://path/to/file.pdf`：从当前 Storage Provider 读取对象，写入 `workspaces/{task_id}/input/` 后交给 SDK。
- `file://...`、`local://...` 或已存在本地路径：校验文件存在后交给 SDK。



### 文件上传任务接口

`POST /api/v1/tasks/upload` 支持 `multipart/form-data` 文件上传。上传文件会先写入当前 Storage Provider（local 或 MinIO）：

```text
tasks/{task_id}/input/{safe_filename}
```

随后后台任务会使用：

```text
storage://tasks/{task_id}/input/{safe_filename}
```

进入现有文档输入解析逻辑。

PowerShell 示例：

```powershell
$form = @{
  file = Get-Item "E:\tmp\test.pdf"
  model = "vlm"
  language = "ch"
}
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/tasks/upload" -Method Post -Form $form
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
│   ├── server.py         # FastAPI 主服务入口
│   ├── task_processor.py # 异步任务处理
│   └── progress_store.py # Redis 进度存储
├── core/                 # 核心业务逻辑
│   ├── full_pipeline.py  # 完整流程服务
│   └── highlight.py      # MD 高亮服务
├── clients/              # 第三方客户端
│   └── mineru.py         # MinerU API 客户端
├── storage/              # 存储插件 (新增)
│   ├── base.py           # Storage Provider 抽象接口
│   ├── local.py          # 本地文件系统实现
│   ├── minio_provider.py # MinIO 对象存储实现
│   ├── factory.py        # Provider 工厂
│   └── workspace.py      # 工作区管理
├── utils/                # 工具模块
│   └── renderer.py       # Markdown 渲染器
├── legacy/               # 待废弃代码 (Celery)
├── profiles/             # 配置文件目录
├── workspaces/           # 临时工作区 (任务运行时产物，自动清理)
├── storage/              # 持久化存储 (Local Provider 根目录)
├── requirements.txt      # Python 依赖
├── .env                  # 环境变量配置
└── README.md             # 本文件
```

## 核心模块说明

| 模块 | 功能描述 |
|------|----------|
| `api/server.py` | FastAPI Web 服务，提供 RESTful API、WebSocket、Artifacts API |
| `api/task_processor.py` | 异步 PDF 处理任务，集成 Workspace + Storage 上传 + 清理 |
| `core/full_pipeline.py` | 完整流程服务，整合 MinerU + LangExtract + 渲染 |
| `core/highlight.py` | Markdown 高亮服务，LangExtract 集成与配置管理 |
| `clients/mineru.py` | MinerU API 客户端，文档解析与结果获取 |
| `storage/` | 存储插件架构：Provider 抽象、Local/MinIO 实现、工作区管理 |
| `utils/renderer.py` | Markdown 渲染器，将高亮结果转为 PDF |

## 数据流

```
PDF URL → MinerU API → Markdown → LangExtract → 高亮渲染 → PDF
                                                      │
                                                      ▼
                                        Workspace: workspaces/{task_id}/
                                        • mineru/      (MinerU 解压产物)
                                        • highlight/   (PDF + debug 产物)
                                                      │
                                                      ▼
                                        Storage Provider 持久化
                                        • tasks/{task_id}/mineru/extracted/...
                                        • tasks/{task_id}/langextract/...
                                        • tasks/{task_id}/highlight/...
                                                      │
                                                      ▼
                                              自动清理 Workspace
```

## 存储架构

### Storage Provider 插件

支持两种后端，通过 `STORAGE_PROVIDER` 环境变量切换：

- **LocalProvider** (`local`)：开发环境默认，产物存入本地 `storage/` 目录
- **MinioProvider** (`minio`)：生产环境，产物存入 MinIO 对象存储桶

### Workspace 机制

- 任务运行时，MinerU 和 Highlight 的中间产物写入 `workspaces/{task_id}/`
- 任务完成后，`_persist_task_artifacts()` 将产物上传至 Storage Provider
- 上传成功后，根据 `CLEAN_WORKSPACE_AFTER_UPLOAD` 自动清理本地工作区
- 下载接口优先检查本地文件，缺失时回退到 Storage Provider 读取

### Artifacts API

```bash
# LangExtract HTML 可视化
GET /api/v1/tasks/{task_id}/artifacts/langextract_html

# 结构化提取结果 (JSONL)
GET /api/v1/tasks/{task_id}/artifacts/entities

# 高亮 PDF
GET /api/v1/tasks/{task_id}/artifacts/highlight_pdf
```

> Redis result 中不再存储 `langextract_html` 和 `entities`，前端通过 Artifacts API 按需拉取。

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

### 查询任务状态

```bash
GET /api/v1/tasks/{task_id}
```

### 下载结果

```bash
GET /api/v1/tasks/{task_id}/download
```

> 下载接口优先使用本地文件，若本地文件不存在（如 Workspace 已清理），自动回退到 Storage Provider 读取。

## 依赖说明

主要依赖：
- **FastAPI** - Web 框架
- **Uvicorn** - ASGI 服务器
- **LangExtract** - 实体提取
- **WeasyPrint** - PDF 渲染
- **python-dotenv** - 环境变量管理

## 许可证

MIT
