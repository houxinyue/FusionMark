# agent-copilot-application Specification

## Purpose
TBD - created by archiving change standalone-agent-copilot-app. Update Purpose after archive.
## Requirements
### Requirement: Standalone copilot application root
The system SHALL provide a standalone `agent-copilot/` application root at the repository level for the intelligent assistant module.

#### Scenario: Root directory exists
- **WHEN** a developer inspects the repository
- **THEN** the `agent-copilot/` directory SHALL exist as a separate application boundary
- **AND** the module SHALL not be nested inside the main `services/` tree

### Requirement: Independent startup entrypoint
The system SHALL provide a minimal application entrypoint so the copilot module can be launched independently.

#### Scenario: App starts with uv
- **WHEN** a developer runs the copilot app entry command
- **THEN** the application SHALL start from the standalone module entrypoint
- **AND** the entrypoint SHALL be runnable with `uv`

### Requirement: Modular package layout
The system SHALL organize the copilot module into separate packages for transport, orchestration, agent logic, storage, schemas, models, config, prompts, and utilities.

#### Scenario: Modules import cleanly
- **WHEN** the package structure is created
- **THEN** each package SHALL be importable without circular dependency errors
- **AND** the module layout SHALL support later replacement of storage and model backends

### Requirement: Prompt assets are file-based
The system SHALL store copilot prompt assets as files under the module prompt directory instead of embedding long prompts in code.

#### Scenario: Prompts can be versioned
- **WHEN** prompt text changes
- **THEN** the change SHALL be captured through file-based assets
- **AND** the module SHALL keep prompt content separate from orchestration logic

### Requirement: Runtime boundaries remain isolated
The system SHALL keep the standalone copilot module isolated from the main profile management workflow during the scaffold stage.

#### Scenario: Existing profile workflow remains intact
- **WHEN** the copilot scaffold is introduced
- **THEN** the current profile save and activate flow SHALL continue to work unchanged
- **AND** the new module SHALL not replace the existing profile UI or storage logic in this stage

