# 轻量化 Redis 进度架构设计

> **状态**: 设计中  
> **替代方案**: [Celery Chain 架构](./celery_full_pipeline_design.md) (已废弃)  
> **目标**: 简化架构，单一进程部署，进度可感知

---

## 1. 设计背景

### 1.1 为什么废弃 Celery Chain？

原 Celery Chain 架构（`celery_chain_pipeline/`）过于重量级：

| 问题 | 说明 |
|------|------|
| 架构复杂 | 需要 Redis + Celery Worker + FastAPI 三个组件 |
| 维护成本高 | Celery 配置、队列管理、Worker 监控 |
| 部署繁琐 | 需要启动多个进程，本地开发麻烦 |
| 过度设计 | 当前单机部署场景不需要分布式能力 |

### 1.2 新架构核心诉求

> **"回归业务本质，去掉繁琐的任务框架"**

- 保持流程：**MinerU 解析 → LangExtract 提取 → 高亮渲染**
- 接受简单逻辑：**失败即标记，用户手动重试**
- 核心改进：**进度实时可见，阻塞等待可感知**

---

## 2. 架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     客户端 (前端)                            │
│                      - 提交任务                              │
│                      - WebSocket 接收进度                     │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI 服务 (单一进程)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   POST /     │  │   GET /      │  │   WS /ws/        │  │
│  │   submit     │  │   status     │  │   {task_id}      │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                  │                    │            │
│         ▼                  ▼                    ▼            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           BackgroundTasks / asyncio Task              │   │
│  │   async def process_task():                          │   │
│  │       1. await mineru.parse() ──► Redis 进度更新      │   │
│  │       2. await lang_extract() ──► Redis 进度更新 ⭐   │   │
│  │       3. await highlight() ──► Redis 进度更新        │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                                                    │
│         │  写入进度                                          │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Redis 进度看板 (轻量级存储)                 │   │
│  │  ┌─────────────────┐  ┌──────────────────────────┐  │   │
│  │  │ Hash: status:*  │  │ PubSub: pubsub:*         │  │   │
│  │  │ - progress      │  │                          │  │   │
│  │  │ - state         │  │  实时推送进度变更         │  │   │
│  │  │ - message       │  │                          │  │   │
│  │  │ - result        │  │  WebSocket handler 订阅   │  │   │
│  │  └─────────────────┘  └──────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件说明

| 组件 | 作用 | 技术选型 |
|------|------|---------|
| **FastAPI** | HTTP 接口 + WebSocket + 后台任务执行 | FastAPI BackgroundTasks |
| **Redis Hash** | 任务状态持久化存储 | Redis HSET/HGETALL |
| **Redis PubSub** | 实时进度推送通道 | Redis PUBLISH/SUBSCRIBE |

---

## 3. 进度埋点设计

### 3.1 业务流程与进度映射

| 阶段 | 进度权重 | Redis 状态 | 用户看到的消息 | 说明 |
|------|---------|-----------|--------------|------|
| **任务初始化** | 5% | `pending` | "任务已接收，准备处理..." | 任务刚入队列 |
| **MinerU 解析** | 10% → 40% | `processing` | "正在解析 PDF 内容..." | 支持细粒度页码进度 |
| **LangExtract** | **40% → 45%** | `processing` | **"调用大模型提取实体（约需1-3分钟）..."** | ⭐ 阻塞前先发状态 |
| **LangExtract 内部** | 45% → 85% | `processing` | "正在分析文档内容..." | 内部阻塞，外部等待 |
| **高亮渲染** | 85% → 95% | `processing` | "正在生成高亮 PDF..." | 最终 PDF 生成 |
| **任务完成** | 100% | `completed` | "处理完成！" | 写入结果路径 |
| **任务失败** | - | `failed` | "处理失败：xxx" | 记录错误信息 |

### 3.2 关键改进点

**LangExtract 等待可感知**

```python
# 在阻塞调用前，先更新 Redis 进度
await update_progress(
    task_id=task_id,
    stage="extraction", 
    progress=45,
    message="调用大模型提取实体（约需1-3分钟，请耐心等待）..."
)

# 这一步阻塞 1-3 分钟，但用户已经收到通知
extraction_result = await asyncio.to_thread(
    lang_extract.extract, 
    md_content
)
```

---

## 4. 核心数据结构

### 4.1 Redis Hash 存储结构

```
Key: fusionmark:task:status:{task_id}
Type: Hash

Field           Value Example
─────────────────────────────────────────
task_id         "task_abc123"
document_url    "https://example.com/file.pdf"
status          "processing" | "completed" | "failed"
stage           "mineru" | "extraction" | "highlight"
progress        "45"
message         "调用大模型提取实体（约需1-3分钟）..."
result          '{"output_path": "/path/to/file.pdf"}'
created_at      "2026-03-18T16:44:53"
updated_at      "2026-03-18T16:45:12"
```

### 4.2 WebSocket 消息格式

```typescript
// 连接响应
{
  "type": "connected",
  "data": {
    "task_id": "task_abc123",
    "status": "processing",
    "progress": 45,
    "stage": "extraction",
    "message": "调用大模型提取实体..."
  }
}

// 进度更新
{
  "type": "progress",
  "data": {
    "stage": "extraction",
    "progress": 45,
    "message": "调用大模型提取实体（约需1-3分钟）..."
  }
}

// 完成
{
  "type": "progress",
  "data": {
    "stage": "completed",
    "progress": 100,
    "status": "completed",
    "result": {"output_path": "/path/to/file.pdf"}
  }
}
```

---

## 5. 关键代码设计

### 5.1 Redis 进度存储类

```python
# progress_store.py
import redis
import json
from typing import Optional, Dict, Any
from datetime import datetime

class RedisProgressStore:
    """Redis 进度看板 - 替代内存存储"""
    
    KEY_PREFIX = "fusionmark:task"
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    def create_task(self, task_id: str, document_url: str) -> Dict:
        """创建任务，初始化进度"""
        data = {
            "task_id": task_id,
            "document_url": document_url,
            "status": "pending",
            "stage": "pending",
            "progress": "5",
            "message": "任务已接收，准备处理...",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self._update_hash(task_id, data)
        return data
    
    def update_progress(self, task_id: str, **kwargs):
        """更新进度，同时发布 PubSub 消息"""
        kwargs["updated_at"] = datetime.now().isoformat()
        self._update_hash(task_id, kwargs)
        
        # 发布实时通知
        channel = f"{self.KEY_PREFIX}:pubsub:{task_id}"
        self.redis.publish(channel, json.dumps(kwargs))
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        key = f"{self.KEY_PREFIX}:status:{task_id}"
        return self.redis.hgetall(key) or None
    
    def _update_hash(self, task_id: str, data: Dict):
        key = f"{self.KEY_PREFIX}:status:{task_id}"
        self.redis.hset(key, mapping=data)
```

### 5.2 异步任务处理流程

```python
# api_server.py - 后台任务处理

async def process_pdf_task(task_id: str, request: SubmitTaskRequest):
    """异步处理任务"""
    store = RedisProgressStore()
    
    async def update(stage: str, progress: int, message: str):
        store.update_progress(
            task_id=task_id,
            stage=stage,
            progress=str(progress),
            message=message,
            status="processing"
        )
    
    try:
        # Step 1: MinerU 解析 (有进度回调)
        await update("mineru", 10, "正在解析 PDF 内容...")
        
        def mineru_cb(attempt, state, data):
            pg = data.get("extract_progress", {})
            if pg.get("total_pages"):
                pct = int(pg["extracted_pages"] / pg["total_pages"] * 30) + 10
                store.update_progress(
                    task_id=task_id,
                    progress=str(min(pct, 40)),
                    message=f"解析中... {pg['extracted_pages']}/{pg['total_pages']}页"
                )
        
        mineru_result = await asyncio.to_thread(
            mineru_client.process_document,
            url=request.document_url,
            wait_callback=mineru_cb
        )
        
        # Step 2: LangExtract ⭐ 关键：阻塞前先发状态
        await update("extraction", 45, 
            "调用大模型提取实体（约需1-3分钟，请耐心等待）...")
        
        highlight_result = await asyncio.to_thread(
            highlight_service.process_text,
            md_text=mineru_result.content
        )
        
        await update("extraction", 85, 
            f"提取完成，共 {highlight_result.extraction_count} 个实体")
        
        # Step 3: 高亮渲染
        await update("highlight", 90, "正在生成高亮 PDF...")
        # ... 渲染代码 ...
        
        # 完成
        store.update_progress(
            task_id=task_id,
            stage="completed",
            progress="100",
            status="completed",
            message="处理完成",
            result=json.dumps({"output_path": str(output_path)})
        )
        
    except Exception as e:
        store.update_progress(
            task_id=task_id,
            stage="failed",
            status="failed",
            message=f"处理失败: {str(e)}"
        )
```

### 5.3 WebSocket 实时推送

```python
# websocket_handler.py
import aioredis
import json
from fastapi import WebSocket

class WebSocketProgressHandler:
    """WebSocket 进度推送 - 从 Redis PubSub 读取"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
    
    async def handle(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        
        # 1. 先发送当前状态
        store = RedisProgressStore()
        current = store.get_task(task_id)
        await websocket.send_json({
            "type": "connected", 
            "data": current or {"error": "任务不存在"}
        })
        
        if not current:
            await websocket.close()
            return
        
        # 2. 订阅 Redis PubSub
        redis = await aioredis.from_url(self.redis_url)
        pubsub = redis.pubsub()
        channel = f"fusionmark:task:pubsub:{task_id}"
        await pubsub.subscribe(channel)
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await websocket.send_json({
                        "type": "progress",
                        "data": data
                    })
                    
                    # 任务完成或失败，关闭连接
                    if data.get("status") in ["completed", "failed"]:
                        break
                        
        except WebSocketDisconnect:
            pass
        finally:
            await pubsub.unsubscribe(channel)
            await redis.close()
```

---

## 6. 部署方案

### 6.1 本地开发

```bash
# 1. 启动 Redis
redis-server

# 2. 启动 FastAPI（单一进程）
uvicorn api_server:app --reload --port 8000
```

### 6.2 生产部署

```bash
# Docker Compose 示例
version: '3'
services:
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    
  api:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
    ports:
      - "8000:8000"
    depends_on:
      - redis

volumes:
  redis_data:
```

---

## 7. 与现有代码的关系

### 7.1 复用组件

| 现有组件 | 复用方式 | 说明 |
|---------|---------|------|
| `mineru_client.py` | 直接复用 | 在后台任务中调用 |
| `md_highlight_service.py` | 直接复用 | 在后台任务中调用 |
| `full_pipeline_service.py` | 参考逻辑 | 流程控制逻辑复用 |
| `api_server.py` | 改造升级 | 接入 Redis 进度存储 |

### 7.2 废弃组件

| 废弃组件 | 说明 |
|---------|------|
| `celery_chain_pipeline/` | 整个目录废弃 |
| `celery_config.py` | Celery 配置废弃 |
| `celery_tasks.py` | Celery 任务定义废弃 |
| `progress_manager.py` | 被 `progress_store.py` 替代 |

---

## 8. 后续优化方向

1. **LangExtract 流式进度** - 如果 LangExtract 支持流式输出，可在内部循环中持续更新进度（45% → 85% 逐步推进）
2. **任务超时控制** - 添加任务执行超时机制
3. **并发数限制** - 使用 `asyncio.Semaphore` 限制同时处理的任务数
4. **结果清理策略** - 定期清理过期的任务记录和输出文件

---

## 9. 总结

> **"FastAPI 自己就是 Worker，Redis 只做进度看板"**

### 架构优势

| 维度 | 评价 |
|------|------|
| 复杂度 | ⭐⭐⭐⭐⭐ 极简单一进程 |
| 部署成本 | ⭐⭐⭐⭐⭐ 只需 FastAPI + Redis |
| 进度可感知 | ⭐⭐⭐⭐⭐ 实时 WebSocket 推送 |
| 扩展性 | ⭐⭐⭐⭐☆ 预留水平扩展能力 |

### 核心改进

1. **去掉 Celery 框架** - 减少依赖，降低维护成本
2. **Redis 进度看板** - 任务状态持久化，重启不丢
3. **LangExtract 等待可感知** - 用户知道在等大模型
4. **单一进程部署** - 开发、测试、部署都更简单

---

## 关联文档

- [原始 Celery Chain 架构设计](./celery_full_pipeline_design.md) (已废弃)
- [Redis 进度实现方案](./redis进度实现方案.md) (需求来源)
