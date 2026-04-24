# Storage Provider MinIO - Tasks

## Phase 1: Storage Abstraction (0.5天)

- [x] Create storage provider interface
  - [x] Define storage object metadata model
  - [x] Define minimal save/upload/read URL methods
- [x] Create provider factory
  - [x] Read provider selection from environment variables
  - [x] Support `local` and `minio`

## Phase 2: Provider Implementations (1天)

- [x] Implement `LocalStorageProvider`
- [x] Implement `MinioStorageProvider`
- [x] Add configuration loading for MinIO credentials and bucket settings

## Phase 3: Artifact Persistence Integration (1天)

- [x] Persist MinerU extracted outputs through storage provider
  - [x] Keep extracted directory semantics
  - [x] Do not persist zip archive
- [x] Persist LangExtract artifacts through storage provider
  - [x] Save JSONL/HTML/entities when enabled
  - [x] Save verbose request/response artifacts only when enabled
- [x] Persist highlight outputs through storage provider

## Phase 4: Task Result Integration (0.5天)

- [x] Add object-key references to task result payload
- [x] Preserve backward-compatible local-path behavior where needed
- [x] Validate result payload structure for frontend and download flow

## Phase 5: Workspace Unification & Auto-Cleanup (0.5天) — 扩展需求

- [x] Introduce workspace management (`services/storage/workspace.py`)
- [x] Route MinerU/Highlight outputs to `workspaces/{task_id}/` instead of project root
- [x] Upload artifacts to storage after task completion
- [x] Auto-cleanup workspace when `CLEAN_WORKSPACE_AFTER_UPLOAD=true`
- [x] Fix `highlight_output` premature directory creation on service startup

## Phase 6: Redis Result Slimming & Artifacts API (0.5天) — 扩展需求

- [x] Remove `langextract_html` and `entities` from Redis result payload
- [x] Add `GET /api/v1/tasks/{task_id}/artifacts/{artifact_type}` endpoint
  - [x] Support `langextract_html` (text/html)
  - [x] Support `entities` (application/json)
  - [x] Support `highlight_pdf` (application/pdf)
- [x] Download endpoint fallback to storage provider when local file is absent

## Phase 7: Frontend Adaptation (0.5天) — 扩展需求

- [x] WebSocket completed: only enable trace button, record artifact URL
- [x] Click "View Extraction Results" button: lazy-load HTML via artifacts API
- [x] Iframe render via `srcdoc` with fetched HTML content
- [x] Fallback to `category_counts` summary when artifacts unavailable

## Phase 8: Validation (0.5天)

- [x] Validate local provider flow
- [ ] Validate MinIO provider flow (pending MinIO service setup)
- [x] Validate environment-variable-based artifact retention
- [x] Validate workspace auto-cleanup
- [x] Validate artifacts API (GET /artifacts/langextract_html)
- [x] Validate frontend lazy-load interaction
