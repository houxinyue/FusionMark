## 1. Domain Models

- [x] 1.1 Extend `CopilotMessage` with `message_type` and `metadata` optional state.
- [x] 1.2 Extend `CopilotCheckpoint` with `step`, `draft_profile`, `validation_result`, `pending_action`, and `agent_trace` optional state.
- [x] 1.3 Extend `CopilotSession` with `current_draft`, `pending_action`, and `last_validation_result` optional state.

## 2. Serialization

- [x] 2.1 Upgrade copilot serialization schema version to `1.1`.
- [x] 2.2 Update message, checkpoint, and session serialization to emit enriched fields.
- [x] 2.3 Update deserialization to read schema `1.0` payloads with default values for new fields.
- [x] 2.4 Update archive payload construction to include replay fields for session and checkpoints.

## 3. Persistence Boundary

- [x] 3.1 Update checkpoint creation to capture `session.current_step` as the checkpoint step.
- [x] 3.2 Confirm Redis session and checkpoint key patterns remain unchanged.
- [x] 3.3 Confirm MinIO archive object path remains unchanged.

## 4. Tests

- [x] 4.1 Add tests for enriched message, checkpoint, and session serialization round trips.
- [x] 4.2 Add tests for legacy schema `1.0` message, checkpoint, and session deserialization.
- [x] 4.3 Add tests for persistence boundary checkpoint step capture.
- [x] 4.4 Add tests for archive payload replay fields and summary counts.
- [x] 4.5 Run `uv run pytest` in `agent-copilot`.

## 5. Documentation and Review

- [x] 5.1 Update related documentation or README references if implementation details differ from the design document.
- [x] 5.2 Run `openspec validate --changes`.
- [x] 5.3 Review `git diff` for unintended changes or sensitive data.
