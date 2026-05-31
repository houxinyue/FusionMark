# Tasks

## 1. Root Scaffold
- [x] 1.1 Create standalone `agent-copilot/` root directory
- [x] 1.2 Add minimal `README.md`, `pyproject.toml`, and `.env.example`
- [x] 1.3 Add `app/__init__.py` and `app/main.py` startup entry
- [x] 1.4 Add initial `scripts/` entry for running the app with `uv`

## 2. Package Layout
- [x] 2.1 Create package folders for `api`, `core`, `agent`, `storage`, `models`, `schemas`, `config`, `prompts`, and `utils`
- [x] 2.2 Add placeholder module files to make the package importable
- [x] 2.3 Add a minimal test that verifies the package imports cleanly

## 3. Core Boundaries
- [x] 3.1 Define the session and checkpoint domain objects
- [x] 3.2 Define storage interfaces for session, checkpoint, and archive access
- [x] 3.3 Define orchestration service boundaries without concrete backend bindings

## 4. Future Execution Hooks
- [x] 4.1 Prepare placeholders for Redis-backed runtime state
- [x] 4.2 Prepare placeholders for MinIO archive handling
- [x] 4.3 Prepare placeholders for prompt loading and validation flow

## 5. Validation
- [x] 5.1 Verify the new module structure is present
- [x] 5.2 Run the new app entrypoint with `uv`
- [x] 5.3 Run the package/import tests
