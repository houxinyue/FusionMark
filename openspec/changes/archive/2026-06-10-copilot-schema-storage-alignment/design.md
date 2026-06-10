## Context

`agent-copilot` currently has a standalone module structure and persistence boundary with in-memory, Redis, and MinIO implementations. The current domain model is intentionally small:

- `CopilotMessage` stores `role`, `content`, and `created_at`.
- `CopilotCheckpoint` stores checkpoint identity, parent identity, message snapshots, and `created_at`.
- `CopilotSession` stores session identity, user identity, messages, checkpoints, `current_step`, and timestamps.
- Redis stores serialized sessions at `agent-copilot:session:{session_id}` and serialized checkpoints in `agent-copilot:session:{session_id}:checkpoints`.
- MinIO stores archive JSON at `{prefix}/{project}/{env}/agent/{user_id}/session/{session_id}.json`.

The next copilot phase needs to persist more than raw chat messages. The conversation system must keep the current draft profile, validation result, pending user confirmation action, and agent trace metadata in the same Redis / MinIO persistence model.

## Goals / Non-Goals

**Goals:**

- Extend the existing session, message, checkpoint, and archive schemas for copilot conversation intelligence state.
- Keep existing Redis key patterns unchanged.
- Keep existing MinIO object path unchanged.
- Preserve backward-compatible reads for existing schema `1.0` payloads.
- Add tests that make the storage contract explicit.

**Non-Goals:**

- Implement HTTP APIs for conversations.
- Implement `ConversationOrchestrator`.
- Implement LLM-backed draft generation or intent classification.
- Implement LangGraph.
- Change profile save / activate behavior in the main application.
- Migrate existing Redis or MinIO data in place.

## Decisions

### Decision 1: Evolve schema through the serialization boundary

The change SHALL update dataclasses and `app/storage/serialization.py` together. Redis and MinIO adapters already depend on serialization helpers, so this keeps persistence changes centralized.

Alternative considered: update Redis and MinIO adapters directly. This would duplicate payload knowledge and make future schema changes harder to review.

### Decision 2: Preserve Redis key patterns

The Redis session key remains:

```text
agent-copilot:session:{session_id}
```

The Redis checkpoint key remains:

```text
agent-copilot:session:{session_id}:checkpoints
```

Only the JSON payload evolves. This avoids data location churn and keeps existing store tests meaningful.

### Decision 3: Add structured fields instead of embedding JSON in message text

Draft profiles, validation results, pending actions, and trace metadata SHALL be modeled as structured optional dictionaries on session/checkpoint objects.

Alternative considered: store all extra state in assistant message content as JSON blocks. That makes recovery brittle, forces natural-language parsing, and couples UI rendering to backend state.

### Decision 4: Keep schema `1.0` readable

`session_from_dict`, `message_from_dict`, and `checkpoint_from_dict` SHALL supply defaults when older payloads omit new fields. New writes will use schema `1.1`, but old test fixtures or Redis entries should still load.

Alternative considered: require a migration command before using new code. That is unnecessary for additive optional fields and raises rollout risk.

### Decision 5: Store trace metadata as summaries, not raw prompt content

`agent_trace` SHALL support intent, node, model, prompt version, context sources, input/output summaries, and latency. It SHALL NOT store secrets, API keys, or full prompt text.

Alternative considered: archive full prompts and full model inputs for reproducibility. That increases leakage risk and archive size. Prompt version plus summaries are enough for this phase.

## Risks / Trade-offs

- [Risk] Optional dictionaries become inconsistent across nodes. → Mitigation: define expected keys in tests and docs, and keep node-specific validation in later orchestrator work.
- [Risk] Archive payloads grow too large. → Mitigation: checkpoint only at key business transitions and store trace summaries instead of full prompts.
- [Risk] Legacy payload compatibility misses a field. → Mitigation: add tests for minimal schema `1.0` message, checkpoint, and session payloads.
- [Risk] Schema `1.1` fields are added before Orchestrator exists. → Mitigation: keep them optional and test only storage/serialization behavior in this change.

## Migration Plan

1. Update dataclasses with optional fields and default values.
2. Update serialization helpers to emit schema `1.1`.
3. Update deserialization helpers to read both `1.0` and `1.1` payloads.
4. Update persistence checkpoint creation to populate `step` at minimum from `session.current_step`.
5. Update archive payload to include current draft, pending action, validation result, and enriched checkpoints.
6. Add tests for new round trips and legacy reads.
7. Run `uv run pytest` in `agent-copilot`.

Rollback strategy:

- Revert the code change if tests or runtime validation fail.
- Since Redis keys and MinIO paths are unchanged and new fields are additive, rollback does not require a key migration.

## Open Questions

- The exact `draft_profile` shape will be finalized when `ConversationOrchestrator` and config validation are implemented.
- The exact `agent_trace` vocabulary may grow with LLM provider integration.
- Whether `current_draft` should eventually become a typed dataclass instead of a dictionary should be revisited after the first working draft generation flow.
