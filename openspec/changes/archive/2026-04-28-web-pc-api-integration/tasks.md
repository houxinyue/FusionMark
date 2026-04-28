# Tasks

## 1. Design
- [x] Confirm first integration scope: URL task -> WebSocket progress -> result download
- [x] Confirm backend endpoints and frontend integration files
- [x] Create OpenSpec proposal, tasks, and spec delta
- [x] Validate OpenSpec
- [x] Wait for user approval before implementation

## 2. Implementation
- [x] Update task API helpers and response types
- [x] Add task-store actions for task lifecycle and snapshot normalization
- [x] Update `UrlSubmit.vue` to create URL task and start WebSocket progress
- [x] Update `useTaskWebSocket.ts` to handle backend `connected`, `progress`, `heartbeat`, and error/fallback behavior
- [x] Display completion/failure state and result download entry in the inspect rail
- [x] Deduplicate and display stage logs from progress payloads
- [x] Load completed task highlight PDF artifact into the center PDF viewer
- [x] Add direct entities JSONL download and embed LangExtract HTML in the extraction result modal

## 3. Validation
- [x] Run `pnpm.cmd build` in `web-pc`
- [x] Verify backend `/health`
- [x] Submit a valid PDF URL through the UI
- [x] Verify WebSocket progress updates all three stages
- [x] Verify completed task can download the result PDF
- [x] Verify completed task renders highlight PDF in the center viewer
- [x] Verify extraction result modal provides JSONL download and embeds LangExtract HTML
- [x] Verify failure state is visible for failed tasks
