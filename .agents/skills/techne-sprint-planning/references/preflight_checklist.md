# Pre-flight checklist

`AuthorityEffect: None.` Reference material for [`sprint-planning`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Pre-Flight Checklist (MANDATORY)

Before starting sprint planning, verify all external dependencies are available.

### Deferred Work Audit

Before planning a new sprint, check for features that have been deferred multiple times:

```bash

# Search for "deferred" or "postponed" in recent sprint retrospectives
grep -ri "defer\|postpone" coda_project_planning/sprints/*/retrospective.md | tail -10

``` ext

If a feature has been deferred 3+ sprints, escalate to Product Owner for re-prioritization decision. Chronic deferral indicates either:

- Feature is not actually needed (descope it)
- Feature is blocked by something unstated (identify and plan for blocker)
- Feature keeps losing priority contests (needs executive decision)

**Source:** Sprint 074 - Content/Education engines deferred for 10 sprints without escalation

### Database Services Check

```python

# Check PostgreSQL (required for all sprints)

# Reads PG_HOST from .env (GCP Cloud SQL: 34.28.15.236). Falls back to localhost.
import os, socket
pg_host = os.environ.get('PG_HOST', 'localhost')
pg_port = int(os.environ.get('PG_PORT', '5432'))
s = socket.socket()
s.settimeout(5)
pg_available = s.connect_ex((pg_host, pg_port)) == 0
s.close()
print(f"PostgreSQL ({pg_host}:{pg_port}): {'AVAILABLE' if pg_available else 'NOT AVAILABLE'}")

# Check Neo4j (required for Graphiti memory stories)
s = socket.socket()
s.settimeout(2)
neo4j_available = s.connect_ex(('localhost', 7687)) == 0
s.close()
print(f"Neo4j: {'AVAILABLE' if neo4j_available else 'NOT AVAILABLE'}")

``` ext

### Alembic Availability Check

```bash

# Check alembic is in PATH
py -3.12 -m alembic --version

``` ext

### Pre-Flight Verification Checklist

| Check | Required | Command |
|-------|----------|---------|
| PostgreSQL port 5432 | Always | `socket.connect_ex((os.environ.get('PG_HOST','localhost'), 5432))` |
| Neo4j port 7687 | If Graphiti stories | `socket.connect_ex(('localhost', 7687))` |
| Alembic module | If migration stories | `py -3.12 -m alembic --version` |
| Git branch | Always | `git branch --show-current` |
| Clean working tree | Recommended | `git status --short` |
| npm install | If frontend stories | `cd frontend && npm install 2>&1` |
| Vitest available | If frontend tests | `cd frontend && npx vitest --version 2>&1` |

### Handling Failures

If pre-flight checks fail:

1. **PostgreSQL not available:**
   - Start PostgreSQL service
   - Or mark DB-dependent stories as BLOCKED in sprint plan
   - Document in `quality_gates.md` ext

2. **Neo4j not available:**
   - Start Neo4j service (if Graphiti stories planned)
   - Or defer Graphiti stories to future sprint

3. **Alembic not available:**
   - Run `pip install alembic` or use `py -3.12 -m alembic` ext
   - Document Windows setup if needed

4. **npm install fails (EBUSY or Rollup binary error):**
   - **Windows-only:** If you see a Rollup binary error, install the Windows binary as an **optional** dependency, for example: `npm install --save-optional @rollup/rollup-win32-x64-msvc` ext
   - Respect any existing `.npmrc` settings for optional dependencies; do **not** add the Windows-only Rollup package as a mandatory dependency for all platforms
   - Clean install (run the variant appropriate for your shell):
     - **POSIX shells (macOS/Linux/Git Bash):** `rm -rf node_modules package-lock.json && npm install` ext
     - **Windows CMD:** `rmdir /s /q node_modules && del /q package-lock.json && npm install` ext
     - **Windows PowerShell:** `Remove-Item -Recurse -Force node_modules, package-lock.json; npm install` ext
   - Close all `node.exe` processes before retry
   - Mark frontend stories as BLOCKED if unresolvable
   - See `frontend/docs/troubleshooting.md` for detailed solutions

5. **Vitest not available:**
   - Run `npm install` first
   - **Windows-only Rollup binary error:** install `@rollup/rollup-win32-x64-msvc` as an **optional** dependency (or follow repo-specific frontend Rollup guidance) rather than a mandatory cross-platform dependency
   - Verify with `npx vitest --version` ext

**Source:** Sprint 052 Retrospective Action #1 (STORY-052-0-001), Sprint 086-0 (npm EBUSY fix)

### Orphaned Sprint Audit (MANDATORY)

Before planning ANY new sprint, check for orphaned sprints:

```bash

# Find sprints with review.md (approved) but no retrospective.md
for dir in coda_project_planning/sprints/[0-9]*/; do
  if [[ -f "$dir/review.md" ]] && [[ ! -f "$dir/retrospective.md" ]]; then
    echo "ORPHAN: $dir"
  fi
done

``` ext

**Gate Logic:**

``` ext
IF orphaned sprints found:
  OUTPUT: "⚠️ ORPHANED SPRINTS DETECTED"
  FOR each orphan:
    OUTPUT: "Sprint {N}: approved but not executed"
  ASK: "Resolve orphans before planning? [y/cancel/defer to backlog]"

``` ext

**Resolution Options:**

1. **Execute orphan** - Run `/sprint-execution {N}` for the orphaned sprint
2. **Cancel orphan** - Create cancellation retrospective.md, archive sprint
3. **Defer to backlog** - Extract incomplete work to next sprint's backlog.md

**Why mandatory:** Sprint 100 session discovered 4 orphaned sprints (068, 078, 082, 084) that were approved but never executed, with no retrospectives. This caused frustration and required extensive cleanup.

**Source:** Sprint 100 autoskill - orphaned sprint audit learning

---
