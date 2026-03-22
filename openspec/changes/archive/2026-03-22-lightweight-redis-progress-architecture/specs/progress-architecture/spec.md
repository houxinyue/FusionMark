## ADDED Requirements

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

## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: Celery Chain architecture
**Reason**: Architecture is too heavyweight, introducing unnecessary complexity for single-machine deployment scenarios. Using FastAPI background tasks + Redis progress storage as lightweight alternative.

**Migration**: None. The new architecture replaces Celery Chain completely.

#### Removed Scenarios:
- Celery Worker process management
- Celery Chain task orchestration
- Celery result backend configuration
