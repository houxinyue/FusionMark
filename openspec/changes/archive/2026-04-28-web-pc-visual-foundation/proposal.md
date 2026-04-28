## Why

`web-pc/` already has a dark Vue 3 workbench and basic Klein blue / Hermes orange styling, but the visual language is still scattered across component-level CSS. The next UI iteration needs a stable visual foundation so future pages, progress states, PDF preview, entity highlighting, and Naive UI components share one recognizable FusionMark design system.

The original visual plan should be adapted as a product UI baseline, not copied as pure decoration. The PDF empty state planet-orbit animation will be retained as a brand memory point, while the system color design will be expanded beyond the current two-color palette.

## What Changes

- Establish a richer `web-pc` color system with brand colors, system stage colors, semantic state colors, entity highlight colors, and neutral surface tokens.
- Keep the PDF empty state planet-orbit motif and redesign it as a FusionMark analysis-orbit symbol instead of replacing it with a document-scan-only empty state.
- Define how MinerU, LangExtract, highlight rendering, completion, warning, and failure states map to specific colors.
- Align Naive UI theme overrides with the project CSS variables so native components and custom components share one visual baseline.
- Define reusable surface, border, shadow, glow, and background rules for the workbench layout, side panel, PDF preview area, upload area, progress card, entity modal, history page, and config page.
- Provide implementation tasks that are style-system first and avoid business logic changes.

## Capabilities

### New Capabilities
- `web-pc-visual-foundation`: Defines the visual foundation for the Vue web-pc frontend, including design tokens, component theme mapping, PDF empty state motif, stage colors, entity colors, and validation requirements.

### Modified Capabilities
- None.

## Impact

- Affected frontend files:
  - `web-pc/src/styles/variables.css`
  - `web-pc/src/styles/main.css`
  - `web-pc/src/styles/animations.css`
  - `web-pc/src/App.vue`
  - `web-pc/src/constants/entityColors.ts`
  - `web-pc/src/views/ProcessPdfView.vue`
  - `web-pc/src/views/TaskHistoryView.vue`
  - `web-pc/src/views/ConfigView.vue`
  - `web-pc/src/components/layout/*`
  - `web-pc/src/components/upload/*`
  - `web-pc/src/components/progress/*`
  - `web-pc/src/components/pdf/*`
  - `web-pc/src/components/entity/*`
- No backend, API, WebSocket, PDF.js rendering contract, or data model changes.
- No new runtime dependency is required unless implementation later chooses an icon package; current scope can be completed with existing CSS and Naive UI.
