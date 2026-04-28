# extraction-preview Specification

## Purpose
TBD - created by archiving change redis-entities-html-preview. Update Purpose after archive.
## Requirements
### Requirement: Task result includes extraction preview payloads
The system SHALL include extraction preview payloads in completed task results so the frontend can display actual extraction content without reading debug files from disk.

#### Scenario: Completed task returns structured entities
- **WHEN** a task finishes LangExtract processing successfully
- **THEN** the completed task result includes an `entities` array
- **AND** each entity includes extracted text and category
- **AND** character interval fields are included when available

#### Scenario: Completed task returns LangExtract HTML preview
- **WHEN** a task finishes LangExtract processing successfully
- **THEN** the completed task result includes `langextract_html`
- **AND** the HTML payload is directly renderable by the frontend entity preview area

---

### Requirement: Frontend entity preview prefers HTML and falls back safely
The frontend SHALL prefer rendering LangExtract HTML preview and fall back to structured entity data or summary counts when richer preview payloads are absent.

#### Scenario: Render HTML preview when available
- **WHEN** completed task result contains `langextract_html`
- **THEN** the entity preview panel renders that HTML content

#### Scenario: Fall back to structured entities
- **WHEN** `langextract_html` is absent and `entities` are present
- **THEN** the entity preview panel renders extracted entities from structured JSON

#### Scenario: Fall back to category counts
- **WHEN** both `langextract_html` and `entities` are absent
- **THEN** the entity preview panel still renders category count summary

---

### Requirement: JSONL debug artifact remains file-based
The system SHALL keep JSONL extraction export as a file-based debug artifact rather than storing raw JSONL text in Redis task result.

#### Scenario: JSONL export continues unchanged
- **WHEN** extraction debug export is enabled
- **THEN** the system still writes `extractions.jsonl` to disk
- **AND** Redis task result does not store the raw JSONL file text

