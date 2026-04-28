## 1. Visual Foundation

- [x] 1.1 Update `web-pc/src/styles/variables.css` with brand, system stage, semantic state, entity, neutral surface, glow, shadow, radius, and typography tokens.
- [x] 1.2 Preserve backward-compatible aliases for existing variables currently used by components.
- [x] 1.3 Update `web-pc/src/styles/main.css` so the application background uses the new workbench surface tokens.
- [x] 1.4 Update `web-pc/src/styles/animations.css` so skeleton, shimmer, scan, and orbit-related effects use the new token roles.

## 2. Theme Integration

- [x] 2.1 Create a centralized Naive UI theme override module for shared component colors, surfaces, borders, radii, operation button colors, and state colors.
- [x] 2.2 Update `web-pc/src/App.vue` to consume the centralized theme module instead of inline theme overrides.
- [x] 2.3 Confirm Naive UI primary, warning, error, success, input, button, modal, and tag styles align with the CSS token palette.

## 3. Component Visual Application

- [x] 3.1 Update `ProcessPdfView.vue` panel surfaces and layout background to the new document-analysis workbench hierarchy.
- [x] 3.2 Update `AppHeader.vue` and `AppFooter.vue` to use the new navigation, border, and surface tokens.
- [x] 3.3 Update `PdfUpload.vue` and `UrlSubmit.vue` so upload and URL actions use brand/focus tokens and richer but restrained interaction states.
- [x] 3.4 Update `ProgressCard.vue`, `StageList.vue`, and `ProgressLogs.vue` so MinerU, LangExtract, highlight rendering, pending, completed, warning, and failed states use the defined semantic colors.
- [x] 3.5 Update `PdfToolbar.vue` and `PdfViewer.vue` so the PDF workbench, toolbar, canvas shadow, and loading states follow the new surface hierarchy.
- [x] 3.6 Preserve and refine the `PdfViewer.vue` planet empty state without visible orbit lines, mapping center planet and nearby satellites/light points to FusionMark, MinerU, LangExtract, and highlight/output roles.
- [x] 3.7 Ensure `PdfViewer.vue` hides or unmounts the planet motif whenever a PDF is loaded or the user is in the active PDF reading state.
- [x] 3.8 If an entry animation is added, keep it short-lived and separate from the active PDF reading state.
- [x] 3.9 Update `EntityTraceButton.vue`, `EntityModal.vue`, and `entityColors.ts` so entity highlight colors remain muted and distinguishable from global state colors.
- [x] 3.10 Update `TaskHistoryView.vue` and `ConfigView.vue` placeholder layouts so they share the same visual foundation as the main workbench.

## 4. Validation

- [x] 4.1 Run `pnpm build` in `web-pc`.
- [ ] 4.2 Inspect the main processing page at desktop widths including 1920px, 1366px, and 1024px.
- [x] 4.3 Verify the PDF empty state still shows the planet motif without visible orbit lines when no PDF is loaded.
- [x] 4.4 Verify the planet motif is hidden or unmounted when a PDF is loaded and does not animate during active PDF reading.
- [x] 4.5 Verify progress stages are distinguishable by role and do not rely on blue/orange alone.
- [x] 4.6 Verify entity colors remain readable on dark surfaces and do not conflict with task state colors.
- [ ] 4.7 Verify no text, buttons, toolbar controls, cards, modals, or empty-state elements overlap or clip unexpectedly.
