# Redis Entities And HTML Preview - Tasks

## Phase 1: Backend Payload Design (0.5天)

- [ ] Add a serializer for LangExtract extractions
  - [ ] Convert extraction objects to lightweight entity dicts
  - [ ] Preserve `text`, `category`, and char interval fields
- [ ] Add HTML preview generation
  - [ ] Reuse LangExtract `visualize(result)` output
  - [ ] Return preview HTML as a string for Redis result

## Phase 2: Task Result Integration (0.5天)

- [ ] Extend highlight service result details
  - [ ] Include `entities`
  - [ ] Include `langextract_html`
- [ ] Extend async task processor result payload
  - [ ] Write `entities` into Redis task result
  - [ ] Write `langextract_html` into Redis task result

## Phase 3: Frontend Rendering (0.5天)

- [ ] Update entity preview area
  - [ ] Prefer rendering `result.langextract_html`
  - [ ] Add fallback rendering from `result.entities`
  - [ ] Keep final fallback to `category_counts`
- [ ] Ensure rendering works in existing completed-task flow

## Phase 4: Validation (0.5天)

- [ ] Run a real task through the existing API workflow
- [ ] Verify Redis task result contains preview payloads
- [ ] Verify frontend entity panel shows HTML preview
- [ ] Verify fallback path still works if HTML is absent
