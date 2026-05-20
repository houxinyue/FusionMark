# frontend-engineering Specification

## Purpose
TBD - created by archiving change web-pc-vue-frontend. Update Purpose after archive.
## Requirements
### Requirement: Vue 3 SPA engineering scaffold
The system SHALL provide a production-grade Vue 3 + Vite + TypeScript frontend scaffold under `web-pc/` directory, managed by pnpm.

#### Scenario: Project initializes successfully
- **WHEN** developer runs `pnpm create vite web-pc --template vue-ts`
- **THEN** the scaffold is created with Vite, Vue 3, and TypeScript configured
- **AND** `pnpm install` installs all dependencies without errors

#### Scenario: Development server starts
- **WHEN** developer runs `pnpm dev`
- **THEN** the Vite dev server starts on port 5173
- **AND** the application loads without console errors

#### Scenario: Production build succeeds
- **WHEN** developer runs `pnpm build`
- **THEN** the build completes without type or syntax errors
- **AND** output is emitted to `dist/`

---

### Requirement: Naive UI dark theme integration
The system SHALL integrate Naive UI with a dark theme aligned to existing brand colors (Klein Blue #002FA7, Hermes Orange #FF6600).

#### Scenario: Dark theme renders correctly
- **WHEN** user opens the application
- **THEN** the UI renders in dark mode by default
- **AND** primary buttons and highlights use Klein Blue
- **AND** warning states use Hermes Orange

---

### Requirement: Modular directory structure
The system SHALL organize source code into modular directories: api, components, composables, constants, router, stores, styles, types, utils, views.

#### Scenario: All modules are importable
- **WHEN** developer imports from `@/api/taskApi` or `@/stores/taskStore`
- **THEN** the module resolves correctly via Vite path alias
- **AND** TypeScript intellisense works without errors

---

### Requirement: Backend API integration layer
The system SHALL provide an Axios-based HTTP client with interceptors and typed task API wrappers, plus a WebSocket composable for real-time progress.

#### Scenario: Task creation request
- **WHEN** user submits a PDF URL
- **THEN** `taskApi.createTask` sends a POST to `/api/v1/tasks`
- **AND** returns the task_id

#### Scenario: WebSocket progress streaming
- **WHEN** a task is created
- **THEN** `useTaskWebSocket` connects to `ws://host/ws/{taskId}`
- **AND** real-time progress updates are pushed to Pinia store

---

### Requirement: PDF.js preview rendering
The system SHALL provide a composable `usePdfViewer` that wraps pdfjs-dist for loading, rendering, zooming, and navigating PDF pages.

#### Scenario: PDF loads and renders
- **WHEN** user uploads or receives a PDF URL
- **THEN** `usePdfViewer.loadPdf` loads the document
- **AND** the first page renders on a canvas element
- **AND** rotation metadata is handled correctly

---

### Requirement: Vite dev proxy configuration
The system SHALL configure Vite proxy to forward `/api` and `/ws` to the backend during development.

#### Scenario: API requests forwarded
- **WHEN** frontend makes request to `/api/v1/tasks`
- **THEN** Vite proxies it to `http://localhost:8000/api/v1/tasks`

#### Scenario: WebSocket forwarded
- **WHEN** frontend connects to `/ws/{taskId}`
- **THEN** Vite proxies it to `ws://localhost:8000/ws/{taskId}`

