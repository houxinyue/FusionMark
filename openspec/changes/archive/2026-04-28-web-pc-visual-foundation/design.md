## Context

The current `web-pc` frontend is a Vue 3 + Vite + TypeScript application using Naive UI dark theme, custom CSS variables, and component-scoped styles. The existing visual baseline already contains Klein blue, Hermes orange, dark surfaces, Morandi entity colors, a left operation panel, a right PDF preview workbench, progress cards, and a planet-orbit empty state.

The visual upgrade should preserve the product-workbench nature of FusionMark. Users need to upload documents, monitor MinerU / LangExtract / highlight processing, inspect PDF output, trace entities, and download artifacts. The UI must remain readable and operationally dense, while gaining a richer color system and stronger identity.

## Goals / Non-Goals

**Goals:**
- Establish a reusable color-token system across brand, operation actions, system stages, semantic states, neutral surfaces, glows, and entity highlights.
- Preserve and refine the planet-orbit empty state as a FusionMark brand motif that appears only before a PDF is loaded, with optional use as an entry animation.
- Make processing stages visually distinct: MinerU, LangExtract, and highlight rendering should not all look like generic blue progress.
- Align Naive UI theme overrides with project CSS tokens.
- Keep the implementation mostly in `web-pc/src/styles`, `App.vue`, constants, and component style sections.
- Improve visual consistency without altering APIs, stores, routing, WebSocket behavior, or PDF.js rendering behavior.

**Non-Goals:**
- No backend or service changes.
- No change to task lifecycle, progress data contracts, PDF artifact URLs, or entity extraction output.
- No landing page redesign.
- No replacement of the planet-orbit empty state with a document-scan-only illustration.
- No broad component library migration.

## Decisions

### Decision 1: Use semantic token layers instead of raw component colors

Define color variables in layers:
- Brand: blue, cyan, orange, gold.
- System stages: MinerU teal, LangExtract violet, highlight orange, artifact gold.
- Semantic states: success, warning, danger, info, pending.
- Entity highlights: muted Morandi colors tuned for dark UI readability.
- Surface neutrals: page, panel, panel-strong, elevated, hover, border, divider.

Rationale: this keeps the palette rich but controlled. Components consume semantic variables instead of hardcoded hex values.

Alternative considered: only intensify the existing blue/orange palette. Rejected because it keeps MinerU, LangExtract, progress, and CTA states visually compressed into one dominant hue family.

### Decision 2: Preserve the planet motif only for empty/entry states

The PDF empty state SHALL retain the planet/space motif, but visible orbit lines should be omitted to keep a more restrained and mysterious feeling. The animation MUST be conditionally hidden once a PDF is loaded or being read. The motif can also be used as an entering-system opening animation before the workbench becomes active.

The motif colors and structure should communicate FusionMark processing:
- Center planet: FusionMark engine, blue/cyan gradient.
- MinerU satellite: teal.
- LangExtract satellite: violet.
- Highlight/output satellite: orange or gold.
- Ambient dust/light points: low-contrast neutral accents.

Rationale: the user explicitly wants to keep the orbit motif, and it can become a recognizable product identity if it is tied to the document-analysis pipeline. At the same time, animated branding must not compete with PDF reading; conditional rendering is clearer than merely lowering opacity.

Alternative considered: use visible orbit rings. Rejected because the user wants less explicit geometry and a more mysterious empty state.

### Decision 3: Use teal for operational buttons instead of blue

Primary Naive UI buttons should use teal as the main operation color. Brand blue remains in the background, logo, ambient light, and identity layer.

Rationale: the UI background already leans blue. Teal gives action controls better separation without introducing a palette that conflicts with MinerU/document parsing semantics. Orange/gold remains reserved for download, output, and result-oriented actions.

### Decision 4: Map stage visuals to the processing pipeline

Progress UI should use stage-specific visual accents:
- MinerU / document parsing: teal.
- LangExtract / semantic extraction: violet.
- Highlight rendering / PDF output: orange.
- Completed artifact: gold or success green depending on context.

Rationale: stage colors help users distinguish pipeline phases quickly, especially in a left-side operational panel.

### Decision 5: Keep entity highlight colors softer than system colors

Entity colors remain in the Morandi family and should not compete with brand or stage colors. Their role is document annotation, not global navigation or workflow state.

Rationale: entity colors appear many times in document previews and modals. High-saturation entity colors would reduce readability and create visual noise.

### Decision 6: Centralize Naive UI theme overrides

Move theme overrides out of `App.vue` into a small theme module such as `src/plugins/naiveTheme.ts` or `src/theme/naiveTheme.ts`.

Rationale: global component colors, border radii, modal surfaces, buttons, inputs, and tags should follow the same token decisions. A separate module makes future theme updates easier and avoids growing `App.vue`.

## Risks / Trade-offs

- Richer palette could look noisy -> mitigate by assigning every color a role and limiting high-saturation colors to actions, stage accents, and small emphasis elements.
- Component-scoped CSS may duplicate token usage -> mitigate by introducing shared variables and utility classes only where repeated patterns are clear.
- Naive UI theme values cannot directly read CSS variables in all contexts -> mitigate by exporting theme color constants from TypeScript and mirroring CSS variable values with clear naming.
- Planet-orbit animation could distract during PDF reading -> mitigate by rendering it only when no PDF is loaded or during an optional entry animation, and hiding/removing it from the active PDF reading state.
- Existing `web-pc-ui-polish` proposal conflicts with replacing the orbit animation -> mitigate by making this change the newer visual-foundation contract and documenting that orbit is retained.

## Migration Plan

1. Add or reorganize CSS tokens in `variables.css` while preserving backward-compatible aliases for existing variable names.
2. Add centralized Naive UI theme override module and update `App.vue` imports.
3. Update entity color constants to match the new token roles.
4. Update layout and component styles incrementally:
   - page background and panels
   - upload/URL input
   - progress and stage list
   - PDF toolbar/viewer empty state and loaded-PDF state
   - entity modal/tags
   - history/config placeholders
5. Run frontend build and visual inspection.

Rollback is straightforward because this change is style-system focused. Revert the changed frontend files or revert the eventual implementation commit.

## Open Questions

- Whether the implementation should add an icon library later for richer controls. Current scope assumes no new dependency.
- Whether the optional entry animation should play once per session or every time the user returns to the processing route. The implementation should default to a conservative one-time or short-lived animation if this is added.
