# Tasks

## 1. Design

- [x] Confirm upload route path and multipart fields
- [x] Confirm storage key layout for uploaded source files
- [x] Confirm validation behavior for empty/unsupported uploads

## 2. Implementation

- [x] Add upload request handling in `services/api/server.py`
- [x] Save uploaded files through the active Storage Provider
- [x] Submit background task using `storage://tasks/{task_id}/input/{safe_filename}`
- [x] Reject upload submissions when MinerU mode is not `open_sdk`
- [x] Keep JSON `POST /api/v1/tasks` behavior unchanged
- [x] Add shared helpers where needed to avoid duplicating task creation logic

## 3. Validation

- [x] Add tests for local storage upload task submission
- [x] Add tests for mocked storage provider / MinIO-compatible path
- [x] Add tests for invalid upload inputs
- [x] Run focused backend pytest
- [x] Run OpenSpec validation

## 4. Documentation and Tracking

- [x] Update API/service docs with upload examples
- [x] Update bd issue `fusion-mark-rte`
- [x] Update this OpenSpec checklist as implementation tasks complete
