## ADDED Requirements

### Requirement: Configurable MinerU Provider
The system SHALL select a MinerU connection provider from configuration and use that provider for document parsing in both API task processing and full pipeline execution.

#### Scenario: Open SDK provider selected
- **WHEN** the configured MinerU client mode is `open_sdk`
- **THEN** the system SHALL parse documents through the official MinerU Open SDK provider

#### Scenario: Legacy provider selected
- **WHEN** the configured MinerU client mode is `legacy_v4`
- **THEN** the system SHALL parse documents through the existing v4 URL client behavior

#### Scenario: Unknown provider configured
- **WHEN** the configured MinerU client mode is not supported
- **THEN** the system SHALL fail fast with a clear configuration error before starting document processing

### Requirement: Normalized Parse Result
Every MinerU provider SHALL return a normalized parse result containing task identity, terminal state, extracted Markdown content, artifact directory path, and error details when parsing fails.

#### Scenario: Successful parse result
- **WHEN** a provider completes document parsing successfully
- **THEN** the normalized result SHALL include `state`, `task_id`, `content`, and `extract_dir`

#### Scenario: Failed parse result
- **WHEN** a provider reports a failed MinerU task
- **THEN** the normalized result SHALL include `state` and `error_msg` without requiring downstream code to inspect provider-specific result objects

#### Scenario: Missing Markdown content
- **WHEN** a provider completes but cannot produce Markdown content
- **THEN** the system SHALL treat the parse as failed for the FusionMark pipeline and report a clear error

### Requirement: Document Source Resolution
The system SHALL resolve document inputs into a provider-compatible source before parsing.

#### Scenario: HTTP URL source
- **WHEN** the task input is an HTTP or HTTPS URL and the selected provider supports direct URL input
- **THEN** the resolver SHALL pass the URL to the provider without materializing it locally

#### Scenario: Storage object source
- **WHEN** the task input references a storage provider object key
- **THEN** the resolver SHALL read the object through `StorageProvider`, write it under the task workspace input directory, and pass the local file path to the provider

#### Scenario: Local file source
- **WHEN** the task input references a local file path
- **THEN** the resolver SHALL validate the file exists and pass the local file path to the provider

#### Scenario: Unsupported source
- **WHEN** the task input cannot be resolved to a supported URL or local file
- **THEN** the system SHALL fail the task with a clear input resolution error

### Requirement: Open SDK Artifact Persistence Compatibility
The Open SDK provider SHALL write MinerU output artifacts to the task artifact directory in a structure compatible with existing storage persistence.

#### Scenario: SDK saves official artifacts
- **WHEN** the official SDK result exposes an artifact save operation
- **THEN** the provider SHALL save official artifacts into the normalized `extract_dir`

#### Scenario: Markdown artifact present
- **WHEN** parsing succeeds through the Open SDK provider
- **THEN** the normalized `extract_dir` SHALL contain a Markdown artifact that downstream persistence can store with other MinerU extracted outputs

#### Scenario: Raw result debugging artifacts
- **WHEN** parsing succeeds through the Open SDK provider
- **THEN** the provider SHOULD store provider result metadata as JSON artifacts for troubleshooting without adding large payloads to Redis

### Requirement: Progress Reporting Compatibility
The MinerU provider layer SHALL support progress callbacks compatible with the existing task processor.

#### Scenario: Page progress available
- **WHEN** the selected provider exposes extracted page and total page progress
- **THEN** the callback data SHALL include those values so WebSocket progress can calculate MinerU stage percentage

#### Scenario: Page progress unavailable
- **WHEN** the selected provider does not expose page-level progress
- **THEN** the callback data SHALL still report coarse state transitions so the task does not appear stalled

### Requirement: Backward-Compatible Public Task Flow
The existing public task submission flow using `document_url` SHALL continue to work after the provider refactor.

#### Scenario: Existing URL request submitted
- **WHEN** a client submits `POST /api/v1/tasks` with `document_url`
- **THEN** the system SHALL process the task through the configured MinerU provider without requiring frontend changes

#### Scenario: Existing artifact APIs used
- **WHEN** a task completes after parsing through the Open SDK provider
- **THEN** existing artifact and download endpoints SHALL continue to retrieve persisted LangExtract and highlight artifacts
