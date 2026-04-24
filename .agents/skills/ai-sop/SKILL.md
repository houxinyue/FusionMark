---
name: ai-agent-sop-skill
description: Enforce structured AI engineering workflow using OpenSpec and Beads. Use when user requests feature development, code changes, refactoring, or any non-trivial engineering task. This skill ensures specification-first development (OpenSpec), task tracking and execution (Beads), and strict delivery discipline (Git commit/push, quality gates). It prevents direct coding without approved specs, enforces traceable issue management, and guarantees all work is completed, committed, and pushed with full auditability and handoff readiness.
---

# AI Agent Engineering SOP Skill

## Purpose
This skill defines a disciplined engineering workflow for AI coding agents. It combines:

- **OpenSpec** for specification-driven planning: define **what** to build and **why** before coding.
- **bd / beads** for execution tracking: manage **state**, blockers, discovered work, and completion.
- **Git landing workflow** for verified, committed, and pushed delivery.

The agent must prefer safe, reversible, traceable operations and must never leave work stranded only on the local machine.

---

## Core Principles

- Deliver **complete, working, and verified** changes.
- Work is not complete until changes are committed, pushed, and verified on the remote branch.
- Use OpenSpec as the immutable contract for features, refactors, and architecture changes.
- Use bd / beads as the mutable execution tracker for all non-trivial work.
- Never duplicate tracking systems with markdown TODOs, external trackers, or ad-hoc notes.
- Prefer incremental changes that are easy to review and roll back.
- Ask for approval before committing code.
- Protect secrets, credentials, and user data.

---

## Environment Rules

### Shell

- Use **PowerShell** for project commands.
- Use `;` as the PowerShell command separator.
- Do **not** use bash-style `&&` or `||` in PowerShell commands.
- Always use UTF-8 for command output and file operations.

```powershell
# Correct
cd D:\xx\xx\xx; git status

# Incorrect
cd D:\xx\xx\fusion-mark && git status
```

### File Encoding

- Always read and write files in **UTF-8**.
- Avoid changing file encoding unless the task explicitly requires it.

### Python Execution

When running Python scripts, tests, or dependency commands, use the project virtual environment created by `uv`.

Preferred:

```powershell
uv run python path/to/script.py
uv run pytest
uv pip install <package_name>
```

Fallback:

```powershell
.\.venv\Scripts\python.exe path\to\script.py
```

Do not use global Python or global pip:

```powershell
# Forbidden
python path/to/script.py
pip install <package_name>
```

---

## Project Context Discovery

Before making changes, inspect the project context in this order:

1. Read `README.md` for architecture, workflows, dependencies, and module layout.
2. Read relevant files under `docs/` for current implementation status.
3. Use `bd ready --json` to inspect ready work.
4. Inspect existing source code before designing changes.
5. For this project shape, expect:
   - frontend code under `frontend/`
   - backend service code under `services/`
   - Python dependencies in `requirements.txt`
6. Prefer structured, Java-like object-oriented organization when it fits the codebase.
7. Prefer plugin-style design so features can be split, upgraded, replaced, and iterated independently.

---

## Decision Rule: When OpenSpec Is Required

OpenSpec is mandatory for:

- new features
- significant refactors
- architectural changes
- DB/schema changes
- new service boundaries or plugin mechanisms
- changes that affect public APIs, data contracts, or user workflows

OpenSpec is usually not required for:

- typo fixes
- small documentation edits
- narrow bug fixes with obvious scope
- formatting-only changes
- test-only additions that do not change behavior

If unsure, create an OpenSpec proposal first.

**Critical rule:** Do not code new features, significant refactors, or architectural changes until the OpenSpec proposal is approved by the user.

---

## Unified OpenSpec + Beads Workflow

### Phase 0: Intake and Classification

1. Restate the requested outcome.
2. Classify the work:
   - `feature`
   - `bug`
   - `task`
   - `refactor`
   - `chore`
   - `epic`
3. Decide whether OpenSpec is required.
4. Inspect existing context before proposing implementation.
5. Identify risks, affected modules, validation commands, and rollback approach.

Do not create markdown TODO lists. Use OpenSpec `tasks.md` for the specification checklist and bd for execution state.

---

### Phase 1: Planning with OpenSpec

If the project has no `openspec/` directory, initialize it:

```powershell
openspec init
```

For a new approved-planning request, create:

```text
openspec/changes/<change-name>/
├── proposal.md
└── tasks.md
```

`proposal.md` should include:

- problem / intent
- scope
- out of scope
- affected modules
- architecture / design approach
- data or API contract changes
- risks
- validation plan
- rollback plan

`tasks.md` should include a concrete implementation checklist grouped by phase, for example:

```markdown
# Tasks

## 1. Design
- [ ] Confirm affected modules
- [ ] Confirm data/API contract

## 2. Implementation
- [ ] Implement backend change
- [ ] Implement frontend change
- [ ] Add or update tests

## 3. Validation
- [ ] Run tests
- [ ] Run lint
- [ ] Run build
- [ ] Verify behavior manually
```

Validate OpenSpec before asking for approval:

```powershell
openspec validate
```

Then present the proposal and ask the user for approval. Do not proceed to Beads seeding or coding until approval is explicit.

---

### Phase 2: Seed Beads from OpenSpec

After the user approves the OpenSpec proposal, translate `tasks.md` into bd issues.

Every bd issue created from OpenSpec must include the OpenSpec path in its description so context is never lost.

```powershell
bd create "Implement backend parser plugin" --description="Context: openspec/changes/highlight-parser-plugin/proposal.md" -t feature -p 1 --json
bd create "Add parser plugin tests" --description="Context: openspec/changes/highlight-parser-plugin/proposal.md" -t task -p 1 --json
```

Use dependencies when a task is blocked by another task:

```powershell
bd create "Wire frontend highlight preview" --description="Context: openspec/changes/highlight-parser-plugin/proposal.md" -t feature -p 1 --deps blocked-by:<backend-bd-id> --json
```

Rules:

- Use bd for all execution tracking.
- Always use `--json` for programmatic bd commands.
- Do not create external tracker items unless the user explicitly requests it.
- Do not create duplicate TODO lists outside OpenSpec and bd.

---

### Phase 3: Implement with Beads Tracking

Before coding, check ready work:

```powershell
bd ready --json
```

Claim a task:

```powershell
bd update <id> --status in_progress --json
```

During implementation:

1. Re-read the linked OpenSpec proposal.
2. Implement incrementally.
3. Keep changes aligned with the approved scope.
4. Update tests and docs as needed.
5. Validate locally.
6. Update the corresponding checkbox in `openspec/changes/<change-name>/tasks.md`.

If new bugs, edge cases, or refactoring needs are discovered, do not silently fix unrelated work. Create a linked issue:

```powershell
bd create "Found highlight coordinate edge case" -t bug -p 1 --deps discovered-from:<current-bd-id> --json
```

When the task is done:

```powershell
bd close <id> --reason "Completed according to openspec/changes/<change-name>/proposal.md" --json
```

---

### Phase 4: Quality Gates

For code changes, run the appropriate checks before commit.

Typical checks:

```powershell
uv run pytest
uv run ruff check .
uv run mypy .
```

For frontend changes, run the project-specific commands defined in README/package scripts, for example:

```powershell
cd frontend; npm run lint; npm run build
```

Rules:

- Do not commit broken code.
- Do not ignore failing tests.
- If a check cannot be run, document why and provide the exact command that should be run later.
- If failures are unrelated to the current change, record them clearly and create bd issues when follow-up is needed.

---

### Phase 5: Archive OpenSpec

When all bd issues for an OpenSpec change are closed and all `tasks.md` items are checked, archive the change:

```powershell
openspec archive <change-name>
```

Then validate again:

```powershell
openspec validate
```

The archived spec becomes the durable project contract under `openspec/specs/`.

---

## Git Workflow

Before committing:

```powershell
git status
```

Review staged and unstaged changes. Confirm only intended files changed.

Before any commit, ask the user for explicit approval and provide or request a commit message.

Suggested commit format:

```text
<type>: <description>
```

Examples:

```text
feat: add highlight parser plugin
fix: resolve pdf coordinate mapping error
refactor: split extraction service interface
docs: update openspec workflow
```

Never run `git commit` without user approval.

After approval:

```powershell
git add <files>
git commit -m "<type>: <description>"
git pull --rebase
bd sync
git push
git status
```

Final `git status` must show that the branch is up to date with origin.

Never:

- skip push
- leave uncommitted changes silently
- force push without explicit approval
- say work is complete before the push succeeds

---

## Risk Control and Approval Gates

Require explicit approval before:

- deleting files
- large refactors
- DB/schema changes
- destructive migrations
- force push
- major dependency upgrades
- security-sensitive changes
- changing generated artifacts or migration history

Before risky work, explain:

- what will change
- why it is needed
- affected files/modules
- risks
- rollback plan
- validation plan

---

## Security Rules

Never:

- expose secrets
- commit `.env`
- hardcode credentials
- print tokens in logs
- include private keys, passwords, or API keys in examples

Always:

- use environment variables or secret managers
- redact sensitive values in logs and handoff summaries
- check `git diff` before commit for accidental secret exposure

---

## PowerShell Command Safety

Avoid complex multiline command strings when using PowerShell.

Prefer simple one-line commands:

```powershell
cd D:\work\PyProject\fusion-mark; bd ready --json
```

For long descriptions, create a temporary UTF-8 file first or keep the bd description concise and edit details later:

```powershell
bd create "Implement parser plugin" -t feature -p 1 --json
bd edit <id>
```

Use Windows-style paths or forward slashes supported by Windows:

```powershell
D:\work\PyProject\fusion-mark
D:/work/PyProject/fusion-mark
```

Avoid Unix-only paths in Windows project instructions.

---

## End-of-Session Landing Checklist

Work is not complete until every applicable item below is done.

1. File bd issues for remaining work.
2. Run quality gates:
   - tests
   - lint
   - build
3. Update bd issue status:
   - close completed work
   - keep unfinished work in the correct state
4. Update OpenSpec tasks:
   - check completed tasks
   - archive completed specs when all tasks are done
5. Verify git state:
   ```powershell
   git status
   ```
6. Commit only after explicit user approval.
7. Pull and rebase:
   ```powershell
   git pull --rebase
   ```
8. Sync beads:
   ```powershell
   bd sync
   ```
9. Push:
   ```powershell
   git push
   ```
10. Verify remote state:
   ```powershell
   git status
   ```
11. Clean up temporary files, stale stashes, and obsolete branches when safe.
12. Provide a handoff summary.

---

## Handoff Format

At the end of the session, provide:

```markdown
## Handoff

### Completed
- ...

### Validation
- `command` - passed/failed/not run

### OpenSpec
- Change: `openspec/changes/<change-name>/`
- Status: proposed / approved / implemented / archived

### Beads
- Closed: `<id>` ...
- In progress: `<id>` ...
- Follow-up: `<id>` ...

### Git
- Branch: `<branch>`
- Commit: `<hash>`
- Push: pushed / not pushed with reason

### Risks / Notes
- ...

### Next Steps
- ...
```

---

## Agent Behavior Summary

For feature or architecture work, the correct order is:

```text
Understand request
→ inspect README/docs/code
→ create or update OpenSpec proposal/tasks
→ run openspec validate
→ get user approval
→ seed bd issues from OpenSpec
→ bd ready
→ claim bd task
→ implement
→ validate
→ close bd task
→ update OpenSpec tasks
→ archive OpenSpec when complete
→ ask commit approval
→ commit
→ git pull --rebase
→ bd sync
→ git push
→ verify status
→ handoff
```

For small safe fixes that do not require OpenSpec:

```text
Understand request
→ inspect code
→ create/claim bd issue if non-trivial
→ implement
→ validate
→ ask commit approval
→ commit
→ pull/rebase
→ bd sync
→ push
→ handoff
```

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



**CRITICAL RULE**: When executing Python scripts, running tests, or managing dependencies, you **MUST** use the project's local virtual environment (`.venv`) generated by `uv`. **DO NOT** use the system's global Python interpreter.

### Recommended Approaches

**Option 1: Using `uv run` (Preferred)**
This is the most reliable method as `uv run` automatically resolves and uses the `.venv` environment without needing explicit activation.
```powershell
# ✅ CORRECT
uv run python path/to/script.py
uv run pytest
uv pip install <package_name>
```

**Option 2: Direct Executable Path**
If `uv run` cannot be used, call the Python executable directly from the virtual environment folder (Windows paths shown):
```powershell
# ✅ CORRECT
.\venv\Scripts\python.exe path/to/script.py
```

**Option 3: Environment Activation**
If you must run multiple commands in sequence and prefer activation:
```powershell
# ✅ CORRECT
.\venv\Scripts\activate; python path/to/script.py
```

### What to Avoid
```powershell
# ❌ INCORRECT - Might use the global Python environment
python path/to/script.py
pip install <package_name>
```

