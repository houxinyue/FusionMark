## ADDED Requirements

### Requirement: Visual token foundation
The web-pc frontend SHALL define a reusable visual token foundation for brand colors, system stage colors, semantic state colors, neutral surfaces, borders, shadows, glows, radii, spacing, and typography.

#### Scenario: Components consume visual tokens
- **WHEN** a web-pc component needs a color, surface, shadow, border, radius, spacing, or font size
- **THEN** it uses a project visual token instead of introducing an unrelated raw value

#### Scenario: Existing variables remain compatible
- **WHEN** existing component styles still reference current variables such as `--klein-blue`, `--hermes-orange`, `--bg-primary`, or `--text-primary`
- **THEN** those aliases remain available or are migrated in the same implementation change

### Requirement: Rich but role-bound color system
The web-pc frontend SHALL provide a richer color system where every saturated color has a defined product role.

#### Scenario: Brand colors are used for product identity
- **WHEN** the UI renders FusionMark identity, ambient workbench lighting, or brand background elements
- **THEN** it uses the brand blue/cyan range

#### Scenario: Operation buttons are separated from blue background
- **WHEN** the UI renders primary operation buttons such as starting processing or choosing a file
- **THEN** it uses teal operation styling instead of primary blue

#### Scenario: Accent colors are used for strong outcomes
- **WHEN** the UI renders downloads, completed output, or important result-oriented actions
- **THEN** it uses orange or gold accents instead of generic primary blue

#### Scenario: System stage colors map to pipeline stages
- **WHEN** the UI renders MinerU parsing, LangExtract extraction, or highlight rendering states
- **THEN** MinerU uses teal, LangExtract uses violet, and highlight rendering uses orange or gold

#### Scenario: Error and warning colors stay distinct
- **WHEN** the UI renders warnings, failures, or invalid states
- **THEN** those states use semantic warning or danger tokens and are not represented only by brand colors

### Requirement: Planet empty and entry state
The PDF preview SHALL retain a planet/space motif as a FusionMark brand element only when it does not compete with PDF reading.

#### Scenario: Empty PDF preview renders planet motif
- **WHEN** no PDF URL is loaded in `PdfViewer`
- **THEN** the empty state displays the planet motif instead of replacing it with a document-scan-only illustration
- **AND** visible orbit lines are not rendered

#### Scenario: Loaded PDF hides planet motif
- **WHEN** a PDF URL is loaded in `PdfViewer`
- **THEN** the planet motif and related animation are not rendered over or behind the active PDF reading area

#### Scenario: Optional entry animation is separate from reading state
- **WHEN** an entry animation is implemented
- **THEN** it completes before or outside the active PDF reading state
- **AND** it does not continue animating while the user is reading a loaded PDF

#### Scenario: Planet colors communicate pipeline meaning
- **WHEN** the planet motif is rendered
- **THEN** the center planet represents the FusionMark engine with blue/cyan styling
- **AND** nearby satellites or light points use stage colors for MinerU, LangExtract, and highlight/output roles

#### Scenario: Planet animation remains restrained
- **WHEN** the planet animation is visible
- **THEN** the animation uses restrained drifting motion because it is a temporary empty or entry-state brand expression

### Requirement: Naive UI theme alignment
The web-pc frontend SHALL align Naive UI theme overrides with the same visual foundation used by custom CSS components.

#### Scenario: Native controls match custom controls
- **WHEN** Naive UI buttons, inputs, dialogs, tags, progress indicators, or cards render
- **THEN** their colors, border radii, borders, and surfaces visually match the custom FusionMark components

#### Scenario: Theme overrides are centrally maintained
- **WHEN** theme override values are updated
- **THEN** they are maintained in a centralized theme module or equivalent centralized location rather than being scattered across page components

### Requirement: Workbench surface hierarchy
The web-pc frontend SHALL present the main UI as a dense document-analysis workbench with clear surface hierarchy.

#### Scenario: Process page uses workbench hierarchy
- **WHEN** the user opens the main PDF processing page
- **THEN** the left operation panel, right PDF preview panel, toolbar, and nested cards have distinct but consistent surfaces

#### Scenario: Background supports readability
- **WHEN** the user views the workbench for extended periods
- **THEN** the background uses restrained dark surfaces and subtle visual texture without decorative elements that reduce text or PDF readability

### Requirement: Entity highlight palette
The web-pc frontend SHALL keep entity highlight colors softer than global brand and stage colors.

#### Scenario: Entity tags use document annotation colors
- **WHEN** entity tags, modal items, or extracted entity categories are rendered
- **THEN** they use muted entity colors suitable for repeated document annotation

#### Scenario: Entity colors do not override system state colors
- **WHEN** entity categories and task states appear in the same view
- **THEN** task state colors remain visually distinguishable from entity highlight colors

### Requirement: Visual validation
The visual foundation implementation SHALL be validated by build checks and viewport inspection.

#### Scenario: Frontend build passes
- **WHEN** the visual foundation implementation is complete
- **THEN** `pnpm build` succeeds in `web-pc`

#### Scenario: Desktop viewport inspection passes
- **WHEN** the main processing page is inspected at common desktop widths
- **THEN** text, panels, toolbar controls, progress elements, empty state, and PDF preview area do not overlap or clip unexpectedly
