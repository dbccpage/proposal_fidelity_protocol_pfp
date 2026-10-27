---
kind: law
authority_effect: None
status: live
owner: techne-council
---
# Windows CLI Patterns

Shared Windows-specific command patterns for cross-platform compatibility.

## Alembic

**CORRECT:** Use `.exe` directly from venv:

```powershell
.venv\Scripts\alembic.exe -c alembic_sdlc.ini upgrade head
.venv\Scripts\alembic.exe -c alembic_sdlc.ini history --verbose
.venv\Scripts\alembic.exe -c alembic_sdlc.ini current

```

**WRONG:** `python -m alembic` fails on Windows:

```text
python -m alembic: No module named alembic.__main__

```

## Pytest

**CORRECT:**

```powershell
.venv\Scripts\pytest.exe tests/
.venv\Scripts\python.exe -m pytest tests/

```

## PostgreSQL (psql)

**CORRECT:**

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d sdlc

```

## Git Add

**Prefer explicit paths** over `git add .` on Windows:

```powershell

# CORRECT - explicit paths

git add .agents/ engine/

# RISKY - may fail with device files (frontend/nul)

git add .

```

**Error pattern:**

```text
error: open("frontend/nul"): No such file or directory
fatal: adding files failed

```

## npm/Node

**EBUSY or binary errors:**

```powershell

# Clean install

Remove-Item -Recurse -Force node_modules, package-lock.json
npm install

# Rollup binary (Windows-specific, optional dep)

npm install --save-optional @rollup/rollup-win32-x64-msvc

```

## Bash Tool on Windows

The Bash tool runs in a Unix-like shell (Git Bash/MSYS2) on Windows. Critical rules:

1. **Always use forward slashes** in paths: `ls "C:/Users/..."` not `ls "C:\Users\..."`
2. **Use Unix commands**: `mkdir -p` not `if not exist ... mkdir`
3. **Subagent prompts with paths**: When dispatching subagents, convert all Windows paths to forward-slash format in the prompt text

### MSYS mangles `git <rev>:<path>` -- WRONG ANSWERS, NOT ERRORS

This is the dangerous class: the command **succeeds** and returns something plausible.
MSYS2 path conversion sees the `:` in a git object spec and rewrites the argument into a
Windows path, so the git command answers a question you did not ask.

```bash

# BROKEN in the Bash tool -- returns  origin\main;.agents\skills\x\SKILL.md

git rev-parse "origin/main:.agents/skills/x/SKILL.md"
git ls-tree -r --name-only <rev> -- ".agents/skills/"   # pathspec mangled too

```

Observed 2026-07-28: these calls produced a tree/blob reading that flatly contradicted
the working tree, and the contradiction was reported as a finding before the mangling
was spotted. **Two commands disagreeing about git state on Windows is a tooling
symptom before it is a repository symptom.**

Use **PowerShell** for any `<rev>:<path>` or tree read -- it has no path conversion:

```powershell
git rev-parse "origin/main:.agents/skills/x/SKILL.md"
git cat-file -e "HEAD:$p"; if ($LASTEXITCODE -eq 0) { "present" } else { "absent" }

```

`MSYS_NO_PATHCONV=1` in front of the Bash invocation also works, but it must be
remembered on **every** call; switching shells for the whole read is the reliable fix.

## The Grep tool respects `.gitignore` -- ignored-but-live dirs are invisible

`.gitignore` line 234 is `/.claude/*` with only `!/.claude/skills/` re-included, so
**`.claude/agents/` and `.claude/workflows/` exist, are live, and are silently absent
from Grep-tool results.** A repo-wide rename that trusts the Grep tool alone will leave
those two surfaces stale. Observed 2026-07-28: a 149-file Grep result showed zero
`.claude/workflows` hits; a direct `grep -ln` on the same paths found four files.

For any cross-host sweep, verify with a shell grep that does not consult `.gitignore`:

```bash
grep -rln "<pattern>" .claude/agents/ .claude/workflows/

```

## General Pattern

When a command fails on Windows:

1. Check if `.exe` version exists in `.venv\Scripts\`
2. Try full path instead of relying on PATH
3. Use PowerShell syntax (`&` for paths with spaces)
4. Check for Windows device name conflicts (CON, NUL, PRN)

---

**Used by:** `alembic-migration`, `postgresql`, `run-tests`, `commit`, `ci-cd`

**Source:** Sprint 104, Sprint 105-0
