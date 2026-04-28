# Web-PC UI v0 Redesign

## Problem / Intent

The current `web-pc` UI already uses a dark technology style, but the visual language is spread across too many saturated hues. User feedback for v0 prefers a lighter document-centric theme: white primary surfaces, gray-blue text, and orange action colors that echo the logo SVG. The v0 redesign should make the app feel like a clean PDF review and annotation workbench rather than a dark control console.

## Scope

- Rework the `web-pc` design tokens around a light logo-aligned palette:
  - white and near-white document surfaces
  - gray-blue text and borders
  - orange primary highlight/action accent
  - restrained semantic colors
  - smaller radii and calmer shadows
- Align Naive UI overrides with the new token direction.
- Convert the main processing page into a v0 three-zone workbench:
  - left input rail
  - central PDF preview canvas
  - right inspection/status rail
- Restyle the header, upload zone, progress card, PDF toolbar/viewer, and placeholder pages to match the v0 direction.
- Keep the implementation CSS-first and avoid new runtime dependencies.
- Remove scan-line animation from clickable controls because it feels visually inconsistent in the light v0 theme.

## Out of Scope

- No backend changes.
- No API, WebSocket, task-store, or PDF.js contract changes.
- No new routes.
- No full history/config feature implementation beyond visual shell alignment.
- No final design-system polish beyond a working v0.

## Affected Modules

- `web-pc/src/styles/variables.css`
- `web-pc/src/styles/main.css`
- `web-pc/src/theme/naiveTheme.ts`
- `web-pc/src/components/layout/AppHeader.vue`
- `web-pc/src/views/ProcessPdfView.vue`
- `web-pc/src/components/upload/PdfUpload.vue`
- `web-pc/src/components/upload/UrlSubmit.vue`
- `web-pc/src/components/progress/ProgressCard.vue`
- `web-pc/src/components/progress/StageList.vue`
- `web-pc/src/components/progress/ProgressLogs.vue`
- `web-pc/src/components/pdf/PdfToolbar.vue`
- `web-pc/src/components/pdf/PdfViewer.vue`
- `web-pc/src/components/entity/EntityTraceButton.vue`
- `web-pc/src/views/TaskHistoryView.vue`
- `web-pc/src/views/ConfigView.vue`

## Architecture / Design Approach

### Design System

- Color palette:
  - page base: `#f8fafc`
  - paper surface: `#ffffff`
  - soft surface: `#f1f5f9`
  - elevated surface: `#e2e8f0`
  - primary accent: `#f97316`
  - soft accent: `#fb923c`
  - text primary: `#334155`
  - text secondary: `#475569`
  - text muted: `#64748b`
- Typography:
  - compact workbench hierarchy, 12-14px component text and 18-20px section titles.
- Spacing:
  - 8px base unit, denser panels than the previous card-heavy layout.
- Radius:
  - panels 8px, controls 6px, tags 4px or pill only for states.
- Shadow:
  - mostly border-led surfaces; orange shadows are subtle and limited to primary action/focus states.
- Motion:
  - restrained progress shimmer only where processing state is shown; no scan animation on clickable buttons or upload controls.

### Layout

The main processing page becomes a CSS grid workbench:

```text
header
left input rail | central PDF preview canvas | right inspect rail
```

At narrower widths, the layout collapses to two rows or one column while preserving PDF preview priority.

## Data or API Contract Changes

None.

## Risks

| Risk | Mitigation |
|---|---|
| Existing color-role semantics may be lost | Keep compatibility aliases and only reduce saturated visual usage |
| Three-column layout may compress on small screens | Add responsive grid breakpoints |
| v0 may not cover every component state | Keep changes scoped and validate build plus main viewport behavior |

## Validation Plan

- Run `pnpm build` in `web-pc`.
- Inspect the main route at desktop width.
- Verify header/navigation, upload rail, progress rail, PDF canvas, and placeholder pages render without obvious overflow.

## Rollback Plan

All changes are frontend style/layout changes. Roll back by reverting the commit or restoring the touched frontend files.
