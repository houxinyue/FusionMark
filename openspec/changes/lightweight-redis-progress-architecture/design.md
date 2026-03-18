## Context

### Background
The project currently uses a memory-based task manager (`TaskManager` class in `api_server.py`) to track PDF processing progress. This approach has several limitations:
- Progress is lost when server restarts
- No persistence for task status
- WebSocket callbacks are memory-based and complex

### Current State
- `api_server.py` uses `BackgroundTasks` for async processing
- `TaskManager` stores tasks in Python dictionary
- WebSocket progress callbacks use synchronous wrappers
- Celery Chain architecture was attempted but abandoned due to complexity

### Constraints
- Single-machine deployment (no distributed requirement currently)
- Must maintain existing API compatibility
- Frontend already supports WebSocket progress updates

## Goals / Non-Goals

**Goals:**
- Replace memory-based progress storage with Redis
- Enable real-time progress push via WebSocket using Redis PubSub
- Make LangExtract waiting period perceptible to users
- Simplify architecture by removing Celery dependency
- Ensure task status persists across server restarts

**Non-Goals:**
- Distributed task processing (multiple workers)
- Automatic retry on failure
- Complex task orchestration or dependencies
- Horizontal scaling support

## Decisions

### Decision 1: Use Redis Hash for Progress Storage
**Rationale**: Redis Hash provides structured storage with O(1) field access, perfect for task status fields (progress, status, message, result).

**Alternative considered**: SQLite - rejected because Redis PubSub integrates better with real-time updates.

### Decision 2: Use Redis PubSub for Real-time Updates
**Rationale**: PubSub allows decoupled message broadcasting. WebSocket handler subscribes to channel, background task publishes updates.

**Alternative considered**: Polling - rejected due to latency and unnecessary load.

### Decision 3: Keep FastAPI as Worker (Single Process)
**Rationale**: For current single-machine deployment, `asyncio.create_task()` is sufficient. No need for separate worker processes.

**Alternative considered**: Celery Worker - rejected due to operational complexity.

### Decision 4: Update Progress Before Blocking Calls
**Rationale**: LangExtract blocks for 1-3 minutes. By updating progress before the call (45% with "calling LLM..." message), users understand the wait.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Redis becomes single point of failure | Document Redis as required dependency; use Redis persistence (AOF/RDB) |
| Memory usage grows with concurrent tasks | Add `maxmemory` policy to Redis; consider task timeout |
| WebSocket connection lost during processing | Client reconnection will fetch current status from Redis |
| LangExtract internal progress not visible | Document as known limitation; consider streaming if LangExtract supports it |

## Migration Plan

1. **Add Dependencies**
   - Add `redis>=5.0.1` and `aioredis>=2.9.3` to requirements.txt

2. **Create New Modules**
   - `progress_store.py` - Redis progress storage
   - `websocket_handler.py` - PubSub-based WebSocket handler

3. **Modify Existing Code**
   - Update `api_server.py` to use new progress store
   - Refactor `process_pdf_task` to async with Redis updates

4. **Testing**
   - Local Redis + FastAPI integration test
   - WebSocket real-time update test
   - Server restart recovery test

5. **Cleanup** (after validation)
   - Mark `celery_chain_pipeline/` as deprecated
   - Update documentation

## Open Questions

1. Should we add a maximum concurrent task limit to prevent resource exhaustion?
2. What's the Redis data retention policy for completed tasks?
3. Do we need to handle Redis reconnection scenarios?
