# Profile Config Copilot - Tasks

## 1. Backend Copilot Domain

- [x] 1.1 Add `services/copilot/` package and DTO/dataclass schemas
- [x] 1.2 Implement `CopilotSessionStore` with replaceable in-memory storage
- [x] 1.3 Implement `ProfileContextProvider` using `ProfileManager`
- [x] 1.4 Implement deterministic `CopilotGuardrails`
- [x] 1.5 Implement `ProfileDraftValidator` with YAML and `FullPipelineConfig` checks

## 2. Backend Draft Generation

- [x] 2.1 Add injectable `ProfileDraftGenerator` interface/class
- [x] 2.2 Implement OpenAI-compatible draft generation using existing environment/provider conventions
- [x] 2.3 Return explicit configuration errors when model credentials are unavailable
- [x] 2.4 Include referenced profile summaries in generation prompts
- [x] 2.5 Keep generated drafts raw and avoid YAML reformatting after validation

## 3. Backend API Integration

- [x] 3.1 Add `/api/v1/profile-copilot/sessions` create endpoint
- [x] 3.2 Add `/api/v1/profile-copilot/sessions/{session_id}` read endpoint
- [x] 3.3 Add `/api/v1/profile-copilot/sessions/{session_id}/messages` endpoint
- [x] 3.4 Add `/api/v1/profile-copilot/sessions/{session_id}/validate` endpoint
- [x] 3.5 Ensure endpoints resolve current user with existing `get_current_user_id()`
- [x] 3.6 Ensure Copilot endpoints do not save, activate, delete, or overwrite Profiles

## 4. Frontend API and State

- [x] 4.1 Add `web-pc/src/types/profileCopilot.ts`
- [x] 4.2 Add `web-pc/src/api/profileCopilotApi.ts`
- [x] 4.3 Add `web-pc/src/stores/profileCopilotStore.ts`
- [x] 4.4 Handle loading, error, rejected, validation, and draft states

## 5. Frontend Config Page Integration

- [x] 5.1 Add `ProfileCopilotPanel.vue`
- [x] 5.2 Integrate the panel into `ConfigView.vue`
- [x] 5.3 Display assistant messages, referenced profiles, validation status, and YAML draft preview
- [x] 5.4 Add "apply to editor" action that updates `profileStore.draftContent`
- [x] 5.5 Keep save and activate actions on existing Profile controls
- [x] 5.6 Ensure responsive layout remains usable on narrower screens

## 6. Validation

- [x] 6.1 Add backend tests for session store and guardrails
- [x] 6.2 Add backend tests for profile context extraction
- [x] 6.3 Add backend tests for draft validation
- [x] 6.4 Add backend API tests for session/message/validate endpoints
- [x] 6.5 Run `uv run pytest`
- [x] 6.6 Run frontend build/type checks according to `web-pc` scripts
- [x] 6.7 Manually verify generate, refine, apply, save, and activate flow
