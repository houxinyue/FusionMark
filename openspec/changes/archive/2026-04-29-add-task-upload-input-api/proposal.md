## Why

`POST /api/v1/tasks` currently accepts JSON task input through `document_url`. After the MinerU provider refactor, the backend can resolve HTTP URLs, storage object keys, and local file paths, but there is still no public task submission endpoint that accepts a browser/client file upload.

Users need to submit a PDF/document file directly, while the backend must keep the same downstream task lifecycle, progress reporting, MinerU parsing, LangExtract extraction, highlight rendering, and artifact persistence behavior. Uploaded files should work with both local storage and MinIO through the existing Storage Provider abstraction.

## What Changes

- Add a multipart upload task endpoint that accepts an uploaded document file and the same task options currently accepted by `POST /api/v1/tasks`.
- Persist the uploaded file through `StorageProvider.save_file` or `save_bytes` under a task-scoped object key.
- Submit the background task using a `storage://...` document input so existing `DocumentInputResolver` materializes the file for the MinerU `open_sdk` provider.
- Keep the existing JSON `POST /api/v1/tasks` contract backward compatible.
- Add upload validation for file name, extension/content type, empty files, and clear task failure responses.
- Add tests for local storage upload and mocked MinIO/storage-provider behavior.

## Scope

In scope:

- Backend FastAPI task upload endpoint.
- Storage-provider-backed upload persistence.
- Compatibility with current `process_pdf_task` and `DocumentInputResolver`.
- API docs and service README updates.
- Unit/API-level tests that do not require real MinerU credentials.

Out of scope:

- Frontend upload UI changes.
- Real MinerU network validation with credentials.
- New database/task metadata store.
- Chunked/resumable uploads.
- Direct `legacy_v4` upload support. Uploaded files require `open_sdk`; `legacy_v4` is considered deprecated for uploaded-file tasks.

## API Contract

Add:

```text
POST /api/v1/tasks/upload
Content-Type: multipart/form-data
```

Fields:

- `file`: required uploaded document.
- `output_filename`: optional string.
- `custom_title`: optional string.
- `custom_prompt`: optional string.
- `model`: optional string, default `vlm`.
- `enable_ocr`: optional bool, default `true`.
- `enable_formula`: optional bool, default `true`.
- `enable_table`: optional bool, default `true`.
- `language`: optional string, default `ch`.

Response:

- Same `TaskResponse` shape as `POST /api/v1/tasks`.

Storage:

- Uploaded source file key: `tasks/{task_id}/input/{safe_filename}`.
- Background `document_url`: `storage://tasks/{task_id}/input/{safe_filename}`.

## Affected Modules

- `services/api/server.py`
- `services/api/task_processor.py` only if shared helper extraction is needed.
- `services/storage/*` only if a small helper is required; avoid changing provider contracts unless necessary.
- `services/clients/document_input.py` for source-recognition compatibility only if needed.
- `services/README.md` and root `README.md`
- Tests under `services/api/` and/or `services/clients/`

## Risks

- Large uploaded files may consume memory if read fully before saving.
- MinIO failures should fail the request before task creation or mark the task failed clearly.
- Uploaded filenames can contain unsafe path characters.
- Existing `SubmitTaskRequest` JSON route must remain backward compatible.
- `legacy_v4` is deprecated for uploaded-file tasks and will be rejected by the upload endpoint.

## Validation Plan

- Unit/API tests for multipart upload with local storage provider.
- Tests with a fake storage provider to ensure uploaded bytes are saved under `tasks/{task_id}/input/...`.
- Test that the background task receives a `storage://...` source.
- Run focused backend pytest for upload/provider/input tests.
- Run OpenSpec validation.

## Rollback Plan

- Remove the upload route and tests.
- Existing JSON `POST /api/v1/tasks` remains unchanged. If rollback is needed, remove the upload route while keeping URL/storage/local JSON task submission available.
