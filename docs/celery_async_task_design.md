# LangExtract 异步进度方案设计

## 背景

当前 `LangExtract` 是**同步阻塞调用**，调用大模型（约1-3分钟）期间前端进度条卡死，无法提供实时进度反馈。本文档提供基于 **Celery + Redis + WebSocket** 的异步进度解决方案。

---

## 架构设计

```
┌─────────────┐     POST /api/v1/tasks      ┌─────────────┐
│             │ ───────────────────────────▶ │             │
│   前端页面   │                              │  FastAPI    │
│  (WebSocket)│                              │   主服务     │
│             │ ◀─────────────────────────── │             │
└──────┬──────┘     返回 task_id              └──────┬──────┘
       │                                            │
       │ WebSocket /ws/{task_id}                    │ 提交Celery任务
       │                                            ▼
       │                                    ┌─────────────┐
       │                                    │   Redis     │
       │                                    │  (Broker)   │
       │                                    └──────┬──────┘
       │                                           │
       │                                    ┌──────▼──────┐
       │                                    │ Celery Worker│
       │                                    │             │
       │                                    │ ┌─────────┐ │
       │                                    │ │LangExtract│ │
       │                                    │ │ 提取任务 │ │
       │                                    │ └────┬────┘ │
       │                                    │      │      │
       │                                    │ 更新进度    │
       │                                    │      │      │
       │                                    └──────┼──────┘
       │                                           │
       │              进度消息                      │
       │◀──────────────────────────────────────────┘
       │         (Redis Pub/Sub + WebSocket)
```

---

## 核心组件

### 1. 消息队列 (Redis)

**作用**: 
- Celery 任务队列 (Broker)
- 任务状态存储 (Backend)
- 进度消息发布订阅 (Pub/Sub)

**配置**:
```python
# celery_config.py
redis_url = "redis://localhost:6379/0"

# Broker (任务队列)
broker_url = redis_url

# Backend (结果存储)
result_backend = redis_url
```

**进度存储结构**:
```
# Redis Key 设计
task:{task_id}:progress  →  JSON {"stage": "extraction", "progress": 45, ...}
task:{task_id}:status    →  "PENDING" / "PROGRESS" / "SUCCESS" / "FAILURE"
task:{task_id}:result    →  任务结果JSON
```

---

### 2. 异步任务引擎 (Celery)

**作用**: 
- 异步执行 LangExtract 提取
- 支持任务并发和重试
- 进度更新机制

**任务状态流转**:
```
PENDING → STARTED → PROGRESS → SUCCESS/FAILURE
           ↓
      实时更新进度到Redis
```

**进度更新方式**:

#### 方式1: 自定义状态 (推荐)
```python
@app.task(bind=True)
def extract_entities_task(self, md_content, config):
    """LangExtract 异步提取任务"""
    
    # 1. 准备阶段 (10%)
    self.update_state(
        state='PROGRESS',
        meta={'stage': 'preparation', 'progress': 10, 'message': '准备提取配置...'}
    )
    
    # 2. 调用大模型 (10% → 60%)
    # LangExtract 是阻塞调用，这里发送"进行中"状态
    self.update_state(
        state='PROGRESS',
        meta={'stage': 'llm_calling', 'progress': 30, 'message': '调用大模型分析（约需1-3分钟）...'}
    )
    
    # 执行 LangExtract (阻塞)
    result = langextract.extract(
        text_or_documents=md_content,
        prompt_description=config.prompt,
        examples=config.examples,
        model_id=config.model_id
    )
    
    # 3. 解析结果 (60% → 90%)
    self.update_state(
        state='PROGRESS',
        meta={'stage': 'parsing', 'progress': 75, 'message': '解析实体结果...'}
    )
    
    # 4. 完成 (100%)
    self.update_state(
        state='PROGRESS',
        meta={'stage': 'completed', 'progress': 100, 'message': '提取完成'}
    )
    
    return {
        'extraction_count': len(result.extractions),
        'extractions': [...],
        'highlight_count': ...
    }
```

#### 方式2: Redis Pub/Sub (实时推送)
```python
import redis
import json

redis_client = redis.Redis()

def publish_progress(task_id, stage, progress, message):
    """发布进度消息到 Redis Pub/Sub"""
    channel = f"task:{task_id}:progress"
    data = json.dumps({
        'stage': stage,
        'progress': progress,
        'message': message,
        'timestamp': time.time()
    })
    redis_client.publish(channel, data)

@app.task
def extract_with_realtime_progress(task_id, md_content, config):
    # 在进入 LangExtract 前发送进度
    publish_progress(task_id, 'extraction', 10, '开始调用大模型...')
    
    # 执行提取 (阻塞)
    result = langextract.extract(...)
    
    # 完成后发送进度
    publish_progress(task_id, 'extraction', 100, '提取完成')
    
    return result
```

---

### 3. WebSocket 进度推送

**作用**: 
- 将 Celery 任务进度实时推送到前端
- 支持长连接，减少轮询开销

**架构**:
```
Celery Worker ──Redis Pub/Sub──▶ FastAPI WebSocket ──▶ 前端
```

**实现方案**:

```python
# api_server.py

import asyncio
import json
import redis.asyncio as aioredis
from fastapi import WebSocket

# Redis 订阅连接
redis_pubsub = None

async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()
    
    # 1. 检查任务状态
    task = task_manager.get_task(task_id)
    if not task:
        await websocket.send_json({"error": "任务不存在"})
        return
    
    # 2. 启动 Redis 订阅监听
    redis_client = aioredis.Redis()
    pubsub = redis_client.pubsub()
    
    # 订阅任务进度频道
    channel = f"task:{task_id}:progress"
    await pubsub.subscribe(channel)
    
    # 3. 创建监听任务
    listen_task = asyncio.create_task(
        listen_progress(pubsub, websocket, task_id)
    )
    
    try:
        # 4. 发送当前状态
        await websocket.send_json({
            "type": "connected",
            "data": task
        })
        
        # 5. 保持连接，处理心跳
        while True:
            data = await asyncio.wait_for(
                websocket.receive_text(), 
                timeout=30
            )
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        listen_task.cancel()
        await pubsub.unsubscribe(channel)

async def listen_progress(pubsub, websocket: WebSocket, task_id: str):
    """监听 Redis Pub/Sub 并推送到 WebSocket"""
    async for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            await websocket.send_json({
                "type": "progress",
                "data": {
                    "task_id": task_id,
                    "progress": data
                }
            })
```

---

## 实施步骤

### Phase 1: 基础环境搭建 (1天)

1. **安装依赖**
```bash
pip install celery[redis] redis
```

2. **启动 Redis**
```bash
# Windows (WSL 或 Docker)
docker run -d -p 6379:6379 redis:latest

# 或本地安装
redis-server
```

3. **配置 Celery**
```python
# celery_config.py 更新
broker_url = "redis://localhost:6379/0"
result_backend = "redis://localhost:6379/0"
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
```

### Phase 2: 异步任务重构 (2天)

1. **创建新的异步任务**
```python
# celery_tasks.py 新增

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
import langextract

@shared_task(bind=True, max_retries=3, soft_time_limit=300)
def process_pdf_async(self, task_id: str, url: str, config: dict):
    """
    异步 PDF 处理任务
    
    流程:
    1. MinerU 解析 (同步，有进度回调)
    2. LangExtract 提取 (异步包装)
    3. 高亮渲染
    """
    try:
        # ========== MinerU 解析阶段 ==========
        update_task_progress(task_id, 'mineru', 0, '开始解析...')
        
        # ... MinerU 解析代码 ...
        
        update_task_progress(task_id, 'mineru', 100, '解析完成')
        
        # ========== LangExtract 阶段 ==========
        update_task_progress(task_id, 'extraction', 10, '准备提取...')
        
        # 执行提取 (阻塞但包装在异步任务中)
        result = langextract.extract(...)
        
        update_task_progress(task_id, 'extraction', 100, '提取完成')
        
        # ========== 高亮渲染阶段 ==========
        update_task_progress(task_id, 'highlight', 0, '开始渲染...')
        
        # ... 渲染代码 ...
        
        update_task_progress(task_id, 'highlight', 100, '渲染完成')
        
        return {'status': 'success', 'result': result}
        
    except SoftTimeLimitExceeded:
        self.retry(countdown=60)
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
```

2. **更新 API 层**
```python
# api_server.py

from celery_tasks import process_pdf_async

@app.post("/api/v1/tasks")
async def submit_task(request: SubmitTaskRequest):
    """提交异步任务"""
    task_id = str(uuid.uuid4())
    
    # 创建任务记录
    task_manager.create_task(task_id, str(request.document_url))
    
    # 提交 Celery 任务 (异步执行)
    celery_task = process_pdf_async.delay(
        task_id=task_id,
        url=str(request.document_url),
        config=request.dict()
    )
    
    # 保存 Celery 任务 ID 映射
    task_manager.update_task(
        task_id,
        celery_task_id=celery_task.id,
        status='processing'
    )
    
    return TaskResponse(
        task_id=task_id,
        status="processing",
        message="任务已提交，正在处理中"
    )
```

### Phase 3: WebSocket 实时推送 (1天)

1. **实现 Redis Pub/Sub 监听**
2. **更新 WebSocket 端点**
3. **前端适配**

```javascript
// 前端连接 WebSocket
const ws = new WebSocket(`ws://localhost:8000/ws/${task_id}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'progress') {
        // 实时更新进度
        const { stage, progress, message } = data.data.progress;
        updateProgress(stage, progress, message);
    }
};
```

### Phase 4: 测试与优化 (1天)

1. **并发测试**
```bash
celery -A celery_tasks worker --loglevel=info --concurrency=4
```

2. **监控与日志**
- Flower (Celery 监控): `pip install flower`
- 启动: `celery -A celery_tasks flower --port=5555`

---

## 预期效果

### 当前问题
```
实体提取: [████░░░░░░] 卡死3分钟无反馈
```

### 优化后
```
实体提取: [█░░░░░░░░░] 10%  准备提取配置...
实体提取: [██░░░░░░░░] 20%  调用大模型分析（约需1-3分钟）...
实体提取: [██░░░░░░░░] 20%  调用大模型分析（约需1-3分钟）...
实体提取: [██░░░░░░░░] 20%  调用大模型分析（约需1-3分钟）...（等待中）
实体提取: [██████░░░░] 60%  大模型返回，解析结果...
实体提取: [████████░░] 80%  实体对齐验证...
实体提取: [██████████] 100% 提取完成，共22个实体
```

---

## 风险与应对

| 风险 | 可能性 | 应对方案 |
|------|--------|----------|
| Redis 单点故障 | 中 | 使用 Redis Sentinel 或集群 |
| Celery Worker 崩溃 | 低 | 配置任务重试机制 (max_retries=3) |
| LangExtract 超时 | 高 | 设置 soft_time_limit=300s，超时自动重试 |
| 内存占用过高 | 中 | 限制并发数 (concurrency=4)，使用流式处理 |

---

## 参考资料

1. [Celery 官方文档](https://docs.celeryq.dev/)
2. [Redis Pub/Sub 文档](https://redis.io/docs/manual/pubsub/)
3. [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
4. [Celery Progress Bars with FastAPI](https://celery.school/celery-progress-bars-with-fastapi-htmx)

---

## 工作量评估

| 阶段 | 工作量 | 说明 |
|------|--------|------|
| 基础环境搭建 | 0.5天 | Redis + Celery 配置 |
| 异步任务重构 | 2天 | 核心开发工作 |
| WebSocket 推送 | 1天 | 实时进度 |
| 测试与优化 | 0.5天 | 并发测试、监控 |
| **总计** | **4天** | |

---

## 下一步行动

1. **确认方案**: 团队评审技术方案
2. **环境准备**: 部署 Redis 服务
3. **逐步实施**: 按 Phase 1→4 推进
4. **监控验证**: 上线后观察任务执行情况

---

**文档版本**: 1.0  
**创建日期**: 2026-03-03  
**作者**: AI Assistant  
**关联任务**: fusion-mark-csy
