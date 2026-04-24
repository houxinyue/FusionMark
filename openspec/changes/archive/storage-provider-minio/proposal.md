## Why

The system currently stores MinerU, LangExtract, and highlight artifacts in local project directories. This is convenient for development but weak for production durability, multi-instance deployment, and historical traceability.

We need a storage abstraction that supports both local filesystem and MinIO object storage, selected through environment variables, so the application remains robust while preserving current development ergonomics.

## What Changes

- Introduce a storage provider abstraction for artifact persistence
- Support `local` and `minio` providers selected by environment variables
- Persist MinerU extracted outputs to storage without keeping zip archives
- Persist LangExtract artifacts to storage with environment-variable-controlled debug retention
- Persist highlight outputs to storage
- Store object references in task results instead of relying only on local paths

## Capabilities

### New Capabilities
- `artifact-storage`: Unified storage provider for task artifacts

### Modified Capabilities
- `task-result`: Completed task result can include object storage references
- `download`: Artifact retrieval can evolve away from strict local-path dependence

## Impact

- New storage module under `services/storage/`
- Backend pipeline and task processor integration
- Environment variable configuration for provider selection and artifact retention
- Redis task result payloads include object keys for persisted artifacts
