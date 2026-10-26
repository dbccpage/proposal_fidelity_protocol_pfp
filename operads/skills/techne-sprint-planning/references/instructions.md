# Planning instructions

`AuthorityEffect: None.` Reference material for [`sprint-planning`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Instructions

When this skill is invoked:

### Step 1: Determine Sprint Number

```python

# From argument
sprint_number = args[0] if args else None

# Or from branch name (sprint-XXX)
if not sprint_number:
    branch = git_current_branch()
    if branch.startswith("sprint-"):
        sprint_number = branch.split("-")[1]

``` ext

**IMPORTANT: Backlog Location**
Always check `coda_project_planning/sprints/{N}/ooutwire_backlog.md` first for sprint objectives.
This file contains the authoritative backlog from ooutwire. Do NOT use other
similarly-named files in subdirectories (e.g., `sprints_logos_news_engine/`).

**Ratified Roadmap Supersedes Prior Plans**
When a ratified roadmap document exists (e.g., `FINAL_SPRINT_ROADMAP.md` from a
multi-model debate or council consensus), it is the **sole source of truth** for
sprint stories, points, and scope. Do NOT reconcile or merge with older backlog
plans that predate the ratified document -- use the ratified stories directly.
Old plans in `backlog/` that conflict with the ratified roadmap are superseded.

**Source:** Sprint 107 planning session -- user correction (2026-02-05)

**Agent & Skill Directory Conventions**
The canonical agent & skill directories live under `.agents/`:

| Purpose | Path | Notes |
|---------|------|-------|
| Primary agents | `.agents/agents/` | Materialized capability slices |
| Active skills | `.agents/skills/` | Operad skills |
| Sprint plans | `coda_project_planning/sprints/` | Canonical sprint directory |

When referencing agent or skill paths, use `.agents/` paths.

### Step 2: Load Blackrod Identity

Load Blackrod's full prompt:

```ext
Load agent prompt: blackrod
```

### Step 3: Read Workflow Prompt

Read the workflow-specific prompt from `.agents/skills/sprint-planning/SKILL.md`.

### Step 4: Create Sprint Folder & Mandatory Subdirectories

Ensure sprint folder and mandatory subdirectories (derived from `000_sprint_template`) are created by `omega-engine-product-manager`:

```bash
mkdir -p coda_project_planning/sprints/{sprint_number}/0_planning_documents
mkdir -p coda_project_planning/sprints/{sprint_number}/1_sprint_impl_documents

```text

*(Note: omega-engine-product-manager also creates parent Epic plan documents (`epic_{slug}_plan.md`) and Saga plan documents (`saga_{slug}_plan.md`) at will when asked to structure project plans. Creation & modification rights for plans and sagas are strictly limited to `OOUTWIRE`, `BLACKROD`, and `omega-engine-product-manager`.)* ext

### Step 5: Submit Commitment (activation)

```python
Submit commitment),
    sprint_id=int(sprint_number),
    agent_code="blackrod",
    task_code=f"SPRINT-{sprint_number}-PLANNING",
    predictions={
        "p_success": 0.75,
        "planning_will_complete_on_time": 0.80,
        "all_stories_estimated": 0.85,
        "zero_critical_blockers": 0.90
    }
)

# Save epistemic_state_id for Outcome

``` ext

### Step 6: Enter Planning Mode

**MANDATORY:** Enter planning mode before any code changes.

``` ext
EnterPlanMode()

``` ext

In planning mode:

- Present sprint goal to user and establish sprint scope
- Read backlog/roadmap documents to define stories
- Explore codebase for current state
- Design implementation approach
- Get user approval before executing

**Gate:** Do NOT proceed past this step until the sprint goal is established and stories are defined. Steps 7-10 depend on knowing what stories exist.

### Step 7: Produce Parsed Plan (Single Pipeline)

Execute the workflow defined in `.anomalon/prompts/workflows/sprint_planning.md`: **Backlog Item → Parsed Plan**. No ghost participants (no product_owner, rust-principal-developer, sprint_architect, scrum_master, tester, devops step-agents). Blackrod (orchestrator) produces the three hard-coded artifacts: `sprint_{N}_plan.md`, `kickoff.md`, `quality_gates.md` in `coda_project_planning/sprints/{N}/`.

### Step 8: Pre-Sprint Code Audit (Scoped to Defined Stories)

**Prerequisite:** Sprint stories must be defined (Steps 6-7 complete).

Audit the codebase for pre-existing work that may affect **the defined stories**:

```bash

# Check for existing implementations related to DEFINED sprint stories
Grep(pattern="<story_keyword>", path="omega_engine/")

# Check for TODO/FIXME markers in affected areas
Grep(pattern="TODO|FIXME", path="backend/")

# Review recent commits for related work
git log --oneline -20 --all | grep -i "<story_keyword>"

``` ext

**Purpose:**

- Identify partially implemented features (adjust estimates down)
- Find existing code that can be reused
- Discover tech debt that may block stories
- Avoid duplicate work

**Scoping rule:** Only audit paths and keywords relevant to the stories defined in Steps 6-7. Do NOT run broad codebase scans before the sprint goal is known.

**Duplicate-claim rule (MANDATORY for "unify/remove/consolidate duplicate X" stories):** before estimating, grep the **whole workspace** for `X` — a "local duplicate" is often a cross-crate shared vocabulary, and naive unification breaks dependents. **Source:** Sprint 120 — STORY-002 ("unify duplicate `AuthorityEffect`") was scoped from one file; the name was actually shared across `omega_certifiers`/`anomalon_councils`/`omega_contracts` with distinct advisory semantics, forcing a re-scope. **If the grep finds >2 definitions or differing variants, scope an ADR/decision story (classify each pair SAME vs DISTINCT) FIRST — do not write a unify story.** **Source:** Sprint 120-0 — the grep found **6** distinct `AuthorityEffect` enums; an ADR-first scope decided "consolidate 3 identical fact-labels, keep firewall/contract/measurement distinct," preventing conflation at 3× the scale. **Cross-crate-ref false-positive guard:** a grep hit for `crate_A_type` inside `crate_B` is a real cross-crate reference ONLY if `crate_B` depends on `crate_A` (check its `Cargo.toml`) AND uses *that* type — a same-named *local* type in a non-dependent crate is a false positive. Verify the dependency edge before scoping it as work. **Source:** Sprint 120-0-0 — `evidence.rs:512` looked like an `omega_measurement` ref but was `omega_contracts`' own same-named `MeasurementEnvelope`; "fixing" it would have broken contracts.

**Doc archival/move ref-scope rule (MANDATORY for "archive/move/retire/rename canonical doc X" stories):** a "no live refs" AC must grep **all file types** (`**/*`, not just code), then classify each hit **live-authoritative** (companion catalogs, `controlling_spine:`/`companion_document:` frontmatter, code doc-comments → repoint) vs **frozen-history** (completed `coda_project_planning/sprints/*`, `completion.md` → EXEMPT and document, never rewrite). Redefine the gate to "0 live refs in code consumers + companion catalogs," not "0 grep hits." **Source:** Sprint 121 — discovery scoped v1-spine refs to `.py/.rs/.toml` (found 1); the real set was ~18, mostly markdown, and rewriting frozen evidence would have falsified the record.

**Document findings in** `coda_project_planning/sprints/{N}/0_planning_documents/code_audit.md` ext

#### Pre-Sprint Discovery Gate → write `discovery.md` (MANDATORY, HARD BLOCK)

**CRITICAL:** This step produces the **discovery witness** that the planning quality
gate (Step 5 of `sprint_planning.json`, `discovery_witness_present`) HARD-BLOCKS on.
Run discovery BEFORE finalizing story estimates — every `-0` cleanup sprint traced
back to discovery deferred to execution.

The full gate (the four checks, the witness template, and sprint-type scoping) is the
single source of truth in **[sprint_gates.md → Pre-Sprint Discovery Gate](../../_shared/sprint_gates.md)**.
Do not restate it; follow it. In summary you MUST:

1. **Paste a real baseline**, not a glance — `cargo test -j 1 --no-run` tail (or
   `pytest --collect-only` / `ruff check` for Python) **and** a `git status --short`
   with every uncommitted entry classified as disposable or sprint-dependency.
2. **Sample content claims** — for any AC asserting SOURCE content ("merge §7 of paper
   Y"), open the source and quote the claimed element. File existence is NOT enough.
3. **Plan dual-side evidence** for any transformation AC (merge/port/consolidate/dedup)
   — presence checks (grep a header, file count) may NOT mark such a story DONE.

**Write the witness to** `coda_project_planning/sprints/{N}/0_planning_documents/discovery.md` using the
template in sprint_gates.md. Placeholder rows (`TBD`, empty cells) = incomplete witness
= handoff blocked.

The per-story commands below populate **§2 of `discovery.md`** (one pasted result per story):

| Check | Command (Windows) | Command (Unix) | Story Types |
|-------|-------------------|----------------|-------------|
| Test file exists | `test -f tests/test_<feature>.py && echo EXISTS` | Same | Test coverage stories |
| Content file exists | `test -f anomalon/.../section.md && echo EXISTS` | Same | Content/lesson stories |
| API endpoint exists | `grep -r "def <endpoint>" backend/api/` | Same | API stories |
| Component exists | `test -f frontend/src/components/<Name>.tsx && echo EXISTS` | Same | Frontend stories |
| Migration exists | `ls backend/alembic/versions/*<keyword>*` | Same | Schema stories |

**Discovery Commands by Story Type:**

```bash

# For test coverage stories
test -f tests/test_<feature>.py && echo "TEST EXISTS - mark story pre-complete"

# For content/lesson stories
ls anomalon/triangles_distinction_to_everything/lesson_*/en/<section>*.md 2>/dev/null && echo "CONTENT EXISTS"

# For API endpoint stories
grep -rn "def <function_name>" backend/api/ && echo "ENDPOINT EXISTS"

# For skill update stories
test -f omega_engine/.omega_skills/<skill>/SKILL.md && echo "SKILL EXISTS"

# Count existing tests for a module
grep -c "def test_" tests/test_<module>.py 2>/dev/null || echo "0 tests"

``` ext

**If Discovery Finds Pre-Existing Work:**

1. **Verify acceptance criteria** - Does existing code meet all criteria?
2. **Run quality gates** - Do tests pass? Is code lint-clean?
3. **Mark story as pre-complete** in sprint plan (see Reference: Async Work Tracking Protocol)
4. **Adjust estimates** - Reduce points if partial implementation exists

**Witness template:** Use the single canonical template in
[sprint_gates.md → Pre-Sprint Discovery Gate](../../_shared/sprint_gates.md) and write it
to `coda_project_planning/sprints/{N}/0_planning_documents/discovery.md`. Do not maintain a second template
here (drift between the two is exactly what lets a check get skipped).

**Source:** Sprint 074 retrospective (verification sprint prevention, STORY-074-0-002);
discovery-gate consolidation from Sprints 101-0/103/104-0/104-0-0/107 retrospectives.

### Step 9: External Research Integration (Scoped to Defined Stories)

**Prerequisite:** Sprint stories must be defined (Steps 6-7 complete).

Research external skill sources when relevant to **the defined stories**:

| Source | URL | Notes |
|--------|-----|-------|
| SkillsMP | skillsmp.com | 87,000+ community skills |
| ScriptByAI | scriptbyai.com/claude-code-resource-list | Curated resources |
| ClaudeSkills | claudeskills.info | Skill collections |
| obra/superpowers | GitHub | Quality patterns |

Use WebFetch/WebSearch to gather insights scoped to the stories defined in Steps 6-7. Do NOT run broad research before the sprint goal is known.

**Document findings in** `coda_project_planning/sprints/{N}/external_skills_research.md` ext

**Source:** Sprint 069 - user preference for thorough planning with external research

### Step 10: Test Quality Review of Stories (MANDATORY - SOVIET INSPECTOR)

**CRITICAL:** Before finalizing stories, invoke `techne-code-soviet-inspector` to validate test requirements.

For EACH story that adds/modifies code:

1. **Verify "Test Requirements" section exists** in story definition
2. **Verify test file path is specified** (not "TBD" or empty)
3. **Verify assertion quality criteria are defined**

```python

# Gate Logic
for story in stories:
    if story.adds_or_modifies_code:
        if not story.test_requirements:
            VETO(f"STORY-{story.id} missing Test Requirements section")
        if not story.test_file_path or story.test_file_path in ["TBD", ""]:
            VETO(f"STORY-{story.id} has no test file path specified")
        if not story.assertion_quality_criteria:
            VETO(f"STORY-{story.id} missing assertion quality criteria")

``` ext

**VETO Action:**

``` ext
IF any story lacks proper test requirements:
  OUTPUT: "SPRINT PLANNING BLOCKED by Techne Code Soviet Inspector"
  OUTPUT: "Story {STORY-ID} missing test requirements. Cannot proceed."
  STOP: Do not finalize sprint plan until fixed

``` ext

**Required Story Test Section Format:**

```markdown

### Test Requirements
- [ ] Test type: (unit/integration/e2e)
- [ ] Test file: path/to/test_file.py (MUST be specific path)
- [ ] Coverage target: X%
- [ ] **Assertion quality criteria:**
  - [ ] Exact counts tested (no `>= 1` when specific count known)
  - [ ] All claimed behaviors have corresponding assertions
  - [ ] Downgrade tested (if migration story)
  - [ ] No tautological assertions (`assert True`, etc.)

``` ext

**Source:** Sprint Workflow Quality Enforcement (Techne Code Soviet Inspector Model)

### Step 11: Create Artifacts (MANDATORY — Templates + Gate)

**CRITICAL:** Create all 3 planning artifacts in `coda_project_planning/sprints/{N}/` BEFORE handoff to `/sprint-review`. Do NOT defer document creation to the review phase.

**PPT Document Flow (end-to-end):**

``` ext
/sprint-planning  → creates: kickoff.md, quality_gates.md, sprint_{N}_plan.md  ← YOU ARE HERE
/sprint-review    → creates: review.md (with APPROVED status)
/sprint-execution → creates: completion.md (MANDATORY before retrospective)
/sprint-retrospective → creates: retrospective.md

``` ext

**Artifacts to create:**

1. **`sprint_{N}_plan.md`** — Full sprint plan with expansive story format. **Must explicitly declare any new top-level library module additions** (e.g., adding `pub mod new_system;` to `mod.rs`) to ensure pre-sprint scaffolding is clear.
2. **`kickoff.md`** — Kickoff with team assignments and dependencies
3. **`quality_gates.md`** — Quality criteria and verification checklist

**Kickoff Template:**

```markdown

# Sprint {N} Kickoff

**Sprint:** {N}
**Date:** YYYY-MM-DD
**Type:** [Feature | Cleanup | Documentation]
**Branch:** sprint-{N}

## Sprint Goal
[Sprint goal from Step 6]

## Team
| Role | Assignment |
|------|-----------|
| Orchestrator | Blackrod |
| Facilitator | Scrum Master |
| Implementer | [assigned] |

## Capacity
- **Total:** X points across Y stories

## Story Assignments
| Story | Points | Priority | Owner |
|-------|--------|----------|-------|
| STORY-{N}-001 | X | P1 | [owner] |

## Dependencies
[List or "None"]

## Risks
| Risk | Mitigation |
|------|------------|
| [risk] | [mitigation] |

``` ext

**Quality Gates Template:**

```markdown

# Sprint {N} Quality Gates

## Gate Definitions
| Gate | Threshold | Applies To | Status |
|------|-----------|------------|--------|
| [gate] | [threshold] | [story/all] | Pending |

## Verification Checklist
- [ ] [checklist item]

## Sprint Type Classification
**Sprint type:** [Feature/Cleanup/Documentation]
**Applicable gates:** [list]
**Not applicable:** [list with reasons]

``` ext

**Artifact Verification Gate (HARD BLOCK before Step 13):**

```bash
SPRINT_DIR="coda_project_planning/sprints/{N}"
MISSING=""
test -f "$SPRINT_DIR/sprint_{N}_plan.md" || MISSING="$MISSING sprint_{N}_plan.md"
test -f "$SPRINT_DIR/kickoff.md" || MISSING="$MISSING kickoff.md"
test -f "$SPRINT_DIR/quality_gates.md" || MISSING="$MISSING quality_gates.md"

if [ -n "$MISSING" ]; then
  echo "HARD BLOCK: Cannot hand off to review. Missing:$MISSING"
  echo "Create missing artifacts before proceeding."
else
  echo "PASS - All 3 planning artifacts verified."
fi

``` ext

**Why mandatory:** Sprint 314 planning documents were created reactively during `/sprint-review` instead of proactively during `/sprint-planning`. This gate prevents that anti-pattern.

**Source:** Sprint 314 Retrospective Action Item #1

### Step 12: Submit Outcome (deactivation)

```python
Submit outcome),
    epistemic_state_id=<from_commitment>,
    agent_code="blackrod",
    actuals={
        "actual": 1,  # or 0 if failed
        "planning_completed_on_time": True,
        "stories_estimated": 12,
        "critical_blockers": 0
    },
    outcome={"status": "complete"}
)

``` ext

### Step 13: Request Handoff

After completion, inform user:

``` ext
SPRINT_PLANNING COMPLETE

Artifacts created:
- coda_project_planning/sprints/{N}/sprint_{N}_plan.md
- coda_project_planning/sprints/{N}/kickoff.md
- coda_project_planning/sprints/{N}/quality_gates.md

NEXT: Run /sprint-review to initiate sprint_planning_review workflow

``` ext

---
