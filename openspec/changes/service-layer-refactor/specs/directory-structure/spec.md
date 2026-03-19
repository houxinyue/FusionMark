## ADDED Requirements

### Requirement: Services directory structure
The system SHALL organize all backend Python service files under a unified `services/` directory with clear sub-directory categorization.

#### Scenario: Navigate to API layer
- **WHEN** developer needs to modify API endpoints
- **THEN** all API-related files are located in `services/api/`

#### Scenario: Navigate to core business logic
- **WHEN** developer needs to modify business logic
- **THEN** all core service files are located in `services/core/`

#### Scenario: Navigate to third-party clients
- **WHEN** developer needs to modify external API integrations
- **THEN** all client files are located in `services/clients/`

---

### Requirement: Import path updates
All internal module imports SHALL be updated to reflect the new directory structure using absolute or relative imports.

#### Scenario: Import from core module
- **WHEN** api/server.py needs to import FullPipelineService
- **THEN** it uses `from ..core.full_pipeline import FullPipelineService`

#### Scenario: Import from clients module
- **WHEN** core service needs to import MinerUClient
- **THEN** it uses `from ..clients.mineru import MinerUClient`

#### Scenario: Import from utils module
- **WHEN** any service needs to import MarkdownRenderer
- **THEN** it uses `from ..utils.renderer import MarkdownRenderer`

---

### Requirement: Legacy code isolation
Deprecated Celery-related code SHALL be moved to `services/legacy/` directory to clearly indicate its status.

#### Scenario: Identify deprecated code
- **WHEN** developer sees `services/legacy/` directory
- **THEN** they understand these files are scheduled for removal

---

## MODIFIED Requirements

### Requirement: Project documentation
All project documentation SHALL be updated to reference the new file paths.

#### Scenario: Read README.md
- **WHEN** new developer reads README.md
- **THEN** all file paths point to `services/` directory
- **AND** startup commands reference `services/start.py`

#### Scenario: Read AGENTS.md
- **WHEN** AI agent reads AGENTS.md
- **THEN** project structure description matches the new layout

#### Scenario: Read architecture docs
- **WHEN** developer reads docs/*.md files
- **THEN** all code references use the new file paths

---

### Requirement: Service startup
The service startup process SHALL work with the new directory structure.

#### Scenario: Start development server
- **WHEN** developer runs `python services/start.py`
- **THEN** FastAPI server starts successfully
- **AND** all modules are imported correctly

#### Scenario: Module execution
- **WHEN** developer runs `python -m services.start`
- **THEN** server starts successfully using module syntax

---

## RENAMED Requirements

### Requirement: File naming convention
Service files SHALL follow simplified naming without redundant `_service` suffix within context-aware directories.

| Old Path | New Path | Rationale |
|----------|----------|-----------|
| `api_server.py` | `services/api/server.py` | Directory provides context |
| `full_pipeline_service.py` | `services/core/full_pipeline.py` | Directory provides context |
| `md_highlight_service.py` | `services/core/highlight.py` | Simplified name |
| `md_highlight_pipeline.py` | `services/pipelines/highlight.py` | Simplified name |
| `md_renderer.py` | `services/utils/renderer.py` | Simplified name |
| `mineru_client.py` | `services/clients/mineru.py` | Simplified name |
| `start_server.py` | `services/start.py` | Simplified name |

#### Scenario: Import full pipeline service
- **WHEN** importing from old location `full_pipeline_service`
- **THEN** new import is `services.core.full_pipeline`

#### Scenario: Import highlight service
- **WHEN** importing from old location `md_highlight_service`
- **THEN** new import is `services.core.highlight`
