# Copilot 对话智能架构设计

## 1. 目标

本文档面向 FusionMark `agent-copilot` 模块，定义配置智能小助手的对话智能架构。

Copilot 的核心目标不是做通用聊天，而是通过多轮对话稳定完成 Profile YAML 配置的生成、修改、校验、确认和归档。系统必须与现有 Redis / MinIO 存储模式对应，保证会话可恢复、关键过程可回放、长期结果可审计。

本设计基于当前已存在的存储边界：

- Redis 保存短期运行时状态。
- MinIO 保存长期会话归档。
- `CopilotSession` 保存会话快照和消息流。
- `CopilotCheckpoint` 保存关键节点快照。
- `archive_payload` 输出完整归档载荷。

---

## 2. 设计原则

1. **配置任务优先**
   Copilot 以生成和优化 FusionMark Profile YAML 为核心任务，不做无边界闲聊。

2. **状态可恢复**
   任意会话在 Redis TTL 内应能恢复到最近状态，关键步骤通过 checkpoint 回放。

3. **归档可审计**
   会话结束或用户显式归档时，应把完整 replay payload 写入 MinIO。

4. **副作用显式确认**
   保存、覆盖、激活 Profile 等动作必须等待用户确认。Copilot 只能生成计划，不能静默执行。

5. **模型输出必须校验**
   模型生成的 YAML 草稿不能直接信任，必须经过 `FullPipelineConfig` 或等价配置校验。

6. **节点插件化**
   意图识别、上下文召回、草稿生成、草稿修复、响应组织等能力应拆成可替换节点，便于后续升级 LangGraph。

7. **提示词资产化**
   系统提示词、任务模板、few-shot 示例必须放入 `app/prompts/`，不直接写死在业务代码中。

---

## 3. 总体架构

```text
前端 Copilot 面板
        │
        ▼
HTTP / SSE API
        │
        ▼
CopilotCoreService
        │
        ▼
ConversationOrchestrator
        │
        ├── Intent Gatekeeper
        ├── Context Retriever
        ├── Draft Generator
        ├── Draft Refiner
        ├── Config Validator
        ├── Save Planner
        └── Response Composer
        │
        ▼
CopilotPersistenceBoundary
        │
        ├── RedisCopilotSessionStore
        ├── RedisCheckpointStore
        └── MinioArchiveStore
```

### 3.1 分层职责

| 层级 | 模块 | 职责 |
|---|---|---|
| 接口层 | `app/api/` | 创建会话、发送消息、确认动作、查询 checkpoint |
| 服务层 | `CopilotCoreService` | 对外门面，隐藏编排和存储细节 |
| 编排层 | `ConversationOrchestrator` | 推进状态机，选择并执行智能节点 |
| 智能节点层 | `app/agent/` | 意图、上下文、生成、校验、修复、响应 |
| 存储边界 | `CopilotPersistenceBoundary` | 会话、消息、checkpoint、归档统一入口 |
| 适配层 | Redis / MinIO | 运行时状态和长期归档 |

---

## 4. 对话状态机

### 4.1 状态列表

建议使用 `CopilotSession.current_step` 保存当前会话状态。

| 状态 | 含义 |
|---|---|
| `created` | 会话已创建，还没有有效用户需求 |
| `intake_requirement` | 正在理解用户配置目标 |
| `context_ready` | 已完成上下文召回 |
| `drafting_profile` | 正在生成 Profile 草稿 |
| `validating_profile` | 正在校验 Profile 草稿 |
| `repairing_draft` | 校验失败后正在修复草稿 |
| `reviewing_draft` | 草稿可展示，等待用户查看 |
| `waiting_user_confirmation` | 等待用户确认保存、覆盖或激活 |
| `save_requested` | 用户已确认保存，等待执行保存流程 |
| `archived` | 会话已归档 |
| `failed` | 编排失败，需要人工或重试 |

### 4.2 状态流转

```text
created
  │
  ▼
intake_requirement
  │
  ▼
context_ready
  │
  ▼
drafting_profile
  │
  ▼
validating_profile
  │
  ├── valid
  │     ▼
  │   reviewing_draft
  │     │
  │     ▼
  │   waiting_user_confirmation
  │
  └── invalid
        ▼
      repairing_draft
        │
        ▼
      validating_profile

waiting_user_confirmation
  ├── revise ───▶ drafting_profile
  ├── save ─────▶ save_requested
  └── cancel ───▶ archived
```

### 4.3 状态推进规则

1. 每次用户消息进入后，先写入 `session.messages`。
2. 编排器根据当前 `current_step` 和最新意图选择下一节点。
3. 关键节点执行后创建 checkpoint。
4. 每次状态变化都保存 session。
5. 会话结束或用户请求归档时写入 MinIO。

---

## 5. 智能节点设计

### 5.1 Intent Gatekeeper

职责：

- 判断用户意图。
- 阻断无关请求或危险请求。
- 判断是否需要追问。
- 判断是否进入保存确认流程。

建议输出：

```json
{
  "intent": "create_profile",
  "confidence": 0.86,
  "requires_clarification": false,
  "blocked": false,
  "reason": ""
}
```

核心意图：

| intent | 含义 |
|---|---|
| `create_profile` | 创建新 Profile |
| `revise_profile` | 修改当前草稿 |
| `explain_profile` | 解释已有配置 |
| `validate_profile` | 校验当前草稿 |
| `repair_profile` | 修复校验错误 |
| `save_profile` | 请求保存 Profile |
| `activate_profile` | 请求激活 Profile |
| `small_talk` | 非配置任务闲聊 |
| `unsupported` | 不支持的请求 |

### 5.2 Context Retriever

职责：

- 读取当前会话消息。
- 读取当前草稿。
- 读取历史 Profile 或模板。
- 提供 `FullPipelineConfig` 结构说明。
- 汇总 LangExtract / MinerU 相关约束。

上下文来源建议记录到 `agent_trace.context_sources`，用于归档审计。

### 5.3 Draft Generator

职责：

- 根据用户需求生成 Profile 草稿。
- 输出结构化对象，不直接输出散乱自然语言。
- 保证草稿能被后续 YAML 构建器消费。

建议输出：

```json
{
  "draft_profile": {},
  "assumptions": [],
  "questions": [],
  "confidence": 0.78
}
```

### 5.4 Draft Refiner

职责：

- 在已有草稿基础上做局部修改。
- 保留用户未要求修改的字段。
- 记录修改摘要。

典型场景：

- 用户要求增加分类。
- 用户要求调整颜色。
- 用户要求减少 OCR 或模型开销。
- 用户要求修改提示词示例。

### 5.5 Config Validator

职责：

- 调用真实配置模型进行校验。
- 返回结构化错误。
- 不依赖模型自行判断合法性。

建议输出：

```json
{
  "valid": false,
  "errors": [
    {
      "path": "categories[0].color",
      "message": "Invalid color format",
      "severity": "error"
    }
  ]
}
```

### 5.6 Repair Node

职责：

- 根据校验错误修复草稿。
- 只修复错误字段，避免重写整个配置。
- 修复后重新进入 `validating_profile`。

### 5.7 Save Planner

职责：

- 生成保存、覆盖、激活计划。
- 明确展示将影响的 Profile 名称、路径或 ID。
- 等待用户确认。

Save Planner 不直接执行副作用动作。

### 5.8 Response Composer

职责：

- 把节点输出整理成用户可读回复。
- 明确展示草稿状态、校验结果、下一步动作。
- 避免把内部 trace、完整 prompt 或敏感信息暴露给前端。

---

## 6. Redis 存储映射

当前实现中 Redis 使用 JSON payload 保存 session，并用 ZSET 保存 checkpoint。

### 6.1 Session Key

```text
agent-copilot:session:{session_id}
```

类型：`STRING`

内容：`session_to_dict(session)` 序列化后的 JSON。

示例：

```json
{
  "schema_version": "1.0",
  "session_id": "s1001",
  "user_id": "u1001",
  "messages": [],
  "checkpoints": [],
  "current_step": "reviewing_draft",
  "created_at": "2026-06-10T04:00:00+00:00",
  "updated_at": "2026-06-10T04:05:00+00:00"
}
```

### 6.2 Checkpoint Key

```text
agent-copilot:session:{session_id}:checkpoints
```

类型：`ZSET`

member：`checkpoint_to_dict(checkpoint)` 序列化后的 JSON。

score：checkpoint 顺序号。

### 6.3 TTL

默认 TTL 为 10 天，即 `864000` 秒。

TTL 适用于：

- session key
- checkpoint zset key

Redis 只承担短期恢复能力，长期保留交给 MinIO。

---

## 7. MinIO 归档映射

当前实现中 MinIO 对象路径为：

```text
{prefix}/{project}/{env}/agent/{user_id}/session/{session_id}.json
```

默认值示例：

```text
fusion-mark/fusion-mark/dev/agent/u1001/session/s1001.json
```

归档内容来自 `archive_payload(session, checkpoints, project, env)`。

MinIO 归档不是 Redis 原始结构的复制，而是稳定的业务回放格式，应包含：

- 会话元信息
- 消息历史
- checkpoint 列表
- 当前状态
- 草稿快照
- 校验结果
- 智能节点 trace
- 汇总统计

---

## 8. Schema 演进建议

当前 `SCHEMA_VERSION` 为 `1.0`。为了让对话智能状态和 Redis / MinIO 对齐，建议演进到 `1.1`。

### 8.1 Message 扩展

当前：

```python
class CopilotMessage:
    role: str
    content: str
    created_at: str
```

建议扩展：

```python
class CopilotMessage:
    role: str
    content: str
    message_type: str = "text"
    metadata: dict | None = None
    created_at: str
```

`message_type` 建议值：

| 类型 | 含义 |
|---|---|
| `text` | 普通文本消息 |
| `draft_summary` | 草稿摘要 |
| `validation_summary` | 校验摘要 |
| `confirmation_request` | 确认请求 |
| `system_event` | 系统事件 |

### 8.2 Checkpoint 扩展

当前：

```python
class CopilotCheckpoint:
    checkpoint_id: str
    parent_checkpoint_id: Optional[str]
    messages: List[CopilotMessage]
    created_at: str
```

建议扩展：

```python
class CopilotCheckpoint:
    checkpoint_id: str
    parent_checkpoint_id: Optional[str]
    step: str
    messages: List[CopilotMessage]
    draft_profile: dict | None
    validation_result: dict | None
    pending_action: dict | None
    agent_trace: dict | None
    created_at: str
```

字段说明：

| 字段 | 用途 |
|---|---|
| `step` | checkpoint 创建时的状态 |
| `draft_profile` | 当前 Profile 草稿 |
| `validation_result` | 最近一次校验结果 |
| `pending_action` | 等待用户确认的动作 |
| `agent_trace` | 意图、节点、模型、prompt 版本、上下文来源 |

### 8.3 Session 扩展

当前：

```python
class CopilotSession:
    session_id: str
    user_id: str
    messages: List[CopilotMessage]
    checkpoints: List[CopilotCheckpoint]
    current_step: str
    created_at: str
    updated_at: str
```

建议扩展：

```python
class CopilotSession:
    session_id: str
    user_id: str
    messages: List[CopilotMessage]
    checkpoints: List[CopilotCheckpoint]
    current_step: str
    current_draft: dict | None
    pending_action: dict | None
    last_validation_result: dict | None
    created_at: str
    updated_at: str
```

说明：

- `current_draft` 用于快速恢复当前草稿。
- `pending_action` 用于保存、覆盖、激活等确认动作。
- `last_validation_result` 用于前端直接展示最近校验状态。

---

## 9. Agent Trace 设计

`agent_trace` 用于记录智能节点执行过程，便于调试、审计和效果评估。

建议结构：

```json
{
  "intent": "create_profile",
  "node": "draft_generator",
  "model": "configured-model-name",
  "prompt_version": "generation/profile_draft/v1",
  "context_sources": [
    "current_messages",
    "profile_schema",
    "historical_profiles"
  ],
  "input_summary": "用户希望为论文 PDF 生成高亮配置",
  "output_summary": "生成包含定义、方法、结论三类的草稿",
  "latency_ms": 1280
}
```

注意：

- 不要在 trace 中保存 API key、完整系统提示词或敏感上下文。
- 可以保存 prompt 版本和摘要。
- 可以保存上下文来源，便于排查生成质量。

---

## 10. 一次消息处理流程

```text
POST /api/v1/agent/sessions/{session_id}/messages
        │
        ▼
load session from Redis
        │
        ▼
append user message
        │
        ▼
Intent Gatekeeper
        │
        ▼
Context Retriever
        │
        ▼
Draft Generator / Refiner / Validator / Save Planner
        │
        ▼
append assistant message
        │
        ▼
update current_step / current_draft / validation_result
        │
        ▼
save session to Redis
        │
        ▼
create checkpoint when needed
        │
        ▼
return response payload
```

建议响应结构：

```json
{
  "session_id": "s1001",
  "current_step": "reviewing_draft",
  "message": {
    "role": "assistant",
    "content": "已生成 Profile 草稿，并通过基础校验。"
  },
  "draft_profile": {},
  "validation_result": {
    "valid": true,
    "errors": []
  },
  "next_actions": [
    "revise",
    "save",
    "cancel"
  ]
}
```

---

## 11. Checkpoint 创建策略

不建议每条消息都创建 checkpoint。建议在关键业务节点创建：

| 触发点 | step |
|---|---|
| 用户需求澄清完成 | `intake_requirement` |
| 上下文召回完成 | `context_ready` |
| 首次草稿生成完成 | `drafting_profile` |
| 配置校验完成 | `validating_profile` |
| 自动修复完成 | `repairing_draft` |
| 进入确认前 | `waiting_user_confirmation` |
| 会话归档前 | `archived` |

checkpoint 应保存：

- 当时的消息快照
- 当前状态
- 当前草稿
- 校验结果
- 待确认动作
- agent trace

---

## 12. 确认动作设计

需要用户确认的动作统一使用 `pending_action` 表示。

示例：

```json
{
  "action": "save_profile",
  "profile_name": "paper_highlight_default",
  "target": "profile-manager",
  "overwrite": false,
  "requires_confirmation": true,
  "created_at": "2026-06-10T04:10:00+00:00"
}
```

确认流程：

```text
Save Planner 生成 pending_action
        │
        ▼
session.current_step = waiting_user_confirmation
        │
        ▼
前端展示影响范围
        │
        ▼
用户确认
        │
        ▼
POST /confirm
        │
        ▼
后端执行保存 / 覆盖 / 激活
        │
        ▼
创建 checkpoint 并归档
```

---

## 13. API 建议

第一版 API 围绕会话和消息组织：

```text
POST   /api/v1/agent/sessions
GET    /api/v1/agent/sessions/{session_id}
POST   /api/v1/agent/sessions/{session_id}/messages
POST   /api/v1/agent/sessions/{session_id}/confirm
GET    /api/v1/agent/sessions/{session_id}/checkpoints
POST   /api/v1/agent/sessions/{session_id}/archive
```

接口职责：

| 接口 | 职责 |
|---|---|
| `POST /sessions` | 创建新会话 |
| `GET /sessions/{id}` | 读取会话快照 |
| `POST /messages` | 发送用户消息并推进状态机 |
| `POST /confirm` | 确认待执行动作 |
| `GET /checkpoints` | 查看 checkpoint 列表 |
| `POST /archive` | 写入 MinIO 长期归档 |

---

## 14. Prompt 资产设计

建议目录：

```text
agent-copilot/app/prompts/
├── system/
│   ├── copilot_system.md
│   └── safety_boundary.md
├── intents/
│   └── intent_gatekeeper.md
├── generation/
│   ├── profile_draft.md
│   └── profile_revision.md
├── validation/
│   └── repair_from_validation_error.md
└── examples/
    ├── profile_minimal.md
    └── profile_paper_highlight.md
```

PromptProvider 职责：

- 按名称加载 prompt。
- 注入变量。
- 返回 prompt 版本。
- 支持后续灰度和 A/B 测试。

归档时只保存 `prompt_version`，不保存完整 prompt 文本。

---

## 15. LangGraph 演进路径

第一版建议使用普通 Python 编排器，不强制接 LangGraph，但节点边界按图模型设计。

未来可映射为：

```text
intent_gatekeeper
        │
        ▼
context_retriever
        │
        ▼
draft_generator
        │
        ▼
config_validator
        │
        ├── valid ─────▶ human_review
        └── invalid ───▶ repair_node ───▶ config_validator

human_review
        │
        ├── revise ───▶ draft_refiner
        ├── save ─────▶ save_planner
        └── cancel ───▶ archive_node
```

这样第一版能快速落地，后续迁移 LangGraph 时只需要替换 `ConversationOrchestrator` 内部实现，不需要重写 API 和存储层。

---

## 16. 实施顺序

建议分阶段实施：

### 阶段 1：Schema 和存储对齐

- 将 `SCHEMA_VERSION` 升级到 `1.1`。
- 扩展 `CopilotMessage`。
- 扩展 `CopilotCheckpoint`。
- 视实现复杂度扩展 `CopilotSession`。
- 更新 `session_to_dict`、`checkpoint_to_dict`、`archive_payload`。
- 保持对 `1.0` 数据的兼容读取。

### 阶段 2：编排器骨架

- 新增 `ConversationOrchestrator`。
- 定义 `handle_message(session_id, content)`。
- 实现状态推进。
- 接入 `CopilotPersistenceBoundary`。

### 阶段 3：智能节点最小闭环

- 实现 Intent Gatekeeper。
- 实现 Context Retriever。
- 实现 Draft Generator。
- 实现 Config Validator。
- 实现 Response Composer。

### 阶段 4：确认动作和归档

- 实现 `pending_action`。
- 实现 `/confirm`。
- 在确认后创建 checkpoint。
- 将完整 payload 写入 MinIO。

### 阶段 5：前端集成

- 会话列表。
- 对话区。
- 草稿预览区。
- 校验结果区。
- 保存 / 修改 / 取消确认控件。

---

## 17. 验收标准

第一版完成后应满足：

1. 用户可以创建 Copilot 会话。
2. 用户可以通过消息生成 Profile 草稿。
3. 系统能把用户消息和助手消息写入 Redis session。
4. 系统能在关键节点写入 Redis checkpoint。
5. 系统能从 Redis 恢复会话和 checkpoint。
6. 系统能调用真实配置校验。
7. 校验失败时能生成修复建议或自动修复草稿。
8. 保存、覆盖、激活动作必须等待用户确认。
9. 会话可归档到 MinIO。
10. MinIO payload 能回放消息、草稿、校验结果和关键 trace。

---

## 18. 风险和约束

| 风险 | 处理方式 |
|---|---|
| 模型生成 YAML 不稳定 | 使用结构化输出 + 后端真实校验 |
| Redis 数据膨胀 | TTL 控制，长期数据写入 MinIO |
| checkpoint 过多 | 只在关键节点创建 checkpoint |
| trace 泄露敏感信息 | 只保存摘要、版本和来源，不保存密钥和完整 prompt |
| 一开始引入 LangGraph 复杂度过高 | 第一版使用普通编排器，保持节点边界兼容 |
| session schema 升级破坏旧数据 | `session_from_dict` 保持默认值和兼容读取 |

---

## 19. 结论

Copilot 对话智能应围绕“可恢复的配置生成流程”设计，而不是围绕“聊天机器人”设计。

推荐架构是：

```text
session.messages 保存对话流
session.current_step 保存当前状态
session.current_draft 保存当前草稿
checkpoint 保存关键节点快照
agent_trace 保存智能节点摘要
Redis 保存短期运行状态
MinIO 保存长期回放归档
```

这样可以与当前 `agent-copilot` 已有的 Redis / MinIO 存储实现自然对应，同时为后续 LangGraph、前端 Copilot 面板、Profile 管理 API 集成留下清晰扩展点。
