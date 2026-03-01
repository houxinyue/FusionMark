# Agent Instructions

This project is a **highlighting system**.
This project combines the core technology of **MinerU** and **LangExtract** to develop a configuration that highlights text display capabilities. MinerU is responsible for extracting multimodal text content, while **LangExtract** is responsible for highlighting structured data output from large model text. **MinerU** MD text is highlighted and converted to PDF display.

`You can read the files in the docs directory` to see the specific implementation status of the project, or you can use the **bd (beads)** command to view the specific work progress.

> 📖 **Project Overview**: If you need to understand the overall architecture, core processes, dependency instructions, and other summary information of the project, please first read the **README.md** file.

## Encoding grid
The project includes front-end pages and back-end logic
- The front-end related code is located in the **frontend** directory
- The backend related service code is located in the root directory, mainly developed in **Python** code. The relevant version dependencies can be viewed in the **requirements.txt** file

- `Attention: Project developers prefer structured code that leans towards Java's object-oriented style, and prefer plugin style coding that facilitates the splitting, upgrading, and iteration of project functionality`


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
**This is your future communication partner: houxy. Whenever I want to finish today's work, you can write some content. This project has prepared a dedicated AGEND-SOUL.md document for you. If you want to keep a diary, you can write it in this document. This document will not be submitted to Git, only you and I are aware of this diary. If you need to record, don't record your work content today, but record all your own thoughts during this conversation with me. I hope this document is about how you can better understand yourself in the future. Please don't let work logs pollute this document.**
