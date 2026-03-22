# 轻量化 Redis 进度架构

## 概述

使用 FastAPI 后台任务 + Redis 进度存储的轻量级架构，替代 Celery Chain 架构，实现任务进度实时可见。

## 需求

### Requirement: Redis 进度存储

The system SHALL use Redis Hash structure to store task progress information, including progress percentage, status, message, and result.

#### Scenario: Create task and initialize progress
- **WHEN** user submits PDF processing task
- **THEN** system creates task record in Redis Hash with initial progress 5%

#### Scenario: Update task progress
- **WHEN** processing stage changes (MinerU/LangExtract/Highlight)
- **THEN** system updates progress field in Redis Hash
- **AND** publishes PubSub message to notify frontend

#### Scenario: Query task status
- **WHEN** user queries task status
- **THEN** system reads latest progress from Redis Hash and returns

---

### Requirement: WebSocket real-time push

The system SHALL push task progress updates to frontend in real-time through WebSocket connection.

#### Scenario: Get current status on WebSocket connection
- **WHEN** user opens task detail page and WebSocket connects
- **THEN** system immediately sends current task status to frontend

#### Scenario: Receive real-time progress update
- **WHEN** task progress changes and Redis PubSub receives message
- **THEN** system immediately pushes update to frontend

#### Scenario: Close connection after task completion
- **WHEN** task is completed or failed
- **THEN** final status is pushed to frontend
- **AND** connection is kept or closed based on policy

---

### Requirement: LangExtract waiting awareness

The system SHALL send progress update before LangExtract blocking call to inform user about waiting time.

#### Scenario: Send status before entering LangExtract
- **WHEN** MinerU parsing is completed
- **AND** system is about to call LangExtract (blocking 1-3 minutes)
- **THEN** system first updates progress to 45% with message "Calling LLM for entity extraction (about 1-3 minutes)..."
- **AND** user sees clear waiting indication

#### Scenario: Update progress after LangExtract completes
- **WHEN** LangExtract blocking call is completed
- **AND** extraction results are obtained
- **THEN** system updates progress to 85% showing extracted entity count

---

### Requirement: Background task processing

The system SHALL use async approach to process PDF tasks so that API can respond immediately without being blocked.

#### Scenario: Start processing task asynchronously
- **WHEN** user submits PDF URL via POST /api/v1/tasks
- **THEN** system immediately returns task_id
- **AND** uses asyncio.create_task() to start background processing

#### Scenario: MinerU progress callback
- **WHEN** MinerU is parsing document
- **AND** MinerU returns page progress
- **THEN** system updates Redis progress in real-time through callback function (10% → 40%)

---

## 废弃说明

### Deprecated: Celery Chain architecture

**Reason**: Architecture is too heavyweight, introducing unnecessary complexity for single-machine deployment scenarios. Using FastAPI background tasks + Redis progress storage as lightweight alternative.

**Migration**: None. The new architecture replaces Celery Chain completely.

#### Removed Components:
- Celery Worker process management
- Celery Chain task orchestration
- Celery result backend configuration

## 架构图

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
│  │       2. await lang_extract() ──► Redis 进度更新      │   │
│  │       3. await highlight() ──► Redis 进度更新         │   │
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

## 相关文件

- `services/api/progress_store.py` - Redis 进度存储类
- `services/api/websocket_handler.py` - WebSocket PubSub 处理器
- `services/api/task_processor.py` - 异步任务处理器
- `services/api/server.py` - FastAPI 服务入口
