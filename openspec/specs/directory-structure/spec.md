# 服务层目录结构

## 概述

将所有后端 Python 服务文件统一组织在 `services/` 目录下，按功能分类存放，简化命名，废弃代码隔离。

## 需求

### Requirement: Services 目录结构

The system SHALL organize all backend Python service files under a unified `services/` directory with clear sub-directory categorization.

#### Scenario: Navigate to API layer
- **WHEN** developer needs to modify API endpoints
- **THEN** all API-related files are located in `services/api/`

#### Scenario: Navigate to core business logic
- **WHEN** developer needs to modify business logic
- **THEN** all core service files are located in `services/core/`

#### Scenario: Navigate to third-party clients
- **WHEN** developer needs to modify external API integrations
- **THEN** all client files are located in `services/clients/`

---

### Requirement: Import path updates

All internal module imports SHALL be updated to reflect the new directory structure using absolute or relative imports.

#### Scenario: Import from core module
- **WHEN** api/server.py needs to import FullPipelineService
- **THEN** it uses `from ..core.full_pipeline import FullPipelineService`

#### Scenario: Import from clients module
- **WHEN** core service needs to import MinerUClient
- **THEN** it uses `from ..clients.mineru import MinerUClient`

#### Scenario: Import from utils module
- **WHEN** any service needs to import MarkdownRenderer
- **THEN** it uses `from ..utils.renderer import MarkdownRenderer`

---

### Requirement: Legacy code isolation

Deprecated Celery-related code SHALL be moved to `services/legacy/` directory to clearly indicate its status.

#### Scenario: Identify deprecated code
- **WHEN** developer sees `services/legacy/` directory
- **THEN** they understand these files are scheduled for removal

---

### Requirement: Project documentation

All project documentation SHALL be updated to reference the new file paths.

#### Scenario: Read README.md
- **WHEN** new developer reads README.md
- **THEN** all file paths point to `services/` directory
- **AND** startup commands reference `services/start.py`

#### Scenario: Read AGENTS.md
- **WHEN** AI agent reads AGENTS.md
- **THEN** project structure description matches the new layout

---

### Requirement: Service startup

The service startup process SHALL work with the new directory structure.

#### Scenario: Start development server
- **WHEN** developer runs `python services/start.py`
- **THEN** FastAPI server starts successfully
- **AND** all modules are imported correctly

#### Scenario: Module execution
- **WHEN** developer runs `python -m services.start`
- **THEN** server starts successfully using module syntax

---

## 文件映射

| 旧路径 | 新路径 | 说明 |
|--------|--------|------|
| `api_server.py` | `services/api/server.py` | 目录提供上下文 |
| `full_pipeline_service.py` | `services/core/full_pipeline.py` | 简化命名 |
| `md_highlight_service.py` | `services/core/highlight.py` | 简化命名 |
| `md_highlight_pipeline.py` | `services/pipelines/highlight.py` | 简化命名 |
| `md_renderer.py` | `services/utils/renderer.py` | 简化命名 |
| `mineru_client.py` | `services/clients/mineru.py` | 简化命名 |
| `start_server.py` | `services/start.py` | 简化命名 |

## 目录结构

```
services/
├── api/                    # API 层
│   ├── server.py          # FastAPI 服务
│   ├── progress_store.py  # Redis 进度存储
│   ├── websocket_handler.py
│   └── task_processor.py
├── core/                   # 核心业务
│   ├── full_pipeline.py   # 完整流程服务
│   └── highlight.py       # 高亮服务
├── clients/                # 第三方客户端
│   └── mineru.py          # MinerU API 客户端
├── pipelines/              # 处理管道
│   └── highlight.py       # 高亮管道
├── utils/                  # 工具模块
│   └── renderer.py        # Markdown 渲染器
├── legacy/                 # 废弃代码
│   ├── celery_config.py
│   ├── celery_tasks.py
│   └── md_highlight_pdf.py
├── profiles/               # 配置档案
├── examples/               # 示例代码
├── start.py               # 启动脚本
├── requirements.txt       # Python 依赖
└── .env                   # 环境变量
```
