## Why

The current intelligent profile copilot work has a clear architecture direction, but it is still embedded conceptually inside the main project. That makes later iteration harder because storage, orchestration, prompts, and API concerns can drift into the main service tree.

We should first carve out a standalone module root for the agent copilot so the feature can evolve as an independently maintainable application. This matches the project preference for plugin-style, splitable code.

## What Changes

- Introduce a standalone `agent-copilot/` application root at the repository level.
- Define a clean internal package layout for API, core orchestration, agent logic, storage, config, models, schemas, prompts, and tests.
- Add a minimal startup entry so the module can be launched independently with `uv`.
- Establish the first implementation phase as a modular skeleton, not a full business rewrite.
- Split the remaining work into executable follow-up tasks for state storage, session handling, API exposure, and frontend integration.

## Out of Scope

- Full LangGraph orchestration.
- Redis/MinIO production wiring beyond the initial abstraction boundaries.
- Frontend integration changes.
- Replacing the existing profile management workflow.
- Large refactors in the main `services/` runtime.

## Impact

- New top-level application directory: `agent-copilot/`
- New package and script layout for the copilot app
- New tests for startup and package importability
- Future follow-up tasks will cover storage, API, and UI integration

## Risks

- The new module may overlap conceptually with existing profile copilot work if boundaries are not explicit.
- If the root scaffold is too thin, later implementation work may still leak into the main service tree.
- If the package layout is not standardized early, repeated rework will follow.

## Validation Plan

- Verify the new root directory is present and importable.
- Verify the app entrypoint starts with `uv`.
- Verify the skeleton layout is ready for later storage/API implementation.

## Rollback Plan

- Remove the new `agent-copilot/` directory and any related project wiring if the module direction is rejected before implementation.
- Keep the existing profile workflow unchanged during this stage.
