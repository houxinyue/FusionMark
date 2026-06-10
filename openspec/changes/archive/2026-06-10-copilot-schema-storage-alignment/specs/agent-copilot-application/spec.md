## ADDED Requirements

### Requirement: Copilot conversation state schema
The system SHALL represent copilot conversation intelligence state in the session persistence model, including message metadata, current draft profile state, validation result state, pending user confirmation action, and checkpoint trace metadata.

#### Scenario: Session serializes conversation state
- **WHEN** a copilot session contains a current draft, a pending action, and a last validation result
- **THEN** the serialized session payload SHALL include those fields
- **AND** the payload SHALL include schema version `1.1`

#### Scenario: Message serializes metadata
- **WHEN** a copilot message has a non-default message type or metadata
- **THEN** the serialized message payload SHALL preserve the message type and metadata

#### Scenario: Checkpoint serializes enriched snapshot
- **WHEN** a checkpoint is created with a step, draft profile, validation result, pending action, and agent trace
- **THEN** the serialized checkpoint payload SHALL preserve each of those fields

### Requirement: Legacy copilot payload compatibility
The system SHALL read existing copilot schema `1.0` session, message, and checkpoint payloads without requiring a Redis or MinIO migration.

#### Scenario: Legacy session payload loads
- **WHEN** a schema `1.0` session payload does not include current draft, pending action, or last validation result fields
- **THEN** deserialization SHALL still return a valid copilot session
- **AND** the missing fields SHALL default to `None`

#### Scenario: Legacy message payload loads
- **WHEN** a message payload does not include message type or metadata fields
- **THEN** deserialization SHALL still return a valid copilot message
- **AND** the message type SHALL default to `text`
- **AND** metadata SHALL default to `None`

#### Scenario: Legacy checkpoint payload loads
- **WHEN** a checkpoint payload does not include step, draft profile, validation result, pending action, or agent trace fields
- **THEN** deserialization SHALL still return a valid copilot checkpoint
- **AND** the missing optional fields SHALL default to `None`

### Requirement: Redis persistence preserves conversation state
The system SHALL preserve enriched copilot session and checkpoint fields through the existing Redis session and checkpoint storage boundaries without changing Redis key patterns.

#### Scenario: Redis session round trip preserves state
- **WHEN** an enriched copilot session is saved and loaded through the Redis session store
- **THEN** the loaded session SHALL preserve current draft, pending action, last validation result, message metadata, and current step
- **AND** the Redis session key pattern SHALL remain `agent-copilot:session:{session_id}`

#### Scenario: Redis checkpoint round trip preserves state
- **WHEN** an enriched checkpoint is saved and listed through the Redis checkpoint store
- **THEN** the listed checkpoint SHALL preserve step, draft profile, validation result, pending action, and agent trace
- **AND** the Redis checkpoint key pattern SHALL remain `agent-copilot:session:{session_id}:checkpoints`

### Requirement: MinIO archive payload supports conversation replay
The system SHALL include enriched copilot conversation state in MinIO archive payloads so a completed session can be replayed and audited.

#### Scenario: Archive payload includes replay fields
- **WHEN** a copilot session with enriched state and checkpoints is archived
- **THEN** the archive payload SHALL include current draft, pending action, last validation result, messages, checkpoints, current step, and summary counts
- **AND** each enriched checkpoint in the payload SHALL include step, draft profile, validation result, pending action, and agent trace

#### Scenario: MinIO object path remains stable
- **WHEN** a copilot session is archived to MinIO
- **THEN** the object path SHALL continue to use `{prefix}/{project}/{env}/agent/{user_id}/session/{session_id}.json`

### Requirement: Checkpoint creation captures session step
The system SHALL capture the current copilot session step when creating a checkpoint through the persistence boundary.

#### Scenario: Persistence boundary creates checkpoint with current step
- **WHEN** the persistence boundary creates a checkpoint for a session whose current step is `validating_profile`
- **THEN** the checkpoint SHALL record step `validating_profile`
- **AND** the checkpoint SHALL still preserve the session message snapshot
