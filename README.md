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
| ⚡ **异步任务处理** | 支持 WebSocket 实时进度推送和 Celery 任务队列 |
| 📝 **配置文件驱动** | YAML 配置文件支持，灵活适配不同场景 |

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
```

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Redis (可选，用于 Celery 任务队列)

### 1. 克隆仓库

```bash
git clone <repository-url>
cd fusion-mark
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
# MinerU API 配置 (必需)
MINERU_API_KEY=your_mineru_api_key

# DeepSeek API 配置 (用于 LangExtract)
DS_API_KEY=your_deepseek_api_key
DS_API_BASE_URL=https://api.deepseek.com

# Redis 配置 (可选，用于 Celery)
REDIS_URL=redis://localhost:6379/0
```

### 4. 启动服务

```bash
# 方式 1: 使用启动脚本
python start_server.py api

# 方式 2: 直接使用 uvicorn
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

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

### 查询任务状态

```bash
GET /api/v1/tasks/{task_id}
```

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

FusionMark 提供精美的 Web 界面，采用**克莱因蓝 + 爱马仕橙**的深色科技风配色。

### 界面特性

- 📤 **拖拽上传** - 支持拖放 PDF 文件
- 🔗 **URL 输入** - 直接输入文档链接
- 📊 **实时进度** - WebSocket 推送处理进度
- 🎨 **PDF 预览** - 内置 PDF.js 预览器
- 📥 **结果下载** - 一键下载高亮 PDF

### 启动前端

前端为纯静态页面，可直接在浏览器中打开 `frontend/index.html`，或通过 FastAPI 的静态文件服务访问。

---

## 🧩 核心模块

### 模块说明

| 文件 | 功能描述 |
|------|----------|
| `api_server.py` | FastAPI Web 服务，提供 RESTful API 和 WebSocket |
| `full_pipeline_service.py` | 完整流程服务，整合 MinerU + LangExtract + 渲染 |
| `mineru_client.py` | MinerU API 客户端，文档解析与结果获取 |
| `md_highlight_service.py` | Markdown 高亮服务，LangExtract 集成与配置管理 |
| `md_renderer.py` | Markdown 渲染器，将高亮结果转为 PDF |
| `celery_tasks.py` | Celery 异步任务定义 |
| `celery_config.py` | Celery 配置 |

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
| [Celery](https://docs.celeryq.dev/) | 异步任务队列 |
| [Redis](https://redis.io/) | 任务队列存储 |

---

## 📂 项目结构

```
fusion-mark/
├── 📁 frontend/              # 前端界面
│   ├── index.html           # 主页面
│   ├── src/
│   │   ├── app.js           # 前端逻辑
│   │   ├── styles/          # CSS 样式
│   │   └── components/      # UI 组件
│   └── dist/                # 构建输出
│
├── 📁 examples/              # 示例与演示代码
│   ├── full_pipeline_demo.py           # 完整流程演示
│   ├── md_highlight_service_demo.py    # 高亮服务演示
│   ├── langextract_demo.py             # LangExtract 基础演示
│   ├── mineru_langextract_fusion_demo.py  # MinerU+LangExtract 融合
│   ├── pymupdf_langextract_fusion.py      # PyMuPDF 备用方案
│   ├── pymupdf_text_extractor.py          # PyMuPDF 文本提取
│   ├── pymupdf_vs_mineru_comparison.py    # 方案对比测试
│   └── pdf_highlight_demo.py              # PDF 高亮演示
│
├── 📁 profiles/              # 配置档案
│   ├── example_profile.yaml # 示例配置
│   └── omdia_smartphone_report.yaml  # Omdia 报告专用配置
│
├── 📁 docs/                  # 文档
│   ├── API_DOCUMENTATION.md      # API 文档
│   ├── IMPLEMENTATION_FUSION_PIPELINE.md  # 实现文档
│   └── ...
│
├── 📁 mineru_output/         # MinerU 解析输出
├── 📁 highlight_output/      # 高亮 PDF 输出
│
├── 📄 api_server.py          # FastAPI 服务
├── 📄 full_pipeline_service.py  # 完整流程服务
├── 📄 mineru_client.py       # MinerU 客户端
├── 📄 md_highlight_service.py   # 高亮服务
├── 📄 md_renderer.py         # Markdown 渲染器
├── 📄 celery_tasks.py        # Celery 任务
├── 📄 start_server.py        # 启动脚本
│
├── 📄 requirements.txt       # Python 依赖
├── 📄 config.yaml            # Dolt 配置
├── 📄 .env                   # 环境变量 (需创建)
│
└── 📄 README.md              # 本文件
```

---

## 🛠️ 开发指南

### 本地开发

```bash
# 1. 安装开发依赖
pip install -r requirements.txt

# 2. 启动 Redis (用于 Celery)
redis-server

# 3. 启动 API 服务
python start_server.py api

# 4. 启动 Celery Worker (新终端)
python start_server.py worker

# 5. 启动 Flower 监控 (可选)
python start_server.py flower
```

### 运行示例

```bash
# 完整流程演示
cd examples
python full_pipeline_demo.py

# MinerU + LangExtract 融合演示
python mineru_langextract_fusion_demo.py

# 回到项目根目录
cd ..

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
