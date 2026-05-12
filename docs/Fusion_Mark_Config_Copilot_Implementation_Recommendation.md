# Fusion-Mark Config Copilot 实施建议

## 1. 结论

Config Copilot 功能值得做，但不建议第一版直接落地为完整的 LangGraph + Chroma + Ollama 复杂 Agent 系统。

当前项目已经具备较完整的 Profile 管理链路：

```text
ProfileManager -> StorageProvider -> Redis active state -> FastAPI -> web-pc ConfigView
```

因此 Config Copilot 的正确定位应是：

> 面向 Profile YAML 的对话式草稿助手，负责生成、修改、解释和校验配置草稿；保存、激活等副作用操作必须复用现有 ProfileManager/API，并由用户显式确认。

第一版应优先实现“可控、可审查、可验证”的 Profile 草稿 Copilot，而不是让 Agent 直接拥有完整业务执行权。

## 2. 对现有设计文档的客观评价

`docs/Fusion_Mark_Config_Copilot_Design.md` 中的总体方向是合理的：

- 通过自然语言降低 YAML Profile 编写门槛。
- 使用历史成功配置辅助生成。
- 在保存和激活前加入人工确认。
- 将 Copilot 限定在配置相关任务范围内。

但文档也存在几个需要修正的点：

| 问题 | 风险 | 建议 |
| --- | --- | --- |
| 直接以 LangGraph 作为第一版核心 | 引入状态持久化、恢复、人审中断等复杂度，开发和测试成本较高 | 第一版用普通服务状态机实现，第二阶段再引入 LangGraph |
| RAG 只索引 `description` | 很多 Profile 的核心差异在 prompt、类别、示例中，召回质量不足 | 索引 `description`、`extraction_prompt`、`category_colors`、`examples` 摘要 |
| “直接调用 CRUD API”描述过泛 | 可能绕开现有 StorageProvider、版本备份、Redis 当前状态 | 后端优先复用 `ProfileManager`，前端复用现有 Profile API/Store |
| 意图拦截过度依赖 LLM | LLM 拒绝不是安全边界 | 工具层只暴露 Profile 草稿、保存、激活能力，不提供删除、系统命令、文件访问 |
| Python 版本描述为 3.10+ | 当前 `pyproject.toml` 要求 `>=3.13` | 文档和依赖策略应以项目实际配置为准 |

## 3. 推荐目标

Config Copilot 第一版应满足以下目标：

1. 用户可以用自然语言描述目标文档类型和高亮需求。
2. Copilot 能基于现有 Profile 生成一个 YAML 草稿。
3. Copilot 能多轮修改草稿，例如调整类别、颜色、OCR 开关、提示词和 few-shot 示例。
4. 后端必须对草稿执行 YAML 解析和 `FullPipelineConfig.from_dict()` 校验。
5. 前端必须展示草稿，允许用户审查后再应用到编辑器。
6. 保存和激活必须沿用现有 Profile 保存/激活链路。
7. 所有副作用操作必须由用户显式点击确认。

第一版不要求：

- 完整 LangGraph 编排。
- Chroma 向量库持久化。
- 自动删除或覆盖已有 Profile。
- 自动访问 PDF 原文。
- 自动执行系统命令或修改项目文件。

## 4. 推荐架构

### 4.1 后端模块

建议新增目录：

```text
services/copilot/
├── __init__.py
├── service.py              # CopilotService，对外编排入口
├── session_store.py        # 会话状态存储
├── profile_context.py      # 从 ProfileManager 读取历史配置上下文
├── draft_generator.py      # LLM 草稿生成和修改
├── draft_validator.py      # YAML + FullPipelineConfig 校验
├── guardrails.py           # 意图和工具边界控制
└── schemas.py              # 请求/响应 DTO
```

核心职责：

| 模块 | 职责 |
| --- | --- |
| `CopilotService` | 串联意图判断、上下文召回、草稿生成、校验、保存准备 |
| `ProfileContextProvider` | 通过 `ProfileManager` 获取历史 Profile，不直接读写本地文件 |
| `DraftGenerator` | 调用 LLM，输出结构化草稿和解释 |
| `DraftValidator` | 执行 `yaml.safe_load()` 和 `FullPipelineConfig.from_dict()` |
| `CopilotSessionStore` | 保存会话消息、当前草稿、待确认动作 |
| `Guardrails` | 限制 Copilot 只处理 Profile 配置任务 |

### 4.2 API 设计

建议新增接口前缀：

```text
/api/v1/profile-copilot
```

建议接口：

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `POST` | `/sessions` | 创建 Copilot 会话 |
| `GET` | `/sessions/{session_id}` | 获取会话状态 |
| `POST` | `/sessions/{session_id}/messages` | 发送用户消息，返回草稿和解释 |
| `POST` | `/sessions/{session_id}/validate` | 校验当前草稿 |
| `POST` | `/sessions/{session_id}/save` | 用户确认后保存为 Profile |
| `POST` | `/sessions/{session_id}/activate` | 用户确认后激活已保存 Profile |

保存和激活接口内部应调用：

```python
get_profile_manager().create_profile(...)
get_profile_manager().update_profile(...)
get_profile_manager().activate_profile(...)
```

不要直接写入 `services/profiles/*.yaml`。

### 4.3 前端集成

当前 `web-pc/src/views/ConfigView.vue` 已经是 Profile 编辑页，Copilot 应集成在这个页面，而不是另起一套独立配置系统。

建议新增：

```text
web-pc/src/api/profileCopilotApi.ts
web-pc/src/stores/profileCopilotStore.ts
web-pc/src/components/config/ProfileCopilotPanel.vue
```

交互建议：

1. 用户在 Copilot 面板中输入需求。
2. 后端返回 YAML 草稿、解释、校验结果和参考 Profile。
3. 前端显示草稿 diff 或完整 YAML。
4. 用户点击“应用到编辑器”后，写入现有 `profileStore.draftContent`。
5. 用户仍通过现有“保存”或“保存并激活”按钮完成落地。

这样可以最大程度复用现有编辑器、保存逻辑、状态提示和错误处理。

## 5. RAG 策略

### 5.1 第一版：轻量召回

第一版建议不引入 Chroma。原因是当前 Profile 数量通常有限，简单召回足够支撑体验。

可从每个 Profile 中提取以下字段组成检索文本：

```text
display_name
description
extraction_prompt 摘要
category_colors.name
category_colors.description
examples.extractions.class
examples.text 摘要
```

召回方式可以先采用：

- 关键词命中。
- 简单分词评分。
- 类别名称匹配。
- description 权重加成。

### 5.2 第二版：向量召回

当 Profile 数量增多或召回质量不足时，再引入：

- Ollama `nomic-embed-text` 生成 embedding。
- Chroma 做本地持久化向量库。

索引对象不应只包含 `description`，而应包含 Profile 的业务摘要。

推荐 metadata：

```json
{
  "profile_id": "...",
  "filename": "...",
  "display_name": "...",
  "updated_at": "...",
  "category_names": ["company_name", "market_share"]
}
```

完整 YAML 可以作为 metadata 或通过 `profile_id` 回查 `ProfileManager`，更推荐后者，避免向量库和主存储之间出现数据不一致。

## 6. LLM 生成策略

不建议让 LLM 直接自由输出最终 YAML 并保存。建议采用分层生成：

```text
用户需求
-> 召回参考 Profile
-> 生成 DraftPlan
-> 合成 YAML
-> YAML 解析
-> FullPipelineConfig 校验
-> 返回草稿和解释
```

`DraftPlan` 可以包含：

```json
{
  "profile_name": "finance-report",
  "description": "...",
  "entities": [
    {
      "name": "company_name",
      "description": "公司名称",
      "color": "#2ecc71"
    }
  ],
  "mineru_options": {
    "enable_ocr": true,
    "enable_table": true,
    "language": "ch"
  },
  "prompt_strategy": "...",
  "examples": []
}
```

后端根据 `DraftPlan` 生成 YAML，可以降低 YAML 结构漂移和字段错误。

## 7. 安全边界

Config Copilot 必须遵守以下边界：

1. 只处理 Profile 配置相关请求。
2. 不提供删除 Profile 的工具。
3. 不提供文件系统读写工具。
4. 不提供系统命令执行工具。
5. 不读取用户上传 PDF 原文，除非后续需求明确授权。
6. 不自动保存、覆盖或激活配置。
7. 保存和激活必须由用户显式确认。
8. 所有 LLM 生成内容必须经过 YAML 和业务配置校验。

LLM 拒绝话术只能作为体验补充，真正的安全边界应由工具白名单和服务端校验保证。

## 8. 分阶段实施计划

### 阶段 1：Profile 草稿 Copilot

目标：先做可用闭环。

后端：

- 新增 `services/copilot/` 模块。
- 新增 Copilot session API。
- 使用现有 ProfileManager 做历史 Profile 读取。
- 使用现有 DeepSeek/OpenAI-compatible 配置生成草稿。
- 用 `FullPipelineConfig.from_dict()` 校验草稿。

前端：

- 在 Config 页面新增 Copilot 面板。
- 支持发送需求、查看回复、应用草稿到 YAML 编辑器。
- 保存和激活继续使用现有按钮。

验证：

- 单元测试覆盖草稿校验、越界请求拒绝、ProfileManager 调用。
- 手工验证生成、修改、应用、保存、激活流程。

### 阶段 2：RAG 增强

目标：提升历史 Profile 复用质量。

- 新增 Profile 摘要提取器。
- 新增可选 Chroma/Ollama embedding 支持。
- Profile 创建/更新后同步索引。
- 检索结果返回引用来源和匹配原因。

### 阶段 3：LangGraph 编排

目标：当流程复杂度提升后再引入图编排。

适合引入 LangGraph 的场景：

- 需要可恢复的人审中断。
- 需要多步骤自动修复校验错误。
- 需要更复杂的工具调用分支。
- 需要持久化对话状态和审计轨迹。

LangGraph 应使用 checkpoint 支撑 human-in-the-loop，不建议只用内存状态。

## 9. 推荐 OpenSpec 范围

这是新功能，正式开发前应创建 OpenSpec change。

建议 change 名称：

```text
profile-config-copilot
```

建议影响范围：

```text
services/copilot/
services/api/server.py
web-pc/src/api/profileCopilotApi.ts
web-pc/src/stores/profileCopilotStore.ts
web-pc/src/components/config/ProfileCopilotPanel.vue
web-pc/src/views/ConfigView.vue
services/examples 或 services/tests 中的相关测试
```

第一版 OpenSpec 不建议包含 Chroma、Ollama、LangGraph。它们可以作为后续 change 独立推进。

## 10. 最小可行版本验收标准

MVP 完成时应满足：

1. 用户能从 Config 页面打开 Copilot 面板。
2. 用户输入“我要一个财务报告高亮配置”后，系统能返回可解析 YAML 草稿。
3. 草稿能通过 `FullPipelineConfig.from_dict()` 校验。
4. 用户能将草稿应用到现有 YAML 编辑器。
5. 用户能用现有保存按钮保存为新 Profile。
6. 用户能用现有保存并激活按钮激活配置。
7. 越界请求不会触发保存、激活或系统级操作。
8. 后端测试覆盖核心服务和校验逻辑。

## 11. 最终建议

推荐实施顺序：

```text
OpenSpec 提案
-> Profile 草稿 Copilot MVP
-> 前端 ConfigView 集成
-> 质量验证
-> RAG 增强
-> LangGraph 编排增强
```

这个顺序可以尽快交付真实价值，同时避免第一版引入过多不必要的基础设施复杂度。
