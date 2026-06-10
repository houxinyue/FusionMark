# FusionMark - PDF 智能解析与高亮系统

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/FastAPI-0.131.0-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</p>

<p align="center">
  <b>智能文档解析 · 实体自动提取 · 可视化高亮渲染</b>
</p>

---

## 📖 项目简介

**FusionMark** 是一个基于 **MinerU** 和 **LangExtract** 技术的 PDF 智能解析与高亮系统。它能够自动从 PDF 文档中提取结构化信息，并将关键内容以彩色高亮的形式标注在原文档上，生成可视化分析报告。

### 核心能力

| 能力 | 描述 |
|------|------|
| 🎯 **多模态文档解析** | 支持 PDF、Word、PPT、图片、HTML 等多种格式 |
| 🤖 **智能实体提取** | 基于 LLM 自动识别文档中的关键信息 |
| 🎨 **可视化高亮** | 将提取结果以彩色边框形式标注在原 PDF 上 |
| ⚡ **异步任务处理** | 支持 WebSocket 实时进度推送 |
| 📝 **配置文件驱动** | YAML 配置文件支持，灵活适配不同场景 |
| 🧠 **配置智能助手** | 独立 `agent-copilot` 模块，面向 Profile YAML 生成、校验、归档 |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        FusionMark 系统架构                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────┐   │
│  │   前端界面   │────▶│  FastAPI    │────▶│  任务管理器      │   │
│  │  (Web UI)   │◀────│   服务端    │◀────│  (TaskManager)  │   │
│  └─────────────┘     └──────┬──────┘     └────────┬────────┘   │
│                             │                      │            │
│                      ┌──────┴──────┐              │            │
│                      │  WebSocket  │◀─────────────┘            │
│                      │  实时进度   │                            │
│                      └─────────────┘                            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   核心处理管道 (Pipeline)                 │   │
│  │                                                          │   │
│  │   PDF/文档  ──▶  MinerU API  ──▶  Markdown              │   │
│  │                                              │          │   │
│  │                                              ▼          │   │
│  │   高亮 PDF  ◀──  WeasyPrint  ◀──  LangExtract提取      │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   存储层 (Storage Provider)               │   │
│  │                                                          │   │
│  │   ┌──────────────┐         ┌──────────────┐             │   │
│  │   │ LocalProvider│         │MinioProvider │             │   │
│  │   │  (本地文件)   │         │  (对象存储)   │             │   │
│  │   └──────────────┘         └──────────────┘             │   │
│  │                                                          │   │
│  │   • Workspace 临时工作区    • 产物持久化                   │   │
│  │   • 任务完成后自动清理      • Artifacts API               │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   配置管理 (Profiles)                     │   │
│  │                                                          │   │
│  │   • YAML 配置文件   • 提取提示词模板   • 类别颜色映射      │   │
│  │   • Few-shot 示例   • 模型参数配置                        │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 数据流转

```
PDF URL → MinerU API → full.md (Markdown 文本)
                                │
                                ▼
                        LangExtract 实体提取
                                │
                                ▼
                        Markdown + 高亮标签
                        (HTML <mark> + CSS)
                                │
                                ▼
                        WeasyPrint 渲染
                                │
                                ▼
                        高亮 PDF 输出
                                │
                                ▼
              ┌─────────────────────────────────┐
              │  Workspace: workspaces/{task_id}/│
              │   • mineru/ (zip + extracted)    │
              │   • highlight/ (PDF + debug)     │
              └─────────────────────────────────┘
                                │
                                ▼
              ┌─────────────────────────────────┐
              │  Storage Provider 持久化         │
              │   • tasks/{task_id}/mineru/      │
              │   • tasks/{task_id}/langextract/ │
              │   • tasks/{task_id}/highlight/   │
              └─────────────────────────────────┘
                                │
                                ▼
                        自动清理 Workspace
```

### 存储架构

FusionMark 采用 **Storage Provider 插件架构**，支持两种存储后端，通过环境变量切换：

| Provider | 适用场景 | 数据位置 |
|---|---|---|
| `local` | 本地开发 | `storage/` 目录（可配置） |
| `minio` | 生产/多实例 | MinIO 对象存储桶 |

**Workspace 机制**：
- 任务运行时，MinerU 和 Highlight 产物先写入临时工作区 `workspaces/{task_id}/`
- 任务完成后，产物自动上传至 Storage Provider，然后清理本地工作区
- 下载接口优先检查本地文件，缺失时自动回退到 Storage Provider 读取

**Artifacts API**：
- `GET /api/v1/tasks/{task_id}/artifacts/langextract_html` — 获取 LangExtract HTML 可视化
- `GET /api/v1/tasks/{task_id}/artifacts/entities` — 获取结构化提取结果（JSONL）
- `GET /api/v1/tasks/{task_id}/artifacts/highlight_pdf` — 获取高亮 PDF

> Redis 中不再存储完整的 `langextract_html` 和 `entities`，前端通过 Artifacts API 按需拉取，显著减轻 Redis payload。

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Redis (用于任务状态缓存)

### 1. 克隆仓库

```bash
git clone <repository-url>
cd fusion-mark
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
输出依赖核心 pip-chill > requirements.txt
```

### 3. 配置环境变量

在 `services/` 目录创建 `.env` 文件：

```bash
cd services
# 编辑 .env 文件
```

```env
# MinerU API 配置 (必需)
MINERU_API_KEY=your_mineru_api_key
MINERU_CLIENT_MODE=open_sdk
MINERU_SDK_BASE_URL=https://mineru.net/api/v4
MINERU_SDK_TOKEN_ENV=MINERU_API_KEY

# DeepSeek API 配置 (用于 LangExtract)
DS_API_KEY=your_deepseek_api_key
DS_API_BASE_URL=https://api.deepseek.com

# Redis 配置（用于任务状态缓存）
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

### 4. 启动服务

进入 `services/` 目录启动后端服务：

```bash
cd services

# 方式 1: 使用启动脚本
python start.py api

# 方式 2: 直接使用 uvicorn
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

> 详细说明参见 [services/README.md](services/README.md)

### 5. 访问服务

- API 文档: http://localhost:8000/docs
- 前端界面: http://localhost:8000 (如已构建)
- 健康检查: http://localhost:8000/health

---

## 📚 API 接口

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

### 上传文件提交任务

```bash
POST /api/v1/tasks/upload
Content-Type: multipart/form-data

file=@report.pdf
model=vlm
language=ch
```

上传文件会通过 Storage Provider 保存到 `tasks/{task_id}/input/`，后台任务再以 `storage://...` 输入进入 MinerU `open_sdk` 解析流程。

### 查询任务状态

```bash
GET /api/v1/tasks/{task_id}
```

### 列出任务历史

```bash
GET /api/v1/tasks?limit=20&offset=0
```

返回最近任务列表，支持分页。

### 删除任务

```bash
DELETE /api/v1/tasks/{task_id}
```

删除任务记录及其 Storage Provider 中的产物。

### WebSocket 实时进度

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{task_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('进度更新:', data);
};
```

### 下载结果

```bash
GET /api/v1/tasks/{task_id}/download
```

### 获取任务产物 (Artifacts)

```bash
# LangExtract HTML 可视化
GET /api/v1/tasks/{task_id}/artifacts/langextract_html

# 结构化提取结果 (JSONL)
GET /api/v1/tasks/{task_id}/artifacts/entities

# 高亮 PDF
GET /api/v1/tasks/{task_id}/artifacts/highlight_pdf
```

详细 API 文档请参见 [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)

---

## ⚙️ 配置文件

### 配置文件示例

```yaml
# 配置档案描述
description: "智能手机市场报告专用配置"

# === MinerU 配置 ===
mineru_model: "vlm"           # 模型: pipeline/vlm/MinerU-HTML
mineru_enable_ocr: true
mineru_enable_formula: true
mineru_enable_table: true
mineru_language: "ch"

# === 高亮渲染配置 ===
highlight_config:
  # 提取提示词模板
  extraction_prompt: |
    从文档中提取以下信息：
    1. company_name: 公司名称
    2. numeric_value: 数值数据
    3. date: 日期信息
  
  # 高亮类别与颜色配置
  category_colors:
    - name: "company_name"
      color: "#2ecc71"
      description: "公司名称"
    
    - name: "numeric_value"
      color: "#3498db"
      description: "数值数据"
  
  # Few-shot 示例
  examples:
    - text: "苹果出货量 240.6 百万部"
      extractions:
        - class: "company_name"
          text: "苹果"
        - class: "numeric_value"
          text: "240.6"

# === 输出配置 ===
final_output_dir: "highlight_output"
```

### 配置管理 API

```bash
# 列出所有配置
GET /api/v1/profiles

# 上传新配置
POST /api/v1/profiles/upload

# 激活配置
POST /api/v1/profiles/{profile_name}/activate

# 获取当前配置
GET /api/v1/profiles/current
```

---

## 🖥️ 前端界面

FusionMark 提供精美的 Web 界面，采用**品牌橙 + 墨水灰蓝**的浅色文档工作台风格配色，以白色为底、橙色为强调色，营造专业、清晰的阅读与操作体验。

### 界面特性

- 📤 **拖拽上传** - 支持拖放 PDF 文件
- 🔗 **URL 输入** - 直接输入文档链接
- 📊 **实时进度** - WebSocket 推送处理进度
- 🎨 **PDF 预览** - 内置 PDF.js 预览器
- 📥 **结果下载** - 一键下载高亮 PDF
- 📜 **任务历史** - 查看 Redis 中所有历史任务，支持分页、状态筛选、查看详情、删除

### 启动前端

本项目提供两套前端：

- **`web-pc/`** — 生产级 Vue 3 工程（推荐用于开发和新功能迭代）
- **`frontend/`** — 原生 HTML/CSS/JS 早期原型（保留参考）

#### 启动新版前端（web-pc）

```bash
cd web-pc
pnpm install
pnpm dev
```

前端将运行在 `http://localhost:5173`，Vite 会自动代理 API 请求到 `http://localhost:8000`。

#### 构建生产包

```bash
cd web-pc
pnpm build
```

构建产物输出到 `web-pc/dist/`，可通过 Nginx 或 FastAPI 静态文件服务部署。

详细说明参见 [web-pc/README.md](web-pc/README.md)

---

## 🧩 核心模块

### 项目结构

```
fusion-mark/
├── services/              # 后端服务代码 (独立 Python 项目)
│   ├── api/              # API 层 (FastAPI)
│   ├── core/             # 核心业务逻辑
│   ├── clients/          # 第三方客户端
│   ├── pipelines/        # 处理管道
│   ├── utils/            # 工具模块
│   ├── legacy/           # 待废弃代码
│   ├── profiles/         # 配置文件
│   ├── examples/         # 示例代码
│   ├── mineru_output/    # MinerU 输出目录
│   ├── highlight_output/ # 高亮输出目录
│   ├── start.py          # 服务启动脚本
│   ├── requirements.txt  # Python 依赖
│   ├── .env              # 环境变量配置
│   └── README.md         # 服务层说明
├── web-pc/               # 新版前端 (Vue 3 + Vite + TS)
├── frontend/             # 旧版前端 (原生 HTML/CSS/JS)
├── agent-copilot/        # 配置智能助手独立应用
└── docs/                 # 文档
```

> **注意**: `services/` 是一个**独立的 Python 项目**，可以单独复制出来运行。详见 **[services/README.md](services/README.md)**

### 模块说明

| 文件 | 功能描述 |
|------|----------|
| `services/api/server.py` | FastAPI Web 服务，提供 RESTful API 和 WebSocket |
| `services/core/full_pipeline.py` | 完整流程服务，整合 MinerU + LangExtract + 渲染 |
| `services/clients/mineru.py` | MinerU API 客户端，文档解析与结果获取 |
| `services/core/highlight.py` | Markdown 高亮服务，LangExtract 集成与配置管理 |
| `services/utils/renderer.py` | Markdown 渲染器，将高亮结果转为 PDF |
| `services/legacy/celery_tasks.py` | ~~Celery 异步任务定义 (已废弃)~~ |
| `services/legacy/celery_config.py` | ~~Celery 配置 (已废弃)~~ |

### 配置智能助手（agent-copilot）

`agent-copilot/` 是面向 FusionMark Profile YAML 的独立智能助手应用，目标是通过多轮对话帮助用户生成、修改、校验和确认配置草稿。它与主解析服务解耦，可以单独启动、单独测试、单独部署。

当前已完成：

- 独立 FastAPI 应用骨架和启动入口。
- 会话、消息、checkpoint 领域模型。
- 内存存储、Redis 会话/checkpoint 适配器、MinIO 会话归档适配器。
- 统一持久化边界 `CopilotPersistenceBoundary`。
- Copilot 会话 schema `1.1`，支持草稿、校验结果、待确认动作和 agent trace。
- Redis key 保持 `agent-copilot:session:{session_id}` 和 `agent-copilot:session:{session_id}:checkpoints`。
- MinIO 归档路径保持 `{prefix}/{project}/{env}/agent/{user_id}/session/{session_id}.json`。

后续计划：

- Conversation Orchestrator 状态机。
- Intent Gatekeeper、Context Retriever、Draft Generator、Config Validator 等智能节点。
- HTTP API 与前端 Copilot 面板集成。
- 提示词资产和 Profile 上下文提供器。

详细说明参见 [agent-copilot/README.md](agent-copilot/README.md) 和 [Copilot 对话智能架构设计](docs/智能体架构设计/Copilot对话智能架构设计.md)。

### 渲染流程

#### Markdown → 高亮 PDF

```
┌─────────────────────────────────────────────────────┐
│  Step 1: LangExtract 实体提取                         │
│  ───────────────────────                             │
│  • 使用配置中的 extraction_prompt 和 few-shot 示例    │
│  • 调用 LLM 提取结构化实体                            │
│  • 输出: List[Extraction(class, text)]               │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  Step 2: HTML 高亮标记                                │
│  ─────────────────                                   │
│  • Markdown → HTML (使用 markdown 库)                │
│  • 在文本节点中查找实体                               │
│  • 添加 <mark class="highlight-{category}"> 标签     │
│  • 处理重叠匹配（优先保留长匹配）                      │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  Step 3: WeasyPrint 渲染                              │
│  ─────────────────                                   │
│  • HTML + CSS → PDF                                  │
│  • 使用 @page 规则设置页眉页脚                        │
│  • 支持中文（Microsoft YaHei/SimSun）                │
│  • 输出最终高亮 PDF                                  │
└─────────────────────────────────────────────────────┘
```

#### 核心渲染代码

```python
# 1. Markdown → HTML
html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

# 2. 使用 BeautifulSoup 添加高亮标签
soup = BeautifulSoup(html_content, 'html.parser')
for entity in entities:
    # 查找文本节点并添加 <mark> 标签
    mark_tag = soup.new_tag("mark", attrs={"class": f"highlight-{entity.category}"})
    mark_tag.string = entity.text

# 3. WeasyPrint 渲染 PDF
HTML(string=full_html).write_pdf(output_path, stylesheets=[CSS(string=css_style)])
```

---

## 🙏 致谢

本项目基于以下优秀开源项目构建：

### [MinerU](https://github.com/opendatalab/MinerU)

> 由 OpenDataLab 开发的多模态文档解析工具，提供高精度的 PDF 解析能力，支持公式、表格、图片等复杂元素的识别。

- **用途**: PDF 文档解析，提取 Markdown 文本和位置信息
- **版本**: API v4
- **模型**: 支持 pipeline、vlm、MinerU-HTML 等多种模型

### [LangExtract](https://github.com/iaizzi/langextract)

> 基于 LLM 的文本信息提取库，支持灵活的实体定义和 Few-shot 学习。

- **用途**: 从 Markdown 文本中提取结构化实体
- **版本**: 1.1.1
- **特性**: 支持自定义提示词、Few-shot 示例、多类别提取

### 其他依赖

| 项目 | 用途 |
|------|------|
| [FastAPI](https://fastapi.tiangolo.com/) | Web 框架 |
| [WeasyPrint](https://weasyprint.org/) | HTML/CSS → PDF 渲染 |
| [Redis](https://redis.io/) | 任务状态缓存 |

---

## 📂 项目结构

```
fusion-mark/
├── 📁 web-pc/                # ⭐ 新版前端 (Vue 3 + Vite + TypeScript)
│   ├── src/
│   │   ├── api/             # Axios 接口层
│   │   ├── components/      # Vue 业务组件
│   │   ├── composables/     # 组合式逻辑
│   │   ├── router/          # Vue Router
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── styles/          # 全局样式
│   │   ├── types/           # TypeScript 类型
│   │   ├── views/           # 页面级组件
│   │   ├── App.vue          # 根组件
│   │   └── main.ts          # 应用入口
│   ├── index.html           # HTML 模板
│   ├── vite.config.ts       # Vite 配置
│   ├── package.json         # 依赖
│   └── README.md            # 前端工程说明
│
├── 📁 frontend/              # 旧版前端 (原生 HTML/CSS/JS，保留参考)
│   ├── index.html
│   └── src/
│       ├── app.js
│       └── styles/
│
├── 📁 services/              # ⭐ 后端服务代码 (独立 Python 项目)
│   ├── api/                  # API 层 (FastAPI)
│   ├── core/                 # 核心业务逻辑
│   ├── clients/              # 第三方客户端
│   ├── pipelines/            # 处理管道
│   ├── utils/                # 工具模块
│   ├── legacy/               # 待废弃代码
│   ├── profiles/             # 配置档案
│   ├── examples/             # 示例代码
│   ├── mineru_output/        # MinerU 解析输出
│   ├── highlight_output/     # 高亮 PDF 输出
│   ├── start.py              # 启动脚本
│   ├── requirements.txt      # Python 依赖
│   ├── .env                  # 环境变量配置
│   └── README.md             # 服务层说明
│
├── 📁 agent-copilot/         # ⭐ 配置智能助手独立应用
│   ├── app/
│   │   ├── api/              # Copilot HTTP API 预留
│   │   ├── core/             # 服务门面与编排边界
│   │   ├── agent/            # 意图、上下文、生成、校验节点预留
│   │   ├── storage/          # Redis / MinIO / 内存持久化边界
│   │   ├── models/           # 会话、消息、checkpoint 领域模型
│   │   ├── schemas/          # 请求响应 DTO
│   │   ├── config/           # 环境变量配置
│   │   └── prompts/          # 提示词资产目录
│   ├── tests/                # 模块级测试
│   ├── scripts/              # 独立启动脚本
│   └── README.md             # 智能助手说明
│
├── 📁 docs/                  # 文档
│   └── 智能体架构设计/        # agent-copilot 架构与存储设计
├── 📁 openspec/              # 规格驱动变更与归档规范
├── 📁 .beads/                # bd 任务追踪数据
├── 📄 LICENSE
├── 📄 .gitignore
└── 📄 README.md              # 本文件
```

---

## 🛠️ 开发指南

### 本地开发

```bash
# 1. 安装开发依赖
pip install -r services/requirements.txt

# 2. 启动 Redis (用于任务状态缓存)
redis-server

# 3. 启动 API 服务
cd services
python start.py api
```

### 运行示例

```bash
# 完整流程演示
cd services/examples
python full_pipeline_demo.py

# MinerU + LangExtract 融合演示
python mineru_langextract_fusion_demo.py

# 回到项目根目录
cd ../..

# API 测试（如有测试目录）
python -m pytest tests/ -v
```

---

## 📋 任务追踪

本项目使用 **bd (beads)** 进行任务追踪。

```bash
# 查看待办任务
bd ready

# 查看所有任务
bd list

# 创建新任务
bd create "任务标题" -t feature -p 1

# 更新任务状态
bd update <task-id> --status in_progress
```

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 [MIT](LICENSE) 许可证开源。

---

## 📞 联系方式

如有问题或建议，欢迎通过以下方式联系：

- 📧 Email: houxinyue18@outlook.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/fusion-mark/issues)

---

<p align="center">
  <b>FusionMark</b> © 2026 | Powered by MinerU + LangExtract
</p>
