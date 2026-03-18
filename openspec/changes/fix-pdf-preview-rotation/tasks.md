# PDF Preview Rotation Fix - Tasks

## Phase 1: Investigation (0.5天)

- [ ] Analyze current PDF.js rendering code
- [ ] Research PDF orientation metadata detection
- [ ] Identify sample PDFs with rotation issues

## Phase 2: Implementation (0.5天)

- [ ] Add PDF orientation detection logic
  - [ ] Read PDF document `/Rotate` entry
  - [ ] Determine rotation angle
- [ ] Update PDF.js viewport configuration
  - [ ] Apply rotation transformation
  - [ ] Adjust canvas size if needed
- [ ] Update frontend PDF preview component
  - [ ] Integrate orientation detection
  - [ ] Test rendering

## Phase 3: Testing (0.5天)

- [ ] Test with normal oriented PDFs
- [ ] Test with rotated PDFs
- [ ] Test with various PDF sources
- [ ] Verify no performance regression

## Phase 4: Deployment (0.5天)

- [ ] Code review
- [ ] Deploy to staging
- [ ] Verify fix in production
