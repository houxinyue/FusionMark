# Celery Chain Pipeline - 全异步工作流架构

将 MinerU → LangExtract → 高亮渲染 全流程改造为 Celery Chain，实现步骤级失败重试和独立进度追踪。

## 目录结构

```
celery_chain_pipeline/
├── __init__.py              # 包初始化
├── celery_config.py         # Celery 应用配置
├── celery_tasks.py          # 三个步骤任务定义
├── progress_manager.py      # 统一进度管理器
├── websocket_handler.py     # WebSocket 进度推送
├── api_server.py            # FastAPI 服务
└── README.md                # 本文档
```

## 核心特性

- **步骤独立**: MinerU/实体提取/高亮渲染 各自为独立 Celery 任务
- **失败重试**: 单步骤失败只重试该步骤，不用从头开始
- **实时进度**: 每个步骤独立进度，通过 WebSocket 实时推送
- **水平扩展**: 支持多 Worker 并发处理

## 启动命令

### 1. 启动 Redis (如未启动)
```bash
redis-server
```

### 2. 启动 Celery Worker
```bash
# 启动所有队列的 Worker
celery -A celery_chain_pipeline.celery_config worker -l info

# 或启动指定队列的 Worker (推荐)
celery -A celery_chain_pipeline.celery_config worker -l info -Q mineru,extraction,highlight

# Windows 下使用 solo pool
celery -A celery_chain_pipeline.celery_config worker -l info -Q mineru,extraction,highlight --pool=solo
```

### 3. 启动 API 服务
```bash
# 开发模式
uvicorn celery_chain_pipeline.api_server:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn celery_chain_pipeline.api_server:app --host 0.0.0.0 --port 8000
```

### 4. (可选) 启动 Flower 监控
```bash
celery -A celery_chain_pipeline.celery_config flower --port=5555
# 访问 http://localhost:5555
```

## API 接口

### 提交任务
```bash
POST /api/v1/tasks
{
    "document_url": "https://example.com/doc.pdf",
    "enable_ocr": true,
    "enable_formula": true
}
```

### 查询状态
```bash
GET /api/v1/tasks/{task_id}
```

### WebSocket 进度
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${task_id}`);
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data);  // { type: "progress", stage: "mineru", progress: 50, ... }
};
```

### 下载结果
```bash
GET /api/v1/tasks/{task_id}/download
```

## Redis Key 结构

| Key | 用途 | 类型 |
|-----|------|------|
| `task:{id}:progress` | 任务总体进度 | Hash |
| `task:{id}:steps` | 各步骤详细状态 | Hash |
| `task:{id}:updates` | Pub/Sub 实时更新 | Channel |
| `celery-task-meta-{id}` | Celery 任务元数据 | String |

## 进度权重

| 步骤 | 权重 | 进度范围 |
|------|------|----------|
| MinerU 解析 | 40% | 0-40% |
| 实体提取 | 30% | 40-70% |
| 高亮渲染 | 30% | 70-100% |

## 环境变量

```env
REDIS_URL=redis://localhost:6379/0
MINERU_API_KEY=your_mineru_key
```

## 与旧版对比

| 特性 | 旧版 | Celery Chain |
|------|------|--------------|
| MinerU 进度 | ✅ 实时 | ✅ 实时 + 可重试 |
| LangExtract 进度 | ❌ 卡住无反馈 | ✅ 状态更新 |
| 单步骤失败 | ❌ 全部重来 | ✅ 仅重试该步骤 |
| 并发处理 | ❌ 阻塞 | ✅ Worker 并发 |
| 水平扩展 | ❌ 单机 | ✅ 多 Worker |
