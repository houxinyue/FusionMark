# Agent Instructions

This project is a **highlighting system**.
This project combines the core technology of **MinerU** and **LangExtract** to develop a configuration that highlights text display capabilities. MinerU is responsible for extracting multimodal text content, while **LangExtract** is responsible for highlighting structured data output from large model text. **MinerU** MD text is highlighted and converted to PDF display.

`You can read the files in the docs directory` to see the specific implementation status of the project, or you can use the **bd (beads)** command to view the specific work progress.

> 📖 **Project Overview**: If you need to understand the overall architecture, core processes, dependency instructions, and other summary information of the project, please first read the **README.md** file.

## Encoding grid
The project includes front-end pages and back-end logic
- The front-end related code is located in the **frontend** directory
- The backend related service code is located in the **services** directory, mainly developed in **Python** code. The relevant version dependencies can be viewed in the **requirements.txt** file

> 📖 **Project Structure**: See **README.md** for detailed project structure and module organization.

- `Attention: Project developers prefer structured code that leans towards Java's object-oriented style, and prefer plugin style coding that facilitates the splitting, upgrading, and iteration of project functionality`

## Specification-Driven Development (OpenSpec + Beads)

**CRITICAL RULE**: NO CODING without an approved specification. All new features, significant refactoring, or architectural changes MUST go through the OpenSpec workflow first.

### Why OpenSpec & Beads?
- **OpenSpec** defines WHAT to build (immutable contract) and WHY.
- **Beads** tracks the execution STATE (mutable reality) and WHEN/WHO.
- Together, they prevent AI amnesia and keep the human in control.

### The 4-Phase Workflow

#### Phase 1: Planning (OpenSpec)
1. **Initialization**: If the project lacks an `openspec/` folder, run:
   ```powershell
   openspec init
   ```
2. **Propose**: When receiving a new feature request, create a new change directory: `openspec/changes/<change-name>/`.
3. **Draft**: Generate `proposal.md` (intent, scope, architecture) and `tasks.md` (implementation checklist) in this directory.
4. **Validate**: Run the following command to ensure format correctness:
   ```powershell
   openspec validate
   ```
5. **Approval**: You MUST present the proposal to the user (houxy) for review. DO NOT proceed to Phase 2 until approved.

#### Phase 2: Seed Tracker (Beads Bridge)
Once the user approves the OpenSpec proposal, you must translate the `tasks.md` into actionable Beads issues.
**Crucial**: ALWAYS include the path to the OpenSpec proposal in the description so the context is never lost.

```powershell
# Example of seeding a task from OpenSpec to Beads
bd create "Implement OAuth login" --description="Context: openspec/changes/oauth/proposal.md" -t feature -p 1 --json
```

#### Phase 3: Implementation Tracking (Beads)
1. **Check ready work**: `bd ready --json` shows unblocked issues.
2. **Claim your task**: `bd update <id> --status in_progress --json`.
3. **Execute**: Write code, test, and verify against the linked OpenSpec file.
4. **Discovery Tracking**: If you discover edge cases, bugs, or refactoring needs during coding, DO NOT just fix them silently. Create a linked issue:
   ```powershell
   bd create "Found DB edge case" -t bug -p 1 --deps discovered-from:<current-bd-id> --json
   ```
5. **Complete**: `bd close <id> --reason "Completed according to spec" --json`. Update the checkbox in `tasks.md`.

#### Phase 4: Archive (OpenSpec)
Once all `bd` tasks for a specification are closed and `tasks.md` is fully checked off, you must merge the change into the main specifications (`openspec/specs/`):
```powershell
openspec archive <change-name>
```

### Important Rules
- ✅ Use OpenSpec for ALL architecture/feature planning.
- ✅ Use `bd` for ALL task tracking.
- ✅ Always use `--json` flag for programmatic `bd` use.
- ❌ Do NOT start coding until Phase 1 is approved by houxy.
- ❌ Do NOT use external issue trackers or markdown TODO lists outside of OpenSpec.


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


