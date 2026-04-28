# Tasks

## 1. Design
- [x] Confirm favicon-based palette and v0 workbench direction
- [x] Define affected frontend files
- [x] Create OpenSpec proposal and tasks
- [x] Validate OpenSpec

## 2. Implementation
- [x] Update CSS design tokens and global page background
- [x] Align Naive UI theme overrides to orange scan/highlight primary
- [x] Rework header navigation and brand treatment
- [x] Rebuild `ProcessPdfView` as a three-zone workbench
- [x] Restyle upload, URL, progress, stage, logs, PDF toolbar/viewer, and entity action components for v0
- [x] Align history/config visual shells with the v0 workbench
- [x] Switch v0 from dark workbench to light document-centric theme: white surfaces, gray-blue text, orange actions
- [x] Remove scan animation from clickable controls
- [x] Replace browser favicon with a compact static SVG optimized for tab display
- [x] Increase Header FusionMark logo display size
- [x] Replace PDF empty-state scan document with a restrained orbit motif
- [x] Add independent `fusion_mark_orbit_core.svg` asset for PDF empty-state center mark

## 3. Validation
- [x] Run initial `pnpm build` in `web-pc` before later visual tweaks
- [x] Re-run `pnpm build` after final favicon/orbit asset tweaks
- [ ] Inspect main layout for overflow/clipping at desktop width

## 4. Current Notes
- [x] Dev server is reachable at `http://127.0.0.1:5173`
- [x] `openspec.cmd validate web-pc-ui-v0-redesign` passed after light theme updates
- [ ] Final commit/push pending user approval
