## ADDED Requirements

### Requirement: PDF orientation detection
The system SHALL detect PDF orientation metadata and determine if correction is needed before rendering.

#### Scenario: Normal oriented PDF requires no correction
- **WHEN** user uploads a PDF with correct orientation metadata
- **THEN** the system detects normal orientation
- **AND** renders the PDF without rotation

#### Scenario: Rotated PDF requires correction
- **WHEN** user uploads a PDF with rotated orientation metadata
- **THEN** the system detects incorrect orientation
- **AND** applies appropriate rotation correction

---

### Requirement: PDF preview rendering
The system SHALL render PDF preview with correct orientation using PDF.js configuration.

#### Scenario: PDF preview displays correctly
- **WHEN** user views PDF preview
- **THEN** the PDF displays in readable orientation
- **AND** rotation correction is applied if needed
