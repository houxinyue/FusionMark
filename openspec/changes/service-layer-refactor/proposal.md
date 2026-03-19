# 服务层代码目录重构提案

## 变更概述

将目前散落在项目根目录下的服务类 Python 文件统一迁移到 `services/` 目录中，建立清晰的服务层架构。

## 动机 (Why)

### 当前问题
1. **根目录杂乱**: 10+ 个 Python 服务文件散落在根目录，难以快速定位
2. **职责不清晰**: 没有明确的分层，服务、客户端、配置混杂
3. **可维护性差**: 新开发者难以快速理解项目结构
4. **扩展困难**: 添加新服务时不知道该放哪里

### 预期收益
- 清晰的目录结构，前后端分离 (`frontend/` ↔ `services/`)
- 明确的服务层边界，便于模块化开发
- 为未来微服务拆分做准备

## 范围 (What)

### 迁移文件清单

| 源文件 | 目标位置 | 说明 |
|--------|----------|------|
| `api_server.py` | `services/api/server.py` | FastAPI 主入口 |
| `full_pipeline_service.py` | `services/core/full_pipeline.py` | 完整流程服务 |
| `md_highlight_service.py` | `services/core/highlight.py` | 高亮服务 |
| `md_highlight_pipeline.py` | `services/pipelines/highlight.py` | 高亮管道 |
| `md_renderer.py` | `services/utils/renderer.py` | Markdown 渲染器 |
| `mineru_client.py` | `services/clients/mineru.py` | MinerU 客户端 |
| `celery_config.py` | `services/legacy/celery_config.py` | Celery 配置(废弃) |
| `celery_tasks.py` | `services/legacy/celery_tasks.py` | Celery 任务(废弃) |
| `start_server.py` | `services/start.py` | 启动脚本 |

### 目录结构

```
fusion-mark/
├── services/                      # 服务层根目录
│   ├── __init__.py               # 包初始化
│   ├── start.py                  # 服务启动脚本
│   ├── api/                      # API 层
│   │   ├── __init__.py
│   │   ├── server.py             # FastAPI 主入口
│   │   └── routes/               # 路由模块(未来拆分)
│   ├── core/                     # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── full_pipeline.py      # 完整流程服务
│   │   └── highlight.py          # 高亮服务
│   ├── clients/                  # 第三方客户端
│   │   ├── __init__.py
│   │   └── mineru.py             # MinerU API 客户端
│   ├── pipelines/                # 处理管道
│   │   ├── __init__.py
│   │   └── highlight.py          # 高亮管道
│   ├── utils/                    # 工具模块
│   │   ├── __init__.py
│   │   └── renderer.py           # Markdown 渲染器
│   └── legacy/                   # 待废弃代码
│       ├── __init__.py
│       ├── celery_config.py      # Celery 配置
│       └── celery_tasks.py       # Celery 任务
├── frontend/                     # 前端代码(已有)
├── docs/                         # 文档(需更新)
└── ...
```

## 影响分析

### 需要修改的地方

1. **Python 导入路径**: 所有内部模块引用需要更新
2. **启动命令**: `python start_server.py` → `python services/start.py`
3. **配置文件路径**: 检查代码中是否有硬编码路径
4. **文档**: 更新 README.md、AGENTS.md 等文档中的文件引用

### 兼容性考虑

- 在根目录保留 **兼容层** (可选): 临时保留软链接或 shim 文件，指向新位置
- 更新 `requirements.txt` 如果需要
- 确保 `__init__.py` 正确设置包导入

## 非目标 (Out of Scope)

- 不修改业务逻辑代码，仅迁移位置
- 不重构代码结构（保留到后续任务）
- 不删除 `celery_chain_pipeline/` 目录（已有独立任务处理）

## 验收标准

- [ ] 所有服务类文件迁移到 `services/` 目录
- [ ] Python 导入路径更新正确，可正常启动
- [ ] 相关文档（README.md、AGENTS.md）更新完成
- [ ] 项目根目录仅剩入口脚本和配置（可选）

## 参考

- AGENTS.md 中的项目结构规范
- docs/ 目录下的架构文档
