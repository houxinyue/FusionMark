## ADDED Requirements

### Requirement: URL task submission
The web-pc frontend SHALL allow users to submit a document URL to the backend task API.

#### Scenario: Valid URL creates a task
- **WHEN** the user enters a valid HTTP or HTTPS document URL and clicks the submit action
- **THEN** the frontend sends `POST /api/v1/tasks` with the URL and default processing options
- **AND** stores the returned `task_id`
- **AND** marks the task as pending or processing in the task store

#### Scenario: Empty URL is rejected client-side
- **WHEN** the user submits an empty URL
- **THEN** the frontend does not call the backend
- **AND** displays or records a validation failure state

### Requirement: WebSocket progress integration
The web-pc frontend SHALL connect to the backend task WebSocket after task creation and apply progress updates to the task store.

#### Scenario: Connected snapshot initializes progress
- **WHEN** the backend sends a `connected` WebSocket message with task data
- **THEN** the frontend normalizes the payload into the `TaskProgress` structure
- **AND** updates task status, overall progress, stage progress, and logs

#### Scenario: Progress message updates current task
- **WHEN** the backend sends a `progress` WebSocket message
- **THEN** the frontend updates the current task status and stage progress from the payload
- **AND** supplies defaults for any missing stage fields

#### Scenario: Heartbeat does not disrupt UI state
- **WHEN** the backend sends a `heartbeat` WebSocket message
- **THEN** the frontend keeps the current task state unchanged

### Requirement: WebSocket error fallback
The web-pc frontend SHALL query the task detail endpoint before deciding that a WebSocket issue means task failure.

#### Scenario: WebSocket error occurs during processing
- **WHEN** the WebSocket errors or closes unexpectedly while a task is active
- **THEN** the frontend calls `GET /api/v1/tasks/{task_id}` when possible
- **AND** applies the returned task snapshot
- **AND** only marks the task failed if the backend status is failed or the fallback query fails

### Requirement: Completion and download entry
The web-pc frontend SHALL expose a result download action after the backend reports a completed task.

#### Scenario: Completed task shows download
- **WHEN** the task status becomes `completed`
- **THEN** the inspect rail exposes an action using `GET /api/v1/tasks/{task_id}/download`

#### Scenario: Incomplete task hides download
- **WHEN** the task status is pending, processing, or failed
- **THEN** the result PDF download action is not shown as an available completed result

### Requirement: Completed PDF preview
The web-pc frontend SHALL render the completed highlight PDF artifact in the center PDF viewer.

#### Scenario: Completed task loads highlight PDF
- **WHEN** the task status becomes `completed`
- **THEN** the center PDF viewer loads `GET /api/v1/tasks/{task_id}/artifacts/highlight_pdf`
- **AND** the toolbar reflects current page, total pages, and zoom state

### Requirement: Extraction result modal
The web-pc frontend SHALL show extracted entities and LangExtract visualization after task completion.

#### Scenario: Completed task opens extraction result
- **WHEN** the task status is `completed` and the user clicks the extraction result action
- **THEN** the frontend fetches `artifacts/langextract_html`
- **AND** displays a direct JSONL download action for `artifacts/entities`
- **AND** embeds the HTML visualization in an iframe

#### Scenario: Incomplete task cannot open extraction result
- **WHEN** the task is not completed
- **THEN** the extraction result action remains disabled

### Requirement: Build validation
The integration implementation SHALL pass the frontend production build.

#### Scenario: Frontend build passes
- **WHEN** implementation is complete
- **THEN** `pnpm.cmd build` succeeds in `web-pc`
