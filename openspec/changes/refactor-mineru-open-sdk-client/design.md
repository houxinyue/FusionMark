## Context

FusionMark currently integrates MinerU through a hand-written client in `services/clients/mineru.py`. The client accepts a document URL, calls MinerU v4 extract APIs, polls status, downloads `full_zip_url`, extracts the ZIP, and reads `full.md`. The task processor and full pipeline depend on the resulting `ParseResult.content` and `ParseResult.extract_dir`.

The project recently added a storage provider abstraction and workspace cleanup. This makes MinIO-backed inputs and output persistence natural, but the current MinerU client still assumes URL input and local ZIP extraction. The official MinerU-Ecosystem Python SDK (`mineru-open-sdk`) supports URL and local file sources, official result models, artifact saving, and more output formats. The refactor should adopt this SDK without breaking LangExtract, highlighter rendering, Redis progress, or existing artifact APIs.

## Goals / Non-Goals

**Goals:**
- Add a provider-style MinerU connection layer with an official SDK implementation and a legacy fallback implementation.
- Keep the internal `ParseResult` contract stable for downstream stages.
- Support document sources from HTTP URLs, storage provider object keys, and local workspace files.
- Materialize MinIO/storage objects to task workspace files before SDK upload/extraction.
- Preserve existing WebSocket progress semantics as far as the selected provider exposes progress data.
- Save SDK output artifacts to a directory compatible with current storage persistence.

**Non-Goals:**
- Replace LangExtract with MinerU KIE extraction results.
- Add a new frontend upload workflow in this change.
- Remove the existing legacy v4 client immediately.
- Change public artifact download APIs.
- Introduce a database or new long-term task metadata store.

## Decisions

### Use `mineru-open-sdk` instead of KIE SDK first

`mineru-open-sdk` maps to the current MinerU document parsing workflow and supports URL/local file inputs plus complete result saving. KIE SDK is pipeline-oriented, returns `parse/split/extract`, only supports synchronous polling, and would require a larger semantic change to the extraction stage. The first implementation SHALL target `mineru-open-sdk`.

Alternative considered: directly adopt KIE SDK. Rejected for this change because it mixes MinerU parsing with KIE extraction and does not match the current `full.md` based LangExtract pipeline.

### Preserve `ParseResult` as the project boundary

Downstream code already consumes `task_id`, `state`, `extract_dir`, `content`, and `error_msg`. The SDK provider SHALL normalize SDK result objects into this shape. This keeps `task_processor.py`, `FullPipelineService`, highlighter, and storage persistence focused on minimal integration changes.

Alternative considered: propagate SDK result models across the pipeline. Rejected because it would spread SDK-specific contracts into unrelated modules.

### Add a document input resolver

The system SHALL resolve source descriptors before invoking MinerU:

- HTTP/HTTPS URL may be passed directly to providers that support URL inputs.
- Storage object keys SHALL be read through `StorageProvider` and written to `workspaces/{task_id}/input/`.
- Local file paths SHALL be validated and passed as local source paths.

The resolver makes MinIO input support independent from the MinerU provider. It also gives future file-upload API work a stable backend entry point.

### Provider selection by configuration

Configuration SHALL select `open_sdk` or `legacy_v4`, defaulting to `open_sdk` after implementation validation. During rollout, `legacy_v4` remains available for rollback.

Environment variables SHALL continue to support `MINERU_API_KEY`; SDK token configuration can use the same value or a configured token env name. This avoids requiring immediate secret renaming.

### Artifact compatibility

The SDK provider SHALL write artifacts into `extract_dir` in a form compatible with existing persistence:

- `full.md` or equivalent Markdown file MUST be present when parsing succeeds.
- Raw SDK metadata/result files SHOULD be stored as JSON for debugging.
- `result.save_all(extract_dir)` SHOULD be used when available to preserve official output formats.

## Risks / Trade-offs

- SDK result shape drift → Keep normalization isolated in the SDK provider and cover it with unit tests using sample result objects.
- SDK dependency or network behavior differs from current requests client → Keep `legacy_v4` provider available and configurable.
- Storage object inputs can be large → Materialize to task workspace, enforce provider file type checks, and rely on workspace cleanup.
- Progress may be less granular in SDK mode → Preserve page-based progress when SDK batch status exposes it; otherwise emit coarse upload/submitted/running/done progress.
- Public URL and local file behavior differ by provider → Resolve source descriptors explicitly and document which providers support direct URL passthrough.

## Migration Plan

1. Add provider abstraction and keep current behavior through a legacy provider adapter.
2. Add `mineru-open-sdk` dependency and implement `OpenSdkMinerUClient`.
3. Add input resolver and route storage/local sources through workspace materialization.
4. Switch task processor and full pipeline to use the provider factory.
5. Validate legacy URL flow and SDK URL/local/storage flow.
6. Default to `open_sdk` after validation; rollback by setting `mineru_client_mode=legacy_v4`.

## Open Questions

- Which environment variable name should be preferred long term: `MINERU_API_KEY`, `MINERU_TOKEN`, or both?
- Should storage-key input be added to the public task API in this change, or only implemented internally for the next upload workflow?
- Which SDK extra formats should be enabled by default beyond Markdown and JSON artifacts?
