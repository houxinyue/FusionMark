## Why

Fusion-Mark profiles are powerful but difficult to author by hand. Users must understand the YAML shape, MinerU options, LangExtract prompts, category colors, examples, and rendering options before they can create a useful highlighting configuration.

The project already has storage-backed Profile management and a web configuration page. We need a first-stage Profile Config Copilot that helps users generate and refine YAML drafts through natural language while preserving the existing ProfileManager, StorageProvider, Redis active-profile state, and manual save/activate controls.

## What Changes

- Add a backend Profile Copilot service for creating and continuing draft-generation sessions.
- Generate Profile YAML drafts from user requirements and existing profile context.
- Validate drafts with YAML parsing and `FullPipelineConfig.from_dict()` before presenting them as usable.
- Add guardrails so the Copilot only handles Profile configuration tasks and cannot perform unrelated actions.
- Add REST APIs under `/api/v1/profile-copilot` for sessions, messages, and validation.
- Add a frontend Copilot panel on the existing Config page.
- Allow users to apply a generated draft to the existing YAML editor, then save or activate through the existing Profile workflow.

## Capabilities

### New Capabilities

- `profile-config-copilot`: Natural-language Profile YAML draft generation and refinement.

### Modified Capabilities

- `profile-management`: The existing Profile management UI gains a Copilot draft panel, but save/activate behavior remains owned by the current Profile APIs.

## Out of Scope

- Chroma vector database integration.
- Ollama embedding integration.
- LangGraph orchestration or checkpoint persistence.
- Automatic save, overwrite, activate, delete, or system-level operations by the Copilot.
- Reading uploaded PDF document contents as Copilot context.
- Authentication, RBAC, or multi-user UI changes.

## Impact

- Backend:
  - New `services/copilot/` package.
  - New API routes in `services/api/server.py` or a dedicated router included by the server.
  - Reuse of `services.profiles.ProfileManager` and `FullPipelineConfig` for context and validation.
  - New tests under `services/` or existing test conventions.
- Frontend:
  - New profile Copilot API/types/store/component under `web-pc/src/`.
  - Update `web-pc/src/views/ConfigView.vue` to include a Copilot panel.
- Dependencies:
  - No new vector database, embedding, or LangGraph dependency in stage 1.
  - Reuse the existing OpenAI-compatible LLM stack already available through current dependencies where practical.

