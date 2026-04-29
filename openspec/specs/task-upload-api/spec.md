# task-upload-api Specification

## Purpose
TBD - created by archiving change add-task-upload-input-api. Update Purpose after archive.
## Requirements
### Requirement: Multipart Task Upload Endpoint

The system SHALL provide a task submission endpoint that accepts an uploaded document file using `multipart/form-data` and returns the same task response shape as the existing JSON task submission endpoint.

#### Scenario: Submit uploaded document task

- **WHEN** a client posts a valid document file to `POST /api/v1/tasks/upload`
- **THEN** the system SHALL create a new task
- **AND** return a `TaskResponse` containing `task_id`, `status`, `message`, and timestamps
- **AND** schedule the existing background processing flow for that task

#### Scenario: Existing JSON task submission remains compatible

- **WHEN** a client posts JSON to `POST /api/v1/tasks`
- **THEN** the system SHALL continue to process URL, storage object, and local file sources without requiring multipart upload

### Requirement: Storage-Provider-Backed Upload Persistence

Uploaded source files SHALL be persisted through the configured Storage Provider before task processing begins.

#### Scenario: Local storage provider selected

- **WHEN** the active Storage Provider is local
- **THEN** the uploaded file SHALL be saved under `tasks/{task_id}/input/{safe_filename}` in local storage
- **AND** the task processor SHALL receive `storage://tasks/{task_id}/input/{safe_filename}` as the document source

#### Scenario: MinIO storage provider selected

- **WHEN** the active Storage Provider is MinIO
- **THEN** the uploaded file SHALL be saved under `tasks/{task_id}/input/{safe_filename}` in MinIO
- **AND** the task processor SHALL receive `storage://tasks/{task_id}/input/{safe_filename}` as the document source

### Requirement: Upload Input Validation

The upload endpoint SHALL reject invalid uploads before scheduling document processing.

#### Scenario: Empty file upload

- **WHEN** the uploaded file has no content
- **THEN** the endpoint SHALL reject the request with a clear validation error

#### Scenario: Unsafe filename

- **WHEN** the uploaded file name contains path separators or unsafe characters
- **THEN** the system SHALL sanitize the filename before creating the storage object key

#### Scenario: Unsupported file extension

- **WHEN** the uploaded file extension is not supported by the document parsing flow
- **THEN** the endpoint SHALL reject the request with a clear validation error

### Requirement: Uploaded Source Processing Compatibility

Uploaded files SHALL be processed through the same downstream pipeline as URL tasks.

#### Scenario: Uploaded file enters MinerU open SDK flow

- **WHEN** a task is created from an uploaded file
- **THEN** the existing document input resolver SHALL materialize the `storage://...` source into the task workspace input directory
- **AND** the selected MinerU provider SHALL parse that local file source

#### Scenario: Deprecated legacy provider configured for upload

- **WHEN** `legacy_v4` is configured and a client submits an uploaded file
- **THEN** the endpoint SHALL reject the request before scheduling processing
- **AND** the error SHALL explain that uploaded-file tasks require `open_sdk`

