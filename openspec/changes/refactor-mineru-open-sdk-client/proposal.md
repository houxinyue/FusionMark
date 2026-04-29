## Why

The current MinerU integration is a hand-written v4 API client that tightly couples URL submission, polling, ZIP download, unzip layout, and Markdown discovery in one class. This makes it hard to support MinIO-backed inputs, local uploads, and the official MinerU SDK without changing downstream LangExtract, storage, and progress code.

MinerU-Ecosystem now provides an official `mineru-open-sdk` that supports both URL and local file sources and exposes parsed Markdown plus complete artifact saving. Refactoring around a provider interface lets the project adopt the official SDK while keeping the existing processing pipeline stable.

## What Changes

- Add a MinerU connection provider abstraction used by the API task processor and full pipeline service.
- Introduce an official SDK provider based on `mineru-open-sdk`.
- Preserve the current hand-written v4 client as a fallback provider during migration.
- Add document input resolution so URL, MinIO/storage object keys, and local workspace files can be materialized into a source accepted by the selected provider.
- Normalize provider results into the existing `ParseResult` contract used by LangExtract, highlight rendering, Redis progress, and artifact persistence.
- Add configuration for provider selection, SDK base URL/token, extra output formats, and input source behavior.
- Update validation coverage for both existing URL flow and SDK-backed local/storage input flow.

## Capabilities

### New Capabilities
- `mineru-connection-provider`: Select and run a MinerU provider that accepts supported document sources and returns a normalized parse result for downstream processing.

### Modified Capabilities
- None.

## Impact

- Backend client modules under `services/clients/`.
- Task execution path in `services/api/task_processor.py`.
- Full pipeline configuration in `services/core/full_pipeline.py` and `services/profiles/full_pipeline_config.yaml`.
- Dependency set in `pyproject.toml` / lock or exported requirements.
- Storage provider integration for MinIO object inputs and persisted MinerU artifacts.
- Tests and documentation for provider selection, input materialization, and parse result normalization.
