## ADDED Requirements

### Requirement: Logo-aligned light UI palette
The web-pc frontend SHALL use a light document-centric palette aligned with the logo SVG colors as the v0 UI palette baseline.

#### Scenario: Brand accent is orange
- **WHEN** the UI renders primary actions, current scan states, selected navigation, progress emphasis, or highlight-related accents
- **THEN** it uses the orange accent family derived from `#f97316` and `#fb923c`

#### Scenario: Surfaces are deep blue-gray
- **WHEN** the UI renders app background, panels, rails, toolbars, and elevated workbench areas
- **THEN** it uses deep blue-gray surfaces derived from `#0f172a`, `#111827`, `#1e293b`, and `#273449`

#### Scenario: Non-brand colors are role-bound
- **WHEN** saturated colors appear outside the orange brand accent
- **THEN** they are limited to semantic success, warning, danger, or muted entity annotation roles

#### Scenario: Main surfaces are white or near-white
- **WHEN** the UI renders app background, panels, rails, toolbars, and elevated workbench areas
- **THEN** it uses white and near-white surfaces with gray-blue borders

#### Scenario: Text is gray-blue
- **WHEN** labels, body text, headings, hints, and toolbar metadata render
- **THEN** they use gray-blue text colors rather than pure black or dark-console colors

### Requirement: v0 document workbench layout
The main PDF processing page SHALL present a dense document-analysis workbench.

#### Scenario: Desktop layout prioritizes PDF preview
- **WHEN** the main route renders on a desktop viewport
- **THEN** the page is organized into a left input rail, central PDF preview canvas, and right inspection/status rail
- **AND** the central PDF preview remains the dominant visual area

#### Scenario: Small desktop layout remains usable
- **WHEN** the viewport width is constrained
- **THEN** the layout collapses without text, controls, or panels overlapping

### Requirement: v0 visual density
The web-pc frontend SHALL reduce decorative dashboard styling and use compact tool-like controls.

#### Scenario: Component radii are compact
- **WHEN** panels, buttons, inputs, cards, tags, and toolbar controls render
- **THEN** their border radii are compact and consistent with a workbench UI

#### Scenario: Effects are restrained
- **WHEN** shadows, glows, animations, or gradients render
- **THEN** they support scanning/highlighting states and do not dominate the page background

#### Scenario: Clickable controls do not use scan animation
- **WHEN** buttons, navigation links, upload controls, or other clickable controls render
- **THEN** they do not show animated scan-line effects

### Requirement: Theme and custom CSS alignment
Naive UI components SHALL visually align with custom CSS components.

#### Scenario: Native controls match v0 tokens
- **WHEN** Naive UI buttons, inputs, cards, modals, tags, or common controls render
- **THEN** their colors, borders, focus states, radii, and surfaces match the v0 token system

### Requirement: Build validation
The v0 redesign SHALL pass the frontend production build.

#### Scenario: Frontend build passes
- **WHEN** implementation is complete
- **THEN** `pnpm build` succeeds in `web-pc`
