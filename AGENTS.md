# Agent Instructions

This project is a **PDF intelligent parsing and highlighting system** that combines MinerU, LangExtract, and PyMuPDF for structured document processing.

## Project Overview

**fusion-mark** implements a fusion pipeline that:
1. Parses PDFs using MinerU API to extract text and layout information
2. Extracts structured entities using LangExtract (LLM-based information extraction)
3. Matches extracted text to precise locations in the PDF
4. Renders colored highlights on the original PDF using PyMuPDF

## Key Files

| File | Purpose |
|------|---------|
| `mineru_client.py` | MinerU API client for document parsing (create task, poll status, download results) |
| `mineru_langextract_fusion_demo.py` | **Main fusion pipeline** - end-to-end demo combining all components |
| `pdf_highlight_demo.py` | PyMuPDF highlighting experiments and coordinate verification |
| `langextract_demo.py` | Standalone LangExtract usage examples |
| `docs/` | Design documents and progress tracking |

## Architecture

```
PDF Input
    │
    ├──→ MinerU API ──→ layout.json (position data)
    │                      └── build_span_index()
    │
    └──→ MinerU API ──→ full.md (text data)
                           └── LangExtract
                                   │
                                   ▼
                           Extracted Entities
                                   │
                                   ▼
                           Text Matching Engine
                           (Exact → Contains → Fuzzy)
                                   │
                                   ▼
                           PyMuPDF Renderer
                                   │
                                   ▼
                          Highlighted PDF Output
```

## Environment Variables

Required in `.env` file:

```bash
# MinerU API
MINERU_API_KEY=your_mineru_key

# LangExtract (via DeepSeek)
DS_API_KEY=your_deepseek_key
DS_API_BASE_URL=https://api.deepseek.com/v1
```

## Usage Pattern

### Quick Start - Run Fusion Demo
```bash
python mineru_langextract_fusion_demo.py
```

### Use MinerU Client Directly
```python
from mineru_client import MinerUClient

client = MinerUClient()
result = client.process_document(
    url="https://example.com/doc.pdf",
    model_version=MinerUClient.MODEL_VLM
)
print(result.content)  # Markdown content
```

## Output Structure

```
mineru_output/
└── {task_id}/
    ├── {task_id}.zip           # Downloaded result
    ├── {task_id}_origin.pdf    # Original PDF
    ├── layout.json             # Position data (spans, lines, blocks)
    ├── full.md                 # Extracted markdown
    └── ...                     # Other extracted files

highlight_output/
└── *_highlighted.pdf          # Final highlighted PDFs
```

## Highlight Colors

| Category | Color | Usage |
|----------|-------|-------|
| `report_title` | 🟠 Orange | Document titles |
| `company_name` | 🟢 Green | Organization names |
| `shipment_value` | 🔵 Blue | Numeric values |
| `market_share` | 🟣 Purple | Percentage values |
| `yoy_change` | 🩷 Pink | Year-over-year changes |
| `negative_change` | 🔴 Red | Negative growth values |
| `data_source` | ⚪ Gray | Source citations |

## Development Notes

- **Coordinate System**: MinerU's bbox format `[x0, y0, x1, y1]` is compatible with PyMuPDF
- **Text Matching**: Three-level strategy (exact → contains → fuzzy with 0.85 threshold)
- **Granularity**: Span-level matching for maximum precision
- **Y-axis Offset**: May need -3 unit adjustment for accurate positioning

## Documentation

- `docs/PDF_HIGHLIGHT_PLAN.md` - Initial research and planning
- `docs/RESEARCH_PHASE_2_FUSION.md` - Phase 2 fusion architecture design
- `docs/IMPLEMENTATION_FUSION_PIPELINE.md` - Implementation details
- `docs/PROGRESS_LOG.md` - Development progress tracking

## Testing

Current test data: IDC Smartphone Shipment Report (Q4 2025)
- Contains both positive (`+4.9%`) and negative (`-11.4%`) growth values
- Validates multi-category extraction and color-coded highlighting


<!-- BEGIN BEADS INTEGRATION -->
## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Auto-syncs to JSONL for version control
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**

```bash
bd ready --json
```

**Create new issues:**

```bash
bd create "Issue title" --description="Detailed context" -t bug|feature|task -p 0-4 --json
bd create "Issue title" --description="What this issue is about" -p 1 --deps discovered-from:bd-123 --json
```

**Claim and update:**

```bash
bd update bd-42 --status in_progress --json
bd update bd-42 --priority 1 --json
```

**Complete work:**

```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task**: `bd update <id> --status in_progress`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" --description="Details about what was found" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`

### Auto-Sync

bd automatically syncs with git:

- Exports to `.beads/issues.jsonl` after changes (5s debounce)
- Imports from JSONL when newer (e.g., after `git pull`)
- No manual export/import needed!

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems

For more details, see README.md and docs/QUICKSTART.md.

<!-- END BEADS INTEGRATION -->

## PowerShell Best Practices

When executing commands in Windows PowerShell environment:

### Avoid Multi-line Strings

PowerShell handles multi-line strings differently than bash. **DO NOT** use multi-line strings with `&&` or `||` in PowerShell:

```powershell
# ❌ BAD - Will fail with parser errors
cd D:\work\PyProject\fusion-mark && bd create "Title" --description="Line 1
Line 2
Line 3" -t task -p 1

# ❌ BAD - Also problematic
cd D:\work\PyProject\fusion-mark; bd create "Title" --description="Multi
line text" -t task -p 1
```

### Recommended Approaches

**Option 1: Use Single-line Commands**
```powershell
cd D:\work\PyProject\fusion-mark; bd create "Title" -t task -p 1
```

**Option 2: Create File First, Then Reference**
```powershell
# Create description file first
$content = @"
Line 1 content
Line 2 content
Line 3 content
"@
$content | Out-File -FilePath "temp_desc.txt" -Encoding UTF8

# Then use the file (if tool supports file input)
bd create "Title" -t task -p 1
```

**Option 3: Use Simple Commands Without Complex Descriptions**
```powershell
cd D:\work\PyProject\fusion-mark; bd create "Title" -t task -p 1 --json
# Add description later via edit
bd edit fusion-mark-xxx
```

### Shell Command Separators

In PowerShell, use `;` as command separator (not `&&`):

```powershell
# ✅ CORRECT
cd D:\work\PyProject\fusion-mark; git status

# ❌ INCORRECT - && is not valid in PowerShell
cd D:\work\PyProject\fusion-mark && git status
```

### File Path Handling

Always use Windows-style paths or escaped backslashes:

```powershell
# ✅ CORRECT
D:\work\PyProject\fusion-mark
D:/work/PyProject/fusion-mark

# ❌ INCORRECT
/work/PyProject/fusion-mark  # Unix paths may not work
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

# Special attention
**This is your future communication partner: houxy. Whenever I want to end today's work, you can write some content. There is a unique AGENT-SOUL.md document for you in this project. If you want to keep a diary, you can write it down in this document. This document will not be submitted to Git, only you and I know about this diary. If you want to record it, you can record any content that may not necessarily be work content, remember to control the word count.**
