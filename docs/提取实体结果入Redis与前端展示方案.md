# 提取实体结果入 Redis 与前端展示方案

## 背景

当前系统在 LangExtract 提取完成后，会导出调试产物：

- `extractions.jsonl`
- LangExtract 官方 HTML 可视化

这些产物对排查和离线分析有价值，但当前前端“提取实体”区域并不能直接消费这些结果。页面上现在主要展示的是：

- 分类计数
- 少量演示占位信息

这导致用户无法直接在主界面中看到本次任务究竟提取了哪些实体文本。

## 目标

在保持现有 JSONL 文件导出能力不变的前提下，将 LangExtract 提取结果同时整理为：

- 结构化实体 JSON
- 可直接嵌入页面的 HTML 可视化片段

并一起写入 Redis 任务结果中。前端实体展示区域优先直接渲染 HTML，可在没有 HTML 时回退到 JSON 展示。

## 非目标

本次方案不包含：

1. 不把原始 JSONL 文本整体写入 Redis
2. 不修改 LangExtract 原始输出格式
3. 不引入新的数据库
4. 不实现实体点击定位到 PDF 高亮位置

## 当前问题

### 1. JSONL 文件适合调试，不适合前端直接消费

JSONL 是文件型调试产物，适合：

- 本地留档
- 离线分析
- 复盘提取结果

但不适合前端页面直接使用，因为：

- 它是文本文件，不是前端可直接渲染的数据结构
- 每次展示都需要额外解析
- Redis 中如果直接保存整段 JSONL，读写与维护都不方便

### 2. 前端实体展示缺少真实提取结果

当前前端“提取实体”区域更接近摘要信息，而不是本次任务的真实实体列表。这会导致：

- 用户不知道模型实际抽取了什么
- 无法快速判断提取是否正确
- 页面价值被压缩成“计数展示”

## 核心方案

### 总体思路

继续保留 JSONL 文件导出作为调试产物，同时新增两份适合前端消费的内容并写入 Redis：

- 结构化实体 JSON：用于统计、回退展示、后续交互扩展
- LangExtract HTML：用于前端直接渲染，快速获得接近官方可视化的展示效果

也就是说：

- 文件系统保留：`extractions.jsonl`
- Redis 保留：`entities` + `langextract_html`

## 为什么不直接把 JSONL 存 Redis

不建议把 JSONL 原文整块存入 Redis，原因如下：

1. 前端最终需要的是结构化对象，不是文件内容
2. Redis 更适合存 JSON 结构，不适合承担文件存储职责
3. 后续查询、筛选、展示都需要再次解析 JSONL，前端复杂度反而上升

因此更合理的做法是：

- JSONL 继续作为磁盘调试产物
- Redis 存解析后的轻量实体数组与可直接显示的 HTML

## Redis 中建议保存的数据结构

当前任务完成后写入 Redis 的 `result` 建议扩展为：

```json
{
  "task_id": "xxx",
  "mineru_task_id": "xxx",
  "output_path": "highlight_output/result.pdf",
  "md_length": 12345,
  "extraction_count": 19,
  "highlight_count": 19,
  "category_counts": {
    "company_name": 5,
    "shipment_value": 5
  },
  "langextract_html": "<div class='...'>...</div>",
  "entities": [
    {
      "text": "Apple",
      "category": "company_name",
      "char_start": 120,
      "char_end": 125
    },
    {
      "text": "81.3",
      "category": "shipment_value",
      "char_start": 240,
      "char_end": 244
    }
  ]
}
```

## 实体对象字段建议

每个实体建议至少包含：

- `text`
- `category`
- `char_start`
- `char_end`

可选字段：

- `document_id`
- `confidence`（若后续上游支持）
- `page`（若未来做页级定位）

### 推荐最小结构

```json
{
  "text": "Apple",
  "category": "company_name",
  "char_start": 120,
  "char_end": 125
}
```

这样既足够前端展示，也为后续定位能力预留扩展空间。

## HTML 存储建议

### 存什么

建议存 LangExtract 官方可视化的主体内容，来源于当前已有的：

- `visualize(result)`

### 存储原则

1. 可以先直接存完整 HTML 字符串，优先满足快速展示
2. 后续若发现样式冲突或体积问题，再收敛为片段或独立容器内容
3. 该 HTML 来源于后端生成，初步可视为可信内容

### 为什么 HTML 也要存 Redis

因为前端当前最直接的诉求不是复杂交互，而是：

- 快速展示提取结果
- 尽量复用 LangExtract 自带可视化
- 减少前端自己重写渲染规则的成本

因此初步方案中，HTML 是展示主路径，JSON 是数据主路径。

## 后端改动方案

## 改动位置

主要涉及：

- `services/core/highlight.py`
- `services/api/task_processor.py`

### 1. 在高亮服务中提取结构化实体

在 LangExtract 返回结果后，当前系统已经会：

- 读取 `result.extractions`
- 转换成 `HighlightEntity`
- 导出 JSONL / HTML

在这一阶段可以新增一个转换函数，将提取结果整理成前端可消费结构：

```python
[
  {
    "text": ext.extraction_text,
    "category": ext.extraction_class,
    "char_start": ext.char_interval.start_pos if ext.char_interval else None,
    "char_end": ext.char_interval.end_pos if ext.char_interval else None,
  }
]
```

### 2. 同时生成前端展示用 HTML

当前系统已经会导出官方 HTML 可视化。建议在同一阶段直接获得 HTML 字符串，并放入返回结果中，例如：

- `details["langextract_html"]`

### 3. 把结构化实体与 HTML 放入 `ServiceResult.details`

当前 `ServiceResult.details` 已用于返回附加信息，建议将实体列表放入：

- `details["entities"]`
- `details["category_counts"]`
- `details["langextract_html"]`

### 4. 在任务处理器写入 Redis 最终结果时透传

在 `services/api/task_processor.py` 写入 `result_data` 时，将实体列表与 HTML 一并加入结果对象：

```python
result_data = {
    ...,
    "category_counts": category_counts,
    "entities": entities,
    "langextract_html": langextract_html
}
```

## 前端改动方案

## 改动位置

主要涉及：

- `frontend/src/app.js`

### 1. 优先读取 `result.langextract_html`

当前前端实体区域建议调整为：

1. 如果 `result.langextract_html` 存在
   - 直接渲染 HTML
2. 如果没有 HTML，但存在 `result.entities`
   - 渲染真实实体列表
3. 如果只有 `category_counts`
   - 降级展示分类统计

### 2. 展示形式建议

优先展示 LangExtract 官方 HTML 可视化。

如果走 JSON 回退模式，则每个实体继续使用现有 tag 风格，但文案直接显示实体原文：

- `Apple`
- `Samsung`
- `81.3`
- `24.2%`

并按 `category` 着色。

### 3. 可选增强

如果后续实体过多，可增加：

- 按类别分组
- 限制首屏展示数量
- “展开更多”按钮

但本次先以最小可用为主，不做复杂分页。

## 与 JSONL 导出的关系

本方案不替代 JSONL 导出，只是补充前端展示数据。

### 仍然保留

- `extractions.jsonl`
- LangExtract 官方 HTML 可视化

### 新增

- Redis 任务结果中的 `entities`
- Redis 任务结果中的 `langextract_html`

也就是说：

- JSONL 负责“调试和留档”
- Redis `langextract_html` 负责“页面快速展示”
- Redis `entities` 负责“结构化数据、回退展示和后续扩展”

## 数据量与性能考虑

一般单个任务的实体量不会太大，通常几十到几百个以内，直接写入 Redis 任务结果是可接受的。

需要注意：

1. 不要写入完整 Markdown 原文到 `entities`
2. 不要把 JSONL 文件全文复制进 Redis
3. HTML 建议仅保存展示所需内容，不叠加无关上下文
4. 只保存前端需要的轻量字段

如果后续实体量明显增大，可再拆分为：

- `result_summary`
- `task_entities`

当前阶段无需提前复杂化。

## 后续扩展

本方案完成后，后续可以继续演进：

1. 支持实体点击后在 PDF 高亮层中联动定位
2. 支持历史任务查看实体列表
3. 支持 Redis 中单独维护 `task:{id}:entities`
4. 支持按类别过滤实体
5. 对 `langextract_html` 做样式隔离或 iframe 化

## 实施顺序建议

1. 在 `highlight.py` 中新增提取结果到结构化实体列表的转换
2. 在 `highlight.py` 中获取 LangExtract HTML 字符串
3. 将 `entities` 和 `langextract_html` 放入 `ServiceResult.details`
4. 在 `task_processor.py` 中把两者写入 Redis `result`
5. 前端优先读取 `result.langextract_html`
6. 若没有 HTML，则回退到 `entities`
7. 若没有 `entities`，则回退到 `category_counts`
8. 使用真实任务验证前端展示结果

## 验收标准

1. 任务完成后，Redis 中的 `result` 包含 `langextract_html` 与 `entities`
2. `entities` 中每项至少包含 `text` 与 `category`
3. 前端“提取实体”区域优先显示 LangExtract HTML
4. 现有 JSONL 导出能力不受影响
5. 若 HTML 缺失，前端仍能回退展示 `entities`
6. 若 `entities` 缺失，前端仍能回退展示分类计数

## 结论

建议采用“JSONL 继续存文件、Redis 同时存 HTML 与结构化实体”的双轨方案。

这样可以兼顾：

- 调试产物保留
- 前端快速展示
- 后续历史查询扩展
- 后续结构化交互扩展

相比“把 JSONL 原文直接存 Redis”，该方案更清晰、可维护性更高，也更符合前后端职责分离原则。相比“只存 HTML”，该方案又保留了后续继续打磨交互能力的空间。
