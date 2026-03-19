# 服务层重构任务清单

## 完成状态

✅ **所有任务已完成** - 服务层目录重构于 2026-03-19 完成

---

## Phase 1: 目录结构搭建 ✅

- [x] 创建 `services/` 目录结构
  - [x] `services/api/` - API 层
  - [x] `services/core/` - 核心业务
  - [x] `services/clients/` - 第三方客户端
  - [x] `services/pipelines/` - 处理管道
  - [x] `services/utils/` - 工具模块
  - [x] `services/legacy/` - 待废弃代码

- [x] 创建所有 `__init__.py` 文件

---

## Phase 2: 代码迁移与导入修复 ✅

### 2.1 API 层 (`services/api/`)

- [x] 迁移 `api_server.py` → `services/api/server.py`
  - [x] 更新文件内所有导入路径
  - [x] 确保相对导入正确 (`..core`, `..clients` 等)

### 2.2 核心业务 (`services/core/`)

- [x] 迁移 `full_pipeline_service.py` → `services/core/full_pipeline.py`
  - [x] 更新导入路径
- [x] 迁移 `md_highlight_service.py` → `services/core/highlight.py`
  - [x] 更新导入路径

### 2.3 客户端 (`services/clients/`)

- [x] 迁移 `mineru_client.py` → `services/clients/mineru.py`
  - [x] 更新导入路径

### 2.4 管道 (`services/pipelines/`)

- [x] 迁移 `md_highlight_pipeline.py` → `services/pipelines/highlight.py`
  - [x] 更新导入路径

### 2.5 工具模块 (`services/utils/`)

- [x] 迁移 `md_renderer.py` → `services/utils/renderer.py`
  - [x] 更新导入路径

### 2.6 遗留代码 (`services/legacy/`)

- [x] 迁移 `celery_config.py` → `services/legacy/celery_config.py`
- [x] 迁移 `celery_tasks.py` → `services/legacy/celery_tasks.py`
- [x] 迁移 `md_highlight_pdf.py` → `services/legacy/md_highlight_pdf.py`

### 2.7 启动脚本

- [x] 创建 `services/start.py`
  - [x] 更新导入路径
  - [x] 确保可以作为模块启动

---

## Phase 3: 配置文件迁移 ✅

- [x] 迁移 `.env` → `services/.env`
- [x] 迁移 `requirements.txt` → `services/requirements.txt`
- [x] 创建 `services/.gitignore`
- [x] 迁移 `profiles/` → `services/profiles/`
- [x] 迁移 `examples/` → `services/examples/`
- [x] 迁移 `celery_chain_pipeline/` → `services/celery_chain_pipeline/`
- [x] 创建 `services/mineru_output/` 和 `services/highlight_output/`
- [x] 更新环境变量加载路径

---

## Phase 4: 文档更新 ✅

### 4.1 主文档

- [x] 创建 `services/README.md`
  - [x] 服务层独立项目说明
  - [x] 启动命令和使用方式
  - [x] 项目结构说明

- [x] 更新根目录 `README.md`
  - [x] 更新项目结构描述
  - [x] 更新启动命令
  - [x] 关联到 services/README.md

- [x] 更新 `AGENTS.md`
  - [x] 简化项目结构说明
  - [x] 指向根目录 README.md

---

## Phase 5: 清理 ✅

- [x] 删除根目录旧文件
  - [x] 删除 `api_server.py`
  - [x] 删除 `full_pipeline_service.py`
  - [x] 删除 `md_highlight_service.py`
  - [x] 删除 `mineru_client.py`
  - [x] 删除 `md_renderer.py`
  - [x] 删除 `md_highlight_pipeline.py`
  - [x] 删除 `celery_config.py`
  - [x] 删除 `celery_tasks.py`
  - [x] 删除 `start_server.py`
  - [x] 删除 `md_highlight_pdf.py`
  - [x] 删除 `.env`
  - [x] 删除 `requirements.txt`
  - [x] 删除根目录 `mineru_output/` 和 `highlight_output/`

---

## 最终结果

```
fusion-mark/
├── docs/                       # 文档
├── frontend/                   # 前端界面
├── services/                   # ⭐ 完整的后端服务项目 (可独立运行)
│   ├── api/                    # API 层
│   ├── core/                   # 核心业务
│   ├── clients/                # 第三方客户端
│   ├── pipelines/              # 处理管道
│   ├── utils/                  # 工具模块
│   ├── legacy/                 # 废弃代码
│   ├── profiles/               # 配置档案
│   ├── examples/               # 示例代码
│   ├── celery_chain_pipeline/  # Celery 链式管道示例
│   ├── mineru_output/          # MinerU 输出
│   ├── highlight_output/       # 高亮输出
│   ├── start.py                # 启动脚本
│   ├── requirements.txt        # Python 依赖
│   ├── .env                    # 环境变量
│   ├── .gitignore              # Git 忽略
│   └── README.md               # 服务层说明
├── LICENSE
├── .gitattributes
├── .gitignore
├── AGENTS.md
└── README.md
```

---

## 关联任务

- Beads Issue: `fusion-mark-1of` - 已关闭
- 关闭时间: 2026-03-19
- 关闭原因: 服务层代码目录重构完成
