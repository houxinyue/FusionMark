# Backend Service Directory Structure

## Purpose

Define the backend Python service layout so developers can navigate API, core logic, client integrations, utilities, and legacy code consistently.

## Requirements

### Requirement: Services Directory Organization

The system SHALL organize backend Python service files under the `services/` directory with clear sub-directory categorization.

#### Scenario: Navigate to API layer
- **WHEN** a developer needs to modify API endpoints
- **THEN** API-related files are located in `services/api/`

#### Scenario: Navigate to core business logic
- **WHEN** a developer needs to modify business logic
- **THEN** core service files are located in `services/core/`

#### Scenario: Navigate to third-party clients
- **WHEN** a developer needs to modify external API integrations
- **THEN** client files are located in `services/clients/`

### Requirement: Import Path Updates

The system SHALL use imports that match the `services/` package structure.

#### Scenario: Import from core module
- **WHEN** the API layer needs `FullPipelineService`
- **THEN** it imports the service from the core module path

#### Scenario: Import from clients module
- **WHEN** core logic needs `MinerUClient`
- **THEN** it imports the client from the clients module path

### Requirement: Legacy Code Isolation

Deprecated Celery-related code SHALL be isolated under `services/legacy/`.

#### Scenario: Identify deprecated code
- **WHEN** a developer sees files in `services/legacy/`
- **THEN** they understand the files are deprecated and scheduled for removal or replacement

### Requirement: Documentation And Startup

Project documentation and startup commands SHALL reference the current backend service structure.

#### Scenario: Read project documentation
- **WHEN** a developer reads project docs
- **THEN** backend file paths and startup commands reference the `services/` layout

#### Scenario: Start development server
- **WHEN** a developer starts the backend service
- **THEN** FastAPI starts successfully and imports service modules correctly
