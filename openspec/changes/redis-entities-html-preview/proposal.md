## Why

The frontend entity panel currently cannot directly display the actual LangExtract results produced during task execution. We already export JSONL and official LangExtract HTML for debugging, but these artifacts stay on disk and are not available through the task result returned by Redis-backed APIs.

This makes it hard for users to quickly verify what was extracted from the document in the main workflow. We need a lightweight way to expose both structured extraction data and a directly renderable HTML preview to the frontend without changing the overall API flow.

## What Changes

- Store structured extraction entities in Redis task result
- Store LangExtract HTML preview in Redis task result
- Update task processing pipeline to include extraction preview payloads
- Update frontend entity panel to prefer rendering LangExtract HTML
- Add fallback rendering from structured entities or category counts

## Capabilities

### New Capabilities
- `extraction-preview`: Task result includes extraction preview data for frontend display

### Modified Capabilities
- `task-result`: Completed task result now includes extraction preview payloads

## Impact

- Backend highlight service (`services/core/highlight.py`)
- Async task processor (`services/api/task_processor.py`)
- Frontend entity preview panel (`frontend/src/`)
- Redis task result payload size increases moderately
