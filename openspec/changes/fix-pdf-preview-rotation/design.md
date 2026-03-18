## Context

PDF preview in frontend currently displays incorrect orientation for some PDFs. This is due to PDF.js not checking the original PDF direction metadata.

## Goals / Non-Goals

**Goals:**
- Detect PDF orientation from metadata
- Apply automatic rotation correction
- Display PDF in readable orientation

**Non-Goals:**
- Manual rotation controls
- PDF editing features

## Decisions

### Decision 1: Use PDF.js viewport rotation
**Rationale**: PDF.js provides viewport transformation options that can rotate the rendering context.

**Implementation**: Check `/Rotate` entry in PDF document dictionary, apply rotation to viewport.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Performance impact | Rotation happens during initial render only |
| Incorrect auto-detection | Test with various PDF sources |

## Migration Plan

1. Update PDF.js rendering code in frontend
2. Add orientation detection logic
3. Test with sample PDFs
4. Deploy to production

## Open Questions

1. Should we cache orientation detection results?
