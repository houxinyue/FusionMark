## ADDED Requirements

### Requirement: Storage provider selection
The system SHALL select artifact persistence behavior through a configured storage provider so business logic does not depend directly on filesystem or MinIO SDK calls.

#### Scenario: Local provider is selected
- **WHEN** `STORAGE_PROVIDER=local`
- **THEN** task artifacts are persisted through the local storage provider

#### Scenario: MinIO provider is selected
- **WHEN** `STORAGE_PROVIDER=minio`
- **THEN** task artifacts are persisted through the MinIO storage provider

---

### Requirement: MinerU extracted artifacts are persisted without zip archive duplication
The system SHALL persist MinerU extracted outputs using business task ID based object keys and SHALL not require the original zip archive to be retained.

#### Scenario: Persist MinerU extracted outputs
- **WHEN** a MinerU task finishes and extracted files are available
- **THEN** the system stores extracted artifacts under the business task ID namespace
- **AND** extracted files preserve their current relative structure where applicable

#### Scenario: Zip archive is not required
- **WHEN** extracted MinerU outputs already exist
- **THEN** the system does not need to persist the original zip archive as a required stored artifact

---

### Requirement: LangExtract artifact persistence is configurable
The system SHALL allow LangExtract artifact persistence to be controlled by environment variables.

#### Scenario: Store base LangExtract artifacts
- **WHEN** `STORE_LANGEXTRACT_ARTIFACTS=true`
- **THEN** the system stores LangExtract JSONL, HTML visualization, and entity summary artifacts

#### Scenario: Skip verbose LangExtract artifacts by default
- **WHEN** `STORE_LANGEXTRACT_VERBOSE_ARTIFACTS=false`
- **THEN** the system does not persist optional verbose request/response artifacts

#### Scenario: Store verbose LangExtract artifacts when enabled
- **WHEN** `STORE_LANGEXTRACT_VERBOSE_ARTIFACTS=true`
- **THEN** the system persists verbose request/response artifacts when available

---

### Requirement: Task result includes object references
The system SHALL include object storage references in task results so artifacts can be tracked independently from local filesystem paths.

#### Scenario: Completed task returns object keys
- **WHEN** a task completes successfully and artifacts were stored
- **THEN** the task result includes object-key references for persisted artifacts
