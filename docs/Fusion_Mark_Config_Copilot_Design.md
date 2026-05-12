# Fusion-Mark Config Copilot 方案设计文档

## 1. 项目概述
### 1.1 背景
Fusion-Mark 是一个智能 PDF 解析与高亮系统，其核心逻辑高度依赖于复杂的 YAML 配置文件（Profile）。手动编写这些文件门槛高、易出错。

### 1.2 目标
构建一个基于 LangGraph 的智能体（Agent），通过多轮自然语言交互引导用户生成、修改、保存并激活 YAML 配置，贯穿现有业务系统。

### 1.3 核心原则
- **专职化**：仅负责配置相关任务，严禁执行无关指令（无情拒绝）。
- **经验化**：引入 RAG（检索增强生成），利用历史成功配置辅助生成。
- **闭环化**：直接对接现有业务 CRUD 接口，实现配置的“即聊即用”。

---

## 2. 技术选型
| 组件 | 选型 | 说明 |
| :--- | :--- | :--- |
| **智能体框架** | LangGraph | 支持循环流转、状态持久化和人工介入（Human-in-the-loop） |
| **推理模型 (LLM)** | DeepSeek-Chat | 通过标准 OpenAI 格式调用，高性价比，逻辑推理能力强 |
| **向量化模型** | Ollama (nomic-embed-text) | 本地部署，保护隐私，零成本，专为 RAG 优化 |
| **向量数据库** | Chroma (Local Persistence) | 轻量级 Python 原生支持，支持元数据（Metadata）存储 |
| **开发语言** | Python 3.10+ | 核心生态对 AI 库支持最完善 |

---

## 3. 系统架构设计

### 3.1 逻辑架构
系统采用“意图拦截 + RAG 增强 + 状态机流转”的架构。

1. **意图拦截层**：作为守门员，识别混合指令并执行“一票否决”。
2. **知识检索层**：从本地向量库检索历史配置的 `description`。
3. **生成决策层**：结合用户需求、RAG 参考模板和 `SKILL.md` 规范生成草案。
4. **人工确认层**：在执行副作用操作（保存/激活）前挂起等待用户点击确认。
5. **系统工具层**：调用现有 CRUD API 完成落地。

### 3.2 状态定义 (State)
```python
class FusionMarkState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_config_draft: dict      # 当前正在打磨的配置草案
    retrieved_context: str          # RAG 检索到的参考资料
    is_authorized: bool             # 用户是否已确认保存/激活动作
    current_step: str               # 流程位置标识
```

---

## 4. 核心模块设计

### 4.1 RAG 检索策略
- **索引对象**：YAML 文件的 `description` 字段。
- **存储内容**：`description` 作为向量内容，完整的 YAML 文本存入 Metadata。
- **理由**：描述字段语义最集中，能有效过滤语法噪音，提高匹配精度。

### 4.2 边界防御 (Guardrails)
- **严格意图识别**：若输入包含“编写 Python 脚本”、“查询天气”等越界请求，Agent 直接回复固定拒绝话术并终止流程。
- **最小工具集**：Agent 仅感知 `save_config`, `get_config`, `update_config` 工具，不提供删除或系统底层访问权限。

### 4.3 LangGraph 节点设计
1. **`intent_gatekeeper`**：检查意图是否纯粹。
2. **`rag_retriever`**：根据 `description` 召回历史相似配置。
3. **`config_generator`**：DeepSeek 结合 RAG 结果输出 YAML 建议。
4. **`human_review_interrupt`**：中断流程，向用户展示对比效果并询问“是否激活”。
5. **`api_executor`**：用户确认后，调用 Tools 发起 HTTP 请求。

---

## 5. 业务流程图 (流程描述)
1. **启动**：用户描述需求（如“我要配一个财务报表的高亮”）。
2. **拦截**：判断是否包含非法指令。
3. **检索**：Ollama 向量化需求，Chroma 召回最接近的“财务类”历史 YAML。
4. **对话**：Agent 展示初步方案，询问类别颜色、OCR 开关。
5. **打磨**：多轮对话修正（如“利润改绿色”）。
6. **终判**：Agent 编译完整 YAML 并弹出【保存并激活】请求。
7. **落地**：调用后端接口，返回成功的 `config_id`。

---

## 6. 数据安全与隐私
- **向量化本地化**：所有 Embedding 计算在 Ollama 本地完成，不外发数据。
- **API 隔离**：DeepSeek 仅获取配置文本，不触及用户实际解析的 PDF 原始文件。

---

## 7. 部署建议
- **环境**：Docker 容器化部署后端服务。
- **存储**：挂载持久化卷（Persistent Volume）用于存放 ChromaDB 数据库文件。
- **配置**：环境变量管理 DeepSeek API Key 和后端 CRUD 服务地址。
