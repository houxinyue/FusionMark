## ADDED Requirements

### Requirement: Copilot session management
The system SHALL provide Profile Config Copilot sessions scoped to the resolved current user.

#### Scenario: Create session
- **WHEN** the frontend requests a new Copilot session
- **THEN** the backend SHALL create a session with a stable session ID
- **AND** the session SHALL be associated with the resolved current user

#### Scenario: Read session
- **WHEN** the frontend requests an existing Copilot session
- **THEN** the backend SHALL return the session messages, current draft, validation result, and referenced profiles

### Requirement: Profile-only guardrails
The Copilot SHALL only handle Fusion-Mark Profile YAML configuration tasks.

#### Scenario: Profile configuration request is accepted
- **WHEN** the user asks to create or modify a Fusion-Mark highlighting Profile
- **THEN** the Copilot SHALL process the message and attempt to produce or refine a draft

#### Scenario: Out-of-scope request is rejected
- **WHEN** the user asks for unrelated information, system command execution, arbitrary file access, application code changes, or Profile deletion
- **THEN** the Copilot SHALL reject the request
- **AND** the Copilot SHALL NOT call generation or persistence operations for that request

### Requirement: Profile context retrieval
The Copilot SHALL use existing user profiles as optional context for draft generation.

#### Scenario: Existing profiles are available
- **WHEN** the Copilot processes a configuration request
- **THEN** it SHALL retrieve candidate profiles through `ProfileManager`
- **AND** it SHALL summarize relevant profile metadata and configuration fields for generation context

#### Scenario: No profiles are available
- **WHEN** no existing profiles can be used as context
- **THEN** the Copilot SHALL still attempt generation from the user's request and the default Profile schema expectations

### Requirement: YAML draft generation
The Copilot SHALL generate raw YAML drafts for Fusion-Mark Profile configuration without persisting them automatically.

#### Scenario: Draft is generated
- **WHEN** the user sends an accepted configuration request
- **THEN** the Copilot SHALL return an assistant message and a raw YAML draft
- **AND** the Copilot SHALL include referenced profile summaries when context was used

#### Scenario: Model configuration is missing
- **WHEN** draft generation requires model credentials that are not configured
- **THEN** the backend SHALL return a clear configuration error
- **AND** it SHALL NOT return fabricated YAML as if it were model-generated

### Requirement: Draft validation
The Copilot SHALL validate generated or submitted drafts before marking them valid.

#### Scenario: Valid draft
- **WHEN** a draft parses as YAML with a mapping root and can construct `FullPipelineConfig`
- **THEN** the validation result SHALL be valid
- **AND** the frontend SHALL be able to apply the draft to the editor

#### Scenario: Invalid draft
- **WHEN** a draft is empty, malformed YAML, not a mapping, or incompatible with `FullPipelineConfig`
- **THEN** the validation result SHALL be invalid
- **AND** the response SHALL include structured validation errors

### Requirement: Manual application and persistence
The Copilot SHALL not save, overwrite, activate, or delete Profiles as part of chat message handling.

#### Scenario: User applies a draft
- **WHEN** the user clicks the frontend action to apply a Copilot draft
- **THEN** the frontend SHALL copy the draft YAML into the existing Profile editor state
- **AND** no backend Profile save or activate operation SHALL occur from that apply action

#### Scenario: User saves or activates after applying draft
- **WHEN** the user uses the existing Config page save or save-and-activate controls
- **THEN** the frontend SHALL use the existing Profile APIs
- **AND** the backend SHALL enforce the existing ProfileManager validation and persistence rules

