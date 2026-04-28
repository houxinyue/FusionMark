# Lightweight Redis Progress Architecture

## Purpose

Define the lightweight task progress architecture that uses FastAPI background processing, Redis task state, and WebSocket updates instead of the older Celery chain approach.

## Requirements

### Requirement: Redis Task Progress Storage

The system SHALL store task progress information in Redis, including progress percentage, status, message, stage logs, artifacts, and result data.

#### Scenario: Create task and initialize progress
- **WHEN** a user submits a PDF processing task
- **THEN** the system creates a Redis task record with an initial progress state

#### Scenario: Update task progress
- **WHEN** a processing stage changes
- **THEN** the system updates Redis progress state and emits a progress notification

#### Scenario: Query task status
- **WHEN** a user queries task status
- **THEN** the system returns the latest task snapshot from Redis

### Requirement: WebSocket Real-Time Push

The system SHALL push task progress updates to the frontend through a task WebSocket connection.

#### Scenario: Get current status on WebSocket connection
- **WHEN** the frontend connects to a task WebSocket
- **THEN** the backend sends the current task status

#### Scenario: Receive real-time progress update
- **WHEN** task progress changes
- **THEN** the backend pushes the progress update to connected clients

#### Scenario: Complete or fail task
- **WHEN** a task reaches a terminal state
- **THEN** the final status and available artifacts are visible to the frontend

### Requirement: Stage Waiting Awareness

The system SHALL expose clear stage messages for long-running MinerU, LangExtract, and PDF highlight work.

#### Scenario: Enter LangExtract stage
- **WHEN** MinerU parsing is completed and entity extraction starts
- **THEN** the frontend receives a LangExtract progress message before the long-running call blocks

#### Scenario: Finish extraction and highlighting
- **WHEN** entity extraction and highlight PDF generation complete
- **THEN** the task result includes downloadable artifacts and preview metadata

### Requirement: Background Task Processing

The system SHALL process PDF tasks asynchronously so the task submission API responds immediately.

#### Scenario: Start processing task asynchronously
- **WHEN** a user submits a PDF URL through `POST /api/v1/tasks`
- **THEN** the API immediately returns a task identifier and starts background processing
