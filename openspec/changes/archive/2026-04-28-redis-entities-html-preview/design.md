## Context

The current workflow already generates three useful outputs after LangExtract finishes:

1. Extraction objects in memory
2. JSONL debug artifact on disk
3. Official LangExtract HTML visualization on disk

The missing piece is that the frontend only receives summary counts from Redis task result, so users cannot see the extracted entities directly in the main UI.

## Goals / Non-Goals

**Goals:**
- Reuse existing LangExtract output as much as possible
- Keep JSONL export unchanged for debugging
- Expose both HTML preview and structured entity JSON through Redis task result
- Let frontend prefer HTML rendering and gracefully fall back to JSON/counts

**Non-Goals:**
- Full text-to-PDF entity linking in the frontend
- Persisting JSONL raw text inside Redis
- Building a new frontend visualization system from scratch

## Decisions

### Decision 1: Store both HTML and JSON in Redis result
**Rationale**: HTML is the fastest path to useful frontend display, while JSON preserves future flexibility for filtering, linking, and fallback rendering.

### Decision 2: Keep JSONL on disk only
**Rationale**: JSONL is a debug artifact and not an ideal frontend payload. Storing it in Redis would increase payload size without improving direct UI usability.

### Decision 3: Frontend prefers `langextract_html`
**Rationale**: This minimizes frontend implementation work and keeps the visible result close to LangExtract’s native visualization.

### Decision 4: Retain fallback rendering from `entities` and `category_counts`
**Rationale**: This preserves resilience if HTML is missing, disabled, or later trimmed.

## Data Model

Recommended completed task result fields:

```json
{
  "extraction_count": 19,
  "highlight_count": 19,
  "category_counts": {
    "company_name": 5
  },
  "langextract_html": "<div>...</div>",
  "entities": [
    {
      "text": "Apple",
      "category": "company_name",
      "char_start": 120,
      "char_end": 125
    }
  ]
}
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Redis result payload becomes larger | Keep entity JSON lightweight and avoid storing JSONL raw text |
| Embedded HTML conflicts with page styles | Render inside a dedicated container and refine isolation later if needed |
| Frontend over-relies on HTML | Keep structured `entities` as fallback and future integration path |

## Migration Plan

1. Extend highlight service to return `entities` and `langextract_html`
2. Extend task processor to write both into Redis `result`
3. Update frontend entity area to prefer HTML
4. Fall back to structured entities, then counts
5. Validate on a real task through the existing API flow

## Open Questions

1. Should LangExtract HTML later be sanitized or sandboxed with `iframe/srcdoc`?
2. Do we want to split large preview payloads into a separate Redis key if task results grow too much?
