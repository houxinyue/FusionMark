# Local + MinIO 存储插件架构设计方案

## 背景

当前系统中，MinerU 与 LangExtract 相关产物主要写入项目本地目录，例如：

- MinerU 输出目录
- `full.md`
- `layout.json`
- `extractions.jsonl`
- LangExtract HTML 可视化
- 最终高亮 PDF

这种方式在本地开发阶段简单直接，但随着系统逐步进入稳定使用阶段，本地文件存储会带来一系列问题：

1. 服务重启、迁移、清理后，产物容易丢失
2. 多实例部署时，本地文件无法共享
3. 下载接口依赖本地路径，健壮性不足
4. Redis 中保存的是任务状态，但真正的重要产物仍散落在本地目录
5. 随时间积累，本地磁盘会持续膨胀，运维成本上升

为了提高系统健壮性，需要引入统一的存储抽象层，并支持通过环境变量在：

- 本地存储
- MinIO 对象存储

之间切换。

## 目标

设计一个统一的存储插件架构，使系统能够：

1. 默认支持本地存储（适合开发和调试）
2. 通过环境变量切换到 MinIO 对象存储
3. 让业务流程层不直接依赖本地路径或 MinIO SDK
4. 逐步将关键产物迁移到对象存储
5. Redis 只保留状态、摘要和对象引用，不承担大文件存储职责

## 非目标

本次方案不包含：

1. 一次性移除所有本地存储逻辑
2. 立即把所有中间文件全部迁移到对象存储
3. 引入新的数据库系统
4. 设计跨云厂商统一 SDK 适配层

## 核心思路

建立统一的存储抽象接口：

- `StorageProvider`

业务代码只依赖该接口，不直接调用：

- 本地路径拼接逻辑
- `open(..., 'wb')`
- MinIO SDK

这样可以把存储实现与业务流程解耦。

## 架构示意

```text
┌──────────────────────────────┐
│      业务流程层              │
│ task_processor               │
│ highlight service            │
│ mineru pipeline              │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       StorageProvider        │
│ save_text                    │
│ save_bytes                   │
│ upload_file                  │
│ get_download_url             │
│ exists                       │
│ delete                       │
└──────────────┬───────────────┘
               │
     ┌─────────┴─────────┐
     ▼                   ▼
┌──────────────┐   ┌──────────────┐
│ LocalStorage │   │ MinIOStorage │
│ Provider     │   │ Provider     │
└──────────────┘   └──────────────┘
```

## 配置方案

### 核心环境变量

```env
STORAGE_PROVIDER=local
```

可选值：

- `local`
- `minio`

### 本地存储配置

```env
LOCAL_STORAGE_ROOT=storage
```

### MinIO 配置

```env
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=fusion-mark
MINIO_SECURE=false
MINIO_REGION=
MINIO_PREFIX=tasks/
```

### 产物保存开关

建议通过环境变量控制不同阶段产物是否写入对象存储：

```env
STORE_MINERU_EXTRACTED=true
STORE_LANGEXTRACT_ARTIFACTS=true
STORE_LANGEXTRACT_VERBOSE_ARTIFACTS=false
STORE_HIGHLIGHT_ARTIFACTS=true
```

建议含义：

- `STORE_MINERU_EXTRACTED`
  - 是否保存 MinerU 解压后的结果目录
- `STORE_LANGEXTRACT_ARTIFACTS`
  - 是否保存 LangExtract 基础调试产物，例如 `extractions.jsonl`、`visualization.html`、`entities.json`
- `STORE_LANGEXTRACT_VERBOSE_ARTIFACTS`
  - 是否保存更详细的过程文件，例如 `request.json`、`response.json`
- `STORE_HIGHLIGHT_ARTIFACTS`
  - 是否保存高亮阶段生成的产物

## Provider 选择逻辑

建议通过工厂函数统一创建：

```python
provider = get_storage_provider()
```

根据 `STORAGE_PROVIDER` 环境变量返回：

- `LocalStorageProvider`
- `MinioStorageProvider`

这样业务层无需关心具体运行环境。

## 接口设计建议

统一抽象接口建议至少包含以下方法：

### 1. 保存文本

```python
save_text(key: str, text: str, content_type: str = "text/plain") -> StorageObject
```

适用：

- `full.md`
- HTML 可视化
- JSON 文本调试产物

### 2. 保存二进制

```python
save_bytes(key: str, data: bytes, content_type: str) -> StorageObject
```

适用：

- PDF
- 图片

### 3. 上传本地文件

```python
upload_file(key: str, local_path: str, content_type: str = None) -> StorageObject
```

适用：

- 当前已有本地生成文件流程
- 对象存储接入初期最实用

### 4. 获取下载地址

```python
get_download_url(key: str, expires_in: int = None) -> str
```

适用：

- 服务端返回签名地址
- 未来前端直接下载对象

### 5. 查询对象是否存在

```python
exists(key: str) -> bool
```

### 6. 删除对象

```python
delete(key: str) -> bool
```

## 返回对象建议

建议 provider 返回统一的对象元数据：

```python
{
  "key": "tasks/xxx/highlighted.pdf",
  "provider": "minio",
  "bucket": "fusion-mark",
  "content_type": "application/pdf",
  "size": 123456,
  "url": "...",
}
```

这样后续 Redis、下载接口、调试日志都更容易统一处理。

## 对象命名规范

建议对象命名不要只按“文件名”组织，而要按：

- 项目标识
- 环境
- 任务 ID
- 处理阶段
- 产物类型

分层组织。

推荐主结构：

```text
{project}/{env}/tasks/{biz_task_id}/{stage}/{relative_path_or_filename}
```

例如：

```text
fusion-mark/prod/tasks/8f3c.../mineru/...
fusion-mark/prod/tasks/8f3c.../langextract/...
fusion-mark/prod/tasks/8f3c.../highlight/...
```

### 分层语义

- `project`
  - 固定项目名前缀，例如 `fusion-mark`
- `env`
  - 运行环境，例如 `dev` / `test` / `prod`
- `biz_task_id`
  - 当前系统业务任务号，作为对象归档主目录
- `stage`
  - `mineru` / `langextract` / `highlight`

### MinerU 产物命名

结合当前项目现有 `mineru_output/` 的真实目录结构，建议不要对 MinerU 内部文件重新发明命名规则，而是尽量保留现有语义和相对路径。

当前本地产物大致包括：

- 任务目录
- `full.md`
- `layout.json`
- `content_list_v2.json`
- `{mineru_file_id}_origin.pdf`
- `{mineru_file_id}_content_list.json`
- `{mineru_file_id}_model.json`
- `images/`

因此建议对象命名为：

```text
fusion-mark/{env}/tasks/{biz_task_id}/mineru/extracted/full.md
fusion-mark/{env}/tasks/{biz_task_id}/mineru/extracted/layout.json
fusion-mark/{env}/tasks/{biz_task_id}/mineru/extracted/content_list_v2.json
fusion-mark/{env}/tasks/{biz_task_id}/mineru/extracted/{mineru_file_id}_origin.pdf
fusion-mark/{env}/tasks/{biz_task_id}/mineru/extracted/{mineru_file_id}_content_list.json
fusion-mark/{env}/tasks/{biz_task_id}/mineru/extracted/{mineru_file_id}_model.json
fusion-mark/{env}/tasks/{biz_task_id}/mineru/extracted/images/{image_name}
```

说明：

- `extracted/`
  - 保存解压后的完整结果
- `mineru_file_id`
  - 保留 MinerU 生成的原始文件名前缀，不额外重命名

这样做的好处是：

1. 与当前 `mineru_output` 结构一致，迁移成本最低
2. 后续排查时可直接按本地目录结构对照对象存储
3. 不需要对 MinerU 内部文件命名做额外转换
4. 避免同时保存 zip 与解压目录造成重复存储

### LangExtract 产物命名

建议独立归档：

```text
fusion-mark/{env}/tasks/{biz_task_id}/langextract/extractions.jsonl
fusion-mark/{env}/tasks/{biz_task_id}/langextract/visualization.html
fusion-mark/{env}/tasks/{biz_task_id}/langextract/entities.json
fusion-mark/{env}/tasks/{biz_task_id}/langextract/request.json
fusion-mark/{env}/tasks/{biz_task_id}/langextract/response.json
```

说明：

- `extractions.jsonl`
  - 官方 JSONL 导出
- `visualization.html`
  - 官方 HTML 可视化
- `entities.json`
  - 面向前端或 Redis 的结构化实体摘要
- `request.json` / `response.json`
  - 可选，保留请求与响应元数据

建议保存策略：

- 默认保存：
  - `extractions.jsonl`
  - `visualization.html`
  - `entities.json`
- 通过 `STORE_LANGEXTRACT_VERBOSE_ARTIFACTS` 决定是否保存：
  - `request.json`
  - `response.json`

### Highlight 产物命名

建议独立归档：

```text
fusion-mark/{env}/tasks/{biz_task_id}/highlight/highlighted.pdf
fusion-mark/{env}/tasks/{biz_task_id}/highlight/rendered.html
fusion-mark/{env}/tasks/{biz_task_id}/highlight/render-metadata.json
fusion-mark/{env}/tasks/{biz_task_id}/highlight/debug/{filename}
```

说明：

- `highlighted.pdf`
  - 最终高亮 PDF
- `rendered.html`
  - 你们自己的高亮 HTML 中间结果
- `render-metadata.json`
  - 渲染统计、耗时、类别分布等信息
- `debug/`
  - 其他调试辅助文件

### 推荐完整示例

假设：

- `env = prod`
- `biz_task_id = task-20260424-001`

则一组对象可以是：

```text
fusion-mark/prod/tasks/task-20260424-001/mineru/extracted/full.md
fusion-mark/prod/tasks/task-20260424-001/mineru/extracted/layout.json
fusion-mark/prod/tasks/task-20260424-001/mineru/extracted/images/img_001.png

fusion-mark/prod/tasks/task-20260424-001/langextract/extractions.jsonl
fusion-mark/prod/tasks/task-20260424-001/langextract/visualization.html
fusion-mark/prod/tasks/task-20260424-001/langextract/entities.json

fusion-mark/prod/tasks/task-20260424-001/highlight/highlighted.pdf
fusion-mark/prod/tasks/task-20260424-001/highlight/rendered.html
fusion-mark/prod/tasks/task-20260424-001/highlight/render-metadata.json
```

### 命名原则

建议统一遵守：

1. 不使用中文文件名
2. 文件名使用稳定语义名称，不在文件名中拼随机串
3. 归档主目录统一使用业务任务号 `biz_task_id`
4. MinerU 内部生成文件保留原始命名
5. 按阶段分层：`mineru / langextract / highlight`
6. 解压结果与调试结果分层：`extracted / debug`

## Redis 中建议保存的内容

Redis 不应保存大文件正文，而只应保存：

- 任务状态
- 统计信息
- 对象引用
- 少量前端直接消费的轻量数据

建议结果结构类似：

```json
{
  "task_id": "xxx",
  "output_path": "highlight_output/result.pdf",
  "pdf_object_key": "fusion-mark/prod/tasks/{biz_task_id}/highlight/highlighted.pdf",
  "md_object_key": "fusion-mark/prod/tasks/{biz_task_id}/mineru/extracted/full.md",
  "jsonl_object_key": "fusion-mark/prod/tasks/{biz_task_id}/langextract/extractions.jsonl",
  "langextract_html_object_key": "fusion-mark/prod/tasks/{biz_task_id}/langextract/visualization.html",
  "entities": [...],
  "langextract_html": "<html>...</html>"
}
```

其中：

- `entities`
- `langextract_html`

仍可以保留在 Redis 中，方便前端快速展示。

而大文件本体应交给对象存储。

## 推荐的迁移策略

不建议一次性重构所有文件路径逻辑，而应该采用“先抽象、后迁移”的方式。

### 第一阶段：接入统一存储层

先引入：

- `StorageProvider`
- `LocalStorageProvider`
- `MinioStorageProvider`

并让现有流程可以通过环境变量选择 provider。

### 第二阶段：先迁移关键产物

优先迁移：

- 最终高亮 PDF
- `extractions.jsonl`
- LangExtract HTML 可视化

这些文件对前端展示、下载和任务追溯价值最高。

### 第三阶段：迁移 MinerU 中间产物

进一步迁移：

- `full.md`
- `layout.json`
- 其他中间解析产物

### 第四阶段：下载接口完全对象化

到这一阶段，API 下载逻辑可改为：

- 通过 provider 获取对象
- 或生成签名 URL

减少对本地路径的依赖。

## 本地文件的角色

本地文件不必立即彻底移除，建议保留为：

- 临时工作目录
- 本地开发调试目录
- 对象上传前的中间缓存

也就是说：

1. 任务处理中先落本地临时文件
2. 成功后上传对象存储
3. Redis 记录对象引用
4. 上传成功后再决定是否清理本地文件

这种方式比“直接流式写 MinIO”更稳，更容易兼容现有代码结构。

## 下载接口建议

未来下载接口建议支持两种模式：

### 模式 1：服务端代理下载

优点：

- 前端不需要感知 MinIO
- 权限控制集中在服务端

缺点：

- 服务端承担带宽与转发压力

### 模式 2：返回签名 URL

优点：

- 服务端压力更小
- 对象存储直接提供下载

缺点：

- 权限和时效控制需要额外设计

建议第一阶段先使用：

- 服务端代理下载

等对象存储稳定后，再考虑签名 URL。

## 风险与注意事项

### 1. 上传失败处理

若对象上传失败，必须避免任务状态被误标记为完成。

建议：

- 上传失败则任务失败
- 或保留本地 fallback，并明确记录状态

### 2. 内容类型

上传对象时要写对 `content_type`，例如：

- `application/pdf`
- `text/markdown`
- `application/json`
- `text/html`

否则后续浏览器预览和下载行为可能异常。

### 3. Redis 与对象存储边界

不能把大文件正文和对象存储同时无限复制，否则会造成：

- Redis 膨胀
- 存储重复
- 维护复杂度上升

### 4. MinIO 凭证与配置管理

建议所有 MinIO 配置统一走环境变量，不写死在代码或配置文件中。

## 与项目风格的匹配

该方案非常符合当前项目偏好的：

- 插件式架构
- 配置驱动
- 可拆分升级
- 面向后续扩展的设计

尤其适合当前项目已有：

- Redis 状态层
- OpenSpec 规范驱动
- 渐进式替换本地流程的需求

## 推荐目录结构

建议新增存储模块：

```text
services/storage/
  __init__.py
  base.py
  factory.py
  local.py
  minio.py
```

职责划分：

- `base.py`：定义接口与统一返回模型
- `local.py`：本地实现
- `minio.py`：MinIO 实现
- `factory.py`：按环境变量返回 provider

## 结论

建议正式采用：

- 本地 + MinIO 双 provider
- 环境变量选择 provider
- 统一存储抽象接口
- Redis 只保存状态、摘要和对象引用
- 本地文件逐步退化为临时工作目录

这个方案兼顾了：

- 当前项目的开发便利性
- 生产环境的健壮性
- 后续多实例部署与历史追溯需求

相比直接把 MinIO 写死在业务代码里，这种插件化设计更稳、更清晰，也更适合后续长期维护。
