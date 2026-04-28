## ADDED Requirements

### Requirement: Skeleton loading state
The system SHALL provide a unified skeleton loading component and CSS animation for transition states before data arrives.

#### Scenario: Progress card shows skeleton on task submit
- **WHEN** user submits a PDF URL
- **AND** WebSocket has not yet returned the first progress update
- **THEN** the progress card area renders a skeleton placeholder with shimmer animation

#### Scenario: PDF viewer shows skeleton while loading
- **WHEN** a PDF URL is assigned to PdfViewer
- **AND** pdfjs-dist is still loading the document
- **THEN** the preview area shows a document-outline skeleton instead of blank space

---

### Requirement: Responsive breakpoint for left panel
The system SHALL adjust the ProcessPdfView layout at 1280px and 1024px breakpoints.

#### Scenario: Large desktop (1920px)
- **WHEN** viewport width is greater than 1280px
- **THEN** left panel remains 380px wide

#### Scenario: Small laptop (1366px)
- **WHEN** viewport width is between 1024px and 1280px
- **THEN** left panel narrows to 320px

#### Scenario: Tablet or split-screen (1024px)
- **WHEN** viewport width is less than 1024px
- **THEN** layout switches to single-column vertical stack

---

### Requirement: Business-themed empty state animation
The system SHALL replace the planet-orbit empty state animation with a document-scan animation that aligns with the PDF parsing business.

#### Scenario: Empty state displays document scan
- **WHEN** no PDF is loaded in the preview area
- **THEN** an animated document icon with a scanning line is displayed
- **AND** the animation loops smoothly

---

### Requirement: Softened progress bar shimmer
The system SHALL soften the progress bar shimmer effect by replacing white highlight with brand-color glow and adding blur.

#### Scenario: Progress bar renders softly
- **WHEN** progress bar is visible and processing
- **THEN** the shimmer animation uses klein-blue tinted light
- **AND** the edge is blurred for a softer visual

---

### Requirement: Entity tag hover interaction
The system SHALL provide hover feedback on entity tags including lift, shadow, and category dot indicator.

#### Scenario: User hovers over entity tag
- **WHEN** mouse enters an entity tag
- **THEN** the tag translates up by 2px
- **AND** a soft shadow appears beneath it

---

### Requirement: Font hierarchy system
The system SHALL define a consistent font size scale from display to tiny in CSS variables.

#### Scenario: Components use font variables
- **WHEN** any component defines font-size
- **THEN** it references `--font-h1`, `--font-body`, `--font-caption`, etc.
- **AND** no hardcoded pixel values are used for typography
