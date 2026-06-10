# agent-copilot

FusionMark 独立智能助手模块。

`agent-copilot` 是一个可独立维护的应用，通过多轮自然语言对话帮助用户生成和优化 FusionMark Profile YAML 配置。它可以单独启动、单独开发、单独部署，与主解析服务解耦。

## 概述

Copilot 通过多轮对话引导用户完成以下操作：

- 根据高层描述生成 Profile YAML 草稿。
- 优化草稿（类别、颜色、OCR 选项、提示词、few-shot 示例等）。
- 在进入编辑器前，对草稿执行 `FullPipelineConfig` 校验。
- 持久化会话状态、检查点和长期归档。

所有保存和激活操作均需用户显式确认，并复用主服务现有的 Profile 管理流程。

## 设计原则

1. **独立应用原则** — 拥有独立的顶级目录，可独立启动。
2. **职责隔离原则** — API、编排、智能逻辑、存储、提示词、校验各自独立，不互相穿透。
3. **运行时与归档分离原则** — Redis 仅存储短期运行时状态，MinIO 负责长期归档。
4. **提示词资产化原则** — 系统提示词、模板、示例统一放在 `app/prompts/` 下管理，不内嵌在业务代码中。
5. **可演进原则** — 第一版使用普通服务编排，后续可平滑迁移到 LangGraph。

## 技术栈

| 组件 | 选型 |
| :--- | :--- |
| 框架 | FastAPI + Uvicorn |
| 语言 | Python >=3.13 |
| 运行时状态 | Redis（会话、检查点，TTL 10 天） |
| 长期归档 | MinIO（JSON 会话归档） |
| 测试 | pytest |
| 包管理 | uv |

## 快速开始

### 1. 配置环境

```powershell
cd agent-copilot
copy .env.example .env
# 根据实际情况修改 Redis / MinIO 地址
```

### 2. 运行

```powershell
# 从 agent-copilot 目录启动
uv run python -m app.main

# 或使用辅助脚本
uv run python scripts/run_agent.py
```

默认地址为 `http://127.0.0.1:8010`。

### 3. 健康检查

```powershell
curl http://127.0.0.1:8010/health
```

## 项目结构

```text
agent-copilot/
├── README.md
├── pyproject.toml
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 入口
│   ├── api/                    # HTTP 路由与依赖
│   ├── core/                   # 编排与服务门面
│   │   ├── service.py          # CopilotCoreService
│   │   └── orchestrator.py     # 编排结果 / 流程壳
│   ├── agent/                  # 意图识别、检索、生成、校验
│   ├── storage/                # 会话、检查点、归档抽象
│   │   ├── session_store.py    # 会话存储（内存 + Redis 适配器）
│   │   ├── checkpoint_store.py # 检查点存储（内存 + Redis 适配器）
│   │   ├── message_store.py    # 消息增删改查边界
│   │   ├── archive_store.py    # 归档存储（空操作 + MinIO 适配器）
│   │   ├── persistence.py      # 统一持久化边界（运行时 + 归档）
│   │   ├── serialization.py    # 模型字典转换 + 归档载荷构建
│   │   ├── redis_store.py      # Redis 会话与检查点实现
│   │   ├── minio_archive.py    # MinIO 归档实现
│   │   └── factory.py          # 内存持久化工厂方法
│   ├── models/                 # 领域对象
│   │   └── session.py          # CopilotSession、CopilotMessage、CopilotCheckpoint
│   ├── schemas/                # 请求 / 响应 DTO
│   │   └── session.py          # MessagePayload、SessionPayload
│   ├── config/                 # 配置
│   │   └── settings.py         # 环境变量驱动的 Settings
│   ├── prompts/                # 提示词资产（system / templates / examples）
│   └── utils/                  # 工具函数
├── scripts/
│   └── run_agent.py            # 独立启动辅助脚本
└── tests/
    ├── conftest.py
    ├── test_external_store_contracts.py # Redis / MinIO key 和 path 合同测试
    ├── test_imports.py         # 应用可导入性冒烟测试
    ├── test_message_store.py   # 消息增删改查边界测试
    ├── test_serialization.py   # 序列化往返 + 归档载荷测试
    └── test_persistence_boundary.py  # 检查点 + 归档流程测试
```

## 当前实现进度

本模块按阶段渐进式构建，以下里程碑已完成：

### ✅ 阶段 1 — 目录骨架
- [x] 独立的 `agent-copilot/` 目录，含 `pyproject.toml` 和 `.env.example`
- [x] FastAPI 启动入口（`app/main.py`）
- [x] 清晰包布局：`api/`、`core/`、`agent/`、`storage/`、`models/`、`schemas/`、`config/`、`prompts/`、`utils/`

### ✅ 阶段 2 — 核心服务骨架
- [x] 会话模型（`CopilotSession`、`CopilotMessage`、`CopilotCheckpoint`）
- [x] 会话、检查点、消息的内存存储实现
- [x] `CopilotCoreService` 门面与 `OrchestrationResult` 编排壳
- [x] 统一持久化边界抽象（`CopilotPersistenceBoundary`），整合运行时状态与长期归档

### ✅ 阶段 3 — 持久化抽象与测试
- [x] 惰性 Redis 适配器（`RedisCopilotSessionStore`、`RedisCheckpointStore`），基于 JSON 序列化
- [x] 惰性 MinIO 适配器（`MinioArchiveStore`），用于会话回放归档
- [x] 序列化层，带 Schema 版本控制（`session_to_dict`、`session_from_dict`、`archive_payload`）
- [x] pytest 覆盖：导入、消息存储、序列化、持久化边界

### ✅ 阶段 4 — 对话状态 Schema 与存储对齐
- [x] `CopilotMessage` 支持 `message_type` 与 `metadata`
- [x] `CopilotCheckpoint` 支持 `step`、`draft_profile`、`validation_result`、`pending_action`、`agent_trace`
- [x] `CopilotSession` 支持 `current_draft`、`pending_action`、`last_validation_result`
- [x] 序列化 Schema 升级到 `1.1`，并兼容读取旧 `1.0` payload
- [x] Redis key 模式保持不变，仅扩展 JSON payload
- [x] MinIO 归档路径保持不变，并扩展 replay payload
- [x] pytest 覆盖：enriched round trip、legacy payload、checkpoint step、Redis/MinIO 合同

### 🔄 后续工作
- [ ] LangGraph 兼容的状态机与节点边界
- [ ] 意图守卫（Intent Gatekeeper）、上下文召回、草稿生成、草稿校验
- [ ] Profile 上下文提供器（通过 `ProfileManager` 读取历史配置）
- [ ] HTTP API 路由（`POST /sessions`、`POST /sessions/{id}/messages` 等）
- [ ] 前端 Copilot 面板集成（`web-pc`）
- [ ] `app/prompts/` 下的提示词资产

## 存储设计

### Redis（运行时状态）

| Key 模式 | 类型 | 用途 |
| :--- | :--- | :--- |
| `agent-copilot:session:{sessionId}` | STRING（JSON） | 会话快照 |
| `agent-copilot:session:{sessionId}:checkpoints` | ZSET | 有序检查点列表 |

默认 TTL 为 **10 天**，防止无限膨胀；长期留存由 MinIO 负责。

### MinIO（长期归档）

```text
{prefix}/{project}/{env}/agent/{userId}/session/{sessionId}.json
```

归档载荷包含会话元信息、消息历史、检查点摘要、当前草稿、校验结果、待确认动作、agent trace 和汇总统计块。

## Schema 版本

当前序列化版本为 `1.1`。

| 对象 | 当前扩展字段 | 用途 |
| :--- | :--- | :--- |
| `CopilotMessage` | `message_type`、`metadata` | 区分普通文本、草稿摘要、校验摘要、确认请求等消息类型 |
| `CopilotCheckpoint` | `step`、`draft_profile`、`validation_result`、`pending_action`、`agent_trace` | 保存关键对话节点的可回放快照 |
| `CopilotSession` | `current_draft`、`pending_action`、`last_validation_result` | 快速恢复当前草稿、确认动作和最近校验状态 |

兼容策略：

- 新写入 payload 使用 `schema_version = "1.1"`。
- 旧 `1.0` payload 缺少新字段时默认读取为 `None` 或 `text`。
- Redis key 与 MinIO object path 不随 schema 升级改变。

## 测试

```powershell
# 运行全部模块测试
cd agent-copilot
uv run pytest
```

当前测试覆盖：

- 应用可导入性与 FastAPI 实例创建
- 内存消息增删改查操作
- 数据类序列化往返、旧 payload 兼容与归档载荷结构
- 持久化边界检查点创建、step 捕获与归档流程
- Redis session / checkpoint key 合同
- MinIO archive object path 合同

## 环境变量

| 变量 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `APP_NAME` | `agent-copilot` | 应用名称 |
| `APP_ENV` | `dev` | 环境标识 |
| `APP_HOST` | `127.0.0.1` | 绑定地址 |
| `APP_PORT` | `8010` | 绑定端口 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接地址 |
| `SESSION_TTL_DAYS` | `10` | Redis 中会话 TTL |
| `MINIO_ENDPOINT` | `127.0.0.1:9000` | MinIO 端点 |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO 访问密钥 |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO  secret 密钥 |
| `MINIO_BUCKET` | `fusion-mark` | MinIO 存储桶 |
| `MINIO_PREFIX` | `fusion-mark` | MinIO 对象前缀 |
| `MINIO_SECURE` | `false` | MinIO 是否启用 TLS |

## 相关文档

- `docs/智能体架构设计/智能体模块化架构设计.md` — 模块化架构与目录设计
- `docs/智能体架构设计/Copilot对话智能架构设计.md` — 对话智能、状态机、Redis / MinIO 存储映射设计
- `docs/智能体架构设计/存储设计.md` — Redis / MinIO 存储 Key 设计
- `docs/Fusion_Mark_Config_Copilot_Design.md` — 原始 Copilot 设计方案
- `docs/Fusion_Mark_Config_Copilot_Implementation_Recommendation.md` — 实施建议与阶段规划
- `openspec/changes/archive/2026-05-31-standalone-agent-copilot-app/` — 本模块的 OpenSpec change 归档
- `openspec/changes/archive/2026-06-10-copilot-schema-storage-alignment/` — 对话状态 Schema 与存储对齐归档

## 注意事项

- Copilot **不会**自动执行保存或激活操作。所有副作用动作均需用户显式确认，并委托给现有的 Profile 管理 API。
- 第一阶段存储默认使用内存实现。Redis 和 MinIO 适配器已提供，但需要安装对应的 Python 包（`redis`、`minio`）并启动相关服务。
