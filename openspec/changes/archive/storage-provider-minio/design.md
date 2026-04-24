## Context

Current artifact persistence is tightly coupled to local directories such as `mineru_output/` and `highlight_output/`. This creates operational fragility and makes production durability dependent on local disk.

At the same time, the project still needs a smooth local development experience. So the right architecture is not “MinIO only”, but a provider abstraction with MinIO as the object-storage implementation and local filesystem as the development/compatibility implementation.

## Goals / Non-Goals

**Goals:**
- Keep local development simple
- Support MinIO through configuration rather than hardcoded SDK calls in business logic
- Preserve MinerU extracted directory semantics
- Avoid storing redundant zip archives when extracted files already exist
- Allow LangExtract debug artifacts to be controlled by environment variables

**Non-Goals:**
- Migrate every historical local artifact immediately
- Introduce additional cloud providers in this change
- Remove all local-path references in one pass

## Decisions

### Decision 1: Use a provider abstraction
**Rationale**: Business logic should not depend directly on MinIO SDK or raw filesystem handling. This keeps the codebase extensible and aligned with the project's plugin-style preference.

### Decision 2: Support `local` and `minio` through environment variables
**Rationale**: This allows development and production to share the same business logic while switching persistence behavior via configuration.

### Decision 3: Store MinerU extracted outputs, not the original zip
**Rationale**: The application already uses extracted outputs directly. Keeping both zip and extracted files creates redundant storage without improving normal operations.

### Decision 4: Gate LangExtract artifact persistence with environment variables
**Rationale**: Some teams want full traceability while others want leaner storage usage. The system should support both without code changes.

## Configuration Model

Suggested environment variables:

```env
STORAGE_PROVIDER=local
LOCAL_STORAGE_ROOT=storage

MINIO_ENDPOINT=127.0.0.1:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=fusion-mark
MINIO_SECURE=false
MINIO_REGION=
MINIO_PREFIX=fusion-mark

STORE_MINERU_EXTRACTED=true
STORE_LANGEXTRACT_ARTIFACTS=true
STORE_LANGEXTRACT_VERBOSE_ARTIFACTS=false
STORE_HIGHLIGHT_ARTIFACTS=true
```

## Object Naming

Recommended key structure:

```text
{project}/{env}/tasks/{biz_task_id}/{stage}/{relative_path_or_filename}
```

Examples:

```text
fusion-mark/prod/tasks/task-20260424-001/mineru/extracted/full.md
fusion-mark/prod/tasks/task-20260424-001/langextract/extractions.jsonl
fusion-mark/prod/tasks/task-20260424-001/highlight/highlighted.pdf
```

## Workspace Architecture (扩展决策)

### Decision 5: Unified workspace under `workspaces/{task_id}/`
**Rationale**: MinerU zip extraction and PDF rendering require local file paths. Rather than scattering `mineru_output/` and `highlight_output/` in the project root, all temporary task outputs go into a single workspace directory. After upload to storage, the workspace is auto-cleaned.

### Decision 6: Lazy cleanup with `CLEAN_WORKSPACE_AFTER_UPLOAD`
**Rationale**: Immediate deletion after upload keeps disk lean. The flag allows debugging by disabling cleanup when needed.

### Decision 7: Redis result slimming — remove large fields
**Rationale**: `langextract_html` and `entities` can be large (MB-level). Storing them in Redis bloats payload and slows frontend sync. Moving them to storage and serving via a dedicated API reduces Redis memory and network overhead.

### Decision 8: Frontend lazy-load on button click
**Rationale**: Pre-loading HTML during WebSocket completion wastes bandwidth if the user never opens the trace modal. Only fetch artifacts when the user explicitly clicks "View Extraction Results".

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Upload failures leave task in inconsistent state | Mark task complete only after required artifacts are stored successfully |
| Provider abstraction adds complexity | Keep API small and focused on current artifact needs |
| Redis payload could become confusing between local paths and object keys | Standardize object reference fields in result payload |
| Workspace cleanup deletes files before user downloads | Download endpoint falls back to storage provider; local path is only a cache |
| HEAD request to artifacts API returns 405 (FastAPI default) | Use GET fetch in frontend and load content into iframe.srcdoc |

## Migration Plan

1. Introduce storage provider abstraction and factory
2. Add local and MinIO implementations
3. Introduce workspace management (`services/storage/workspace.py`)
4. Redirect MinerU/Highlight outputs to task-level workspaces
5. Persist key artifact groups through provider after task completion
6. Record object references in task results; remove heavy HTML/entities from Redis
7. Add artifacts API for on-demand artifact retrieval
8. Update frontend to lazy-load HTML via artifacts API on button click
9. Auto-clean workspace after successful upload
10. Keep local behavior available for development fallback

## Open Questions

1. Should completed downloads eventually return signed MinIO URLs, or stay proxied through the API?
2. Which historical local-path fields should remain during the transition period?
3. Should workspace cleanup be async (background thread) to avoid blocking task completion response?
