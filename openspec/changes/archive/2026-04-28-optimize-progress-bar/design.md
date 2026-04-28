## Context

Current progress bar has basic functionality but lacks visual polish. Users need clearer feedback about processing stages.

## Goals / Non-Goals

**Goals:**
- Clear progress percentage display
- Visual distinction between stages
- Smooth animations
- Intuitive stage icons

**Non-Goals:**
- Customizable themes
- Sound notifications

## Decisions

### Decision 1: Use CSS transitions for smooth animations
**Rationale**: CSS transitions provide smooth stage transitions without JavaScript complexity.

### Decision 2: Stage-specific color coding
**Rationale**: Different colors for each stage (mineru=blue, extraction=orange, highlight=green) provide instant visual recognition.

### Decision 3: SVG icons for stages
**Rationale**: SVG icons scale well and support animations.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Animation performance | Use CSS transforms only, no layout-triggering properties |
| Color accessibility | Ensure sufficient contrast ratios |

## Migration Plan

1. Update progress bar component styling
2. Add stage icon components
3. Integrate with new Redis progress data format
4. Test animations on various devices

## Open Questions

1. Should we add sound effects for stage completion?
2. Do we need a compact mode for small screens?
