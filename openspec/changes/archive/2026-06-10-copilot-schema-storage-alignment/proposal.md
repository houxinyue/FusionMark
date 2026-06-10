## Why

`agent-copilot` already has a standalone application boundary and basic Redis / MinIO persistence adapters, but the current session, message, checkpoint, and archive schemas only store a minimal message snapshot. The next implementation phase needs explicit fields for draft profiles, validation results, pending confirmation actions, and agent trace metadata so the copilot conversation can be recovered from Redis and replayed from MinIO without inventing a parallel memory model.

## What Changes

- Extend the copilot domain models to carry conversation intelligence state:
  - message type and metadata on `CopilotMessage`
  - step, draft profile, validation result, pending action, and trace data on `CopilotCheckpoint`
  - current draft, pending action, and last validation result on `CopilotSession`
- Upgrade copilot serialization schema from `1.0` to `1.1`.
- Preserve backward-compatible reads for existing `1.0` session, message, and checkpoint payloads.
- Update Redis-backed session and checkpoint persistence through the existing serialization boundary, without changing Redis key patterns.
- Update MinIO archive payloads to include the new conversation replay fields.
- Add focused tests for schema round trips, legacy payload compatibility, checkpoint enrichment, and archive payload content.
- Update documentation references where needed.

No Redis key migration, MinIO object path change, HTTP API implementation, LLM generation, or LangGraph implementation is included in this change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `agent-copilot-application`: Extend the standalone copilot application contract so runtime session state, checkpoint snapshots, and MinIO archives can represent draft profile state, validation results, pending user-confirmed actions, and agent execution trace metadata.

## Impact

- Affected code:
  - `agent-copilot/app/models/session.py`
  - `agent-copilot/app/storage/serialization.py`
  - `agent-copilot/app/storage/persistence.py`
  - existing Redis / MinIO adapters indirectly through serialization output
  - `agent-copilot/tests/`
- Affected data contracts:
  - Redis session JSON payload remains at `agent-copilot:session:{session_id}` but gains schema `1.1` fields.
  - Redis checkpoint ZSET remains at `agent-copilot:session:{session_id}:checkpoints` but each JSON member gains schema `1.1` fields.
  - MinIO object path remains unchanged but archive JSON gains replay fields.
- Dependencies:
  - No new runtime dependency expected.
- Risks:
  - Legacy payload compatibility can break if defaults are not handled carefully.
  - Archive payload growth should stay bounded by existing message and checkpoint strategy.
