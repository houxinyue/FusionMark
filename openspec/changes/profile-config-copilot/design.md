## Context

Profile configuration is currently managed through `ProfileManager`, which stores raw YAML and metadata through `StorageProvider` and tracks the active profile through Redis. The frontend `ConfigView.vue` provides list/edit/save/activate workflows over that API.

The Copilot should sit beside that workflow rather than replacing it. Its output is a draft. The user remains responsible for applying the draft and triggering save or activation.

## Goals / Non-Goals

**Goals:**

- Provide a natural-language assistant for creating and refining Profile YAML drafts.
- Reuse existing profile context through `ProfileManager`.
- Preserve manual review before any persistent Profile change.
- Keep the backend modular and object-oriented.
- Validate every generated YAML draft before it is marked valid.
- Integrate into the existing Config page with minimal disruption.

**Non-Goals:**

- No Chroma, Ollama, or LangGraph in this stage.
- No automatic persistence side effects from a chat response.
- No PDF content inspection.
- No visual form editor for every YAML field.
- No deletion or file-system tooling exposed to the Copilot.

## Backend Design

Add a new package:

```text
services/copilot/
├── __init__.py
├── service.py
├── session_store.py
├── profile_context.py
├── draft_generator.py
├── draft_validator.py
├── guardrails.py
└── schemas.py
```

### Service responsibilities

`ProfileCopilotService` is the public orchestration class. It should:

1. Resolve or create a session.
2. Check the user's message with `CopilotGuardrails`.
3. Load lightweight context from existing profiles.
4. Ask `ProfileDraftGenerator` to create or modify a draft.
5. Validate the draft with `ProfileDraftValidator`.
6. Persist only session state, not Profile storage.
7. Return messages, draft YAML, validation status, and referenced profiles.

### Session storage

Stage 1 can use an in-memory session store with a narrow interface:

```python
class CopilotSessionStore:
    def create(self, user_id: str) -> CopilotSession: ...
    def get(self, session_id: str) -> CopilotSession: ...
    def save(self, session: CopilotSession) -> None: ...
```

The interface allows later replacement with Redis without changing API handlers.

Session data should include:

- `session_id`
- `user_id`
- `messages`
- `current_draft_yaml`
- `validation`
- `referenced_profiles`
- `created_at`
- `updated_at`

### Profile context

`ProfileContextProvider` should read profiles only through `ProfileManager`.

For each candidate profile, build a compact context summary from:

- `display_name`
- `description`
- `extraction_prompt`
- `category_colors.name`
- `category_colors.description`
- `examples.extractions.class`

Stage 1 may use deterministic keyword scoring instead of vector search.

### Draft generation

`ProfileDraftGenerator` should use an injectable model client boundary rather than hard-coding provider calls inside route handlers.

Recommended interface:

```python
class ProfileDraftGenerator:
    def generate(self, request: DraftGenerationRequest) -> DraftGenerationResult: ...
```

The generator prompt should instruct the model to:

- Produce YAML only for Fusion-Mark Profile configuration.
- Preserve supported keys.
- Prefer valid `FullPipelineConfig`-compatible structure.
- Use referenced profiles as examples, not as mandatory templates.
- Avoid secrets and do not invent API keys.

If no model credentials are configured, the service should return a clear configuration error instead of silently producing fake YAML.

### Validation

`ProfileDraftValidator` must:

1. Reject empty content.
2. Parse YAML with `yaml.safe_load`.
3. Require a mapping root.
4. Validate with `FullPipelineConfig.from_dict()`.
5. Return structured errors suitable for frontend display.

Validation must not rewrite raw YAML.

### Guardrails

Guardrails should be implemented with deterministic checks plus prompt-level instruction. The hard boundary is the available service methods, not model text.

Stage 1 should reject messages that clearly request:

- system command execution
- arbitrary file read/write
- deleting profiles
- unrelated information such as weather/news/general chat
- modifying application code

The rejection response should state that the Copilot only helps create or modify Fusion-Mark Profile YAML.

## API Design

Add routes under:

```text
/api/v1/profile-copilot
```

Suggested endpoints:

```http
POST /api/v1/profile-copilot/sessions
GET  /api/v1/profile-copilot/sessions/{session_id}
POST /api/v1/profile-copilot/sessions/{session_id}/messages
POST /api/v1/profile-copilot/sessions/{session_id}/validate
```

Stage 1 does not need save/activate Copilot endpoints because the frontend applies the draft to the existing editor and then uses current Profile APIs.

### Response shape

Message responses should include:

```json
{
  "session_id": "...",
  "assistant_message": "...",
  "draft_yaml": "...",
  "validation": {
    "valid": true,
    "errors": []
  },
  "referenced_profiles": [
    {
      "profile_id": "...",
      "display_name": "...",
      "description": "..."
    }
  ],
  "rejected": false
}
```

## Frontend Design

Add:

```text
web-pc/src/types/profileCopilot.ts
web-pc/src/api/profileCopilotApi.ts
web-pc/src/stores/profileCopilotStore.ts
web-pc/src/components/config/ProfileCopilotPanel.vue
```

`ProfileCopilotPanel.vue` should:

- Start a session on first use.
- Send user messages.
- Display assistant replies.
- Show validation status.
- Show referenced profiles.
- Preview the generated YAML draft.
- Provide an "apply to editor" action that writes to `profileStore.draftContent`.

The panel should not directly call save or activate. The existing Config page buttons remain the persistence controls.

## Risks / Trade-offs

| Risk | Mitigation |
| --- | --- |
| LLM outputs invalid YAML | Always validate and show structured errors before allowing users to apply confidently |
| Model credentials are missing | Return explicit backend error and keep UI in a recoverable state |
| Copilot bypasses Profile storage rules | Copilot only produces drafts; persistence remains through existing Profile APIs |
| In-memory sessions are lost on restart | Acceptable for stage 1; keep store interface replaceable |
| Keyword context retrieval is weaker than vector search | Keep context provider pluggable and add vector RAG in a later change |
| Frontend layout becomes crowded | Add a collapsible side panel or integrated right rail in Config page |

## Validation Plan

- Backend tests:
  - session creation
  - out-of-scope rejection
  - profile context extraction from existing profiles
  - draft validation success/failure
  - message endpoint returns draft and validation payload
- Frontend checks:
  - TypeScript/build validation
  - apply-to-editor behavior
  - validation error display
- Manual flow:
  - create draft for a finance/report profile
  - apply draft to editor
  - save as new Profile
  - save and activate through existing controls

