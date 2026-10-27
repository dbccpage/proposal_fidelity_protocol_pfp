# Execution instructions

`AuthorityEffect: None.` Reference material for [`sprint-execution`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Instructions

### Step 1: Load Agents

```python

# Lead
Load agent prompt: scrum

# Enforcer
Load agent prompt: blackrod

``` ext

### Step 2: Submit Commitment (activation)

Blackrod submits Commitment for sprint execution.

**CRITICAL: UUID Format Required**

The `start_client_request_id` and `end_client_request_id` parameters MUST be valid UUIDs:

```python
import uuid

# WRONG - will fail with "invalid input syntax for type uuid"
start_client_request_id="028-0-completion-20260112"

# CORRECT - use uuid.uuid4()
start_client_request_id=str(uuid.uuid4())

``` ext

### Step 3: Database Migration Check (MANDATORY)

Before any development begins, verify database schema is current:

```bash

# Check pending SDLC migrations
alembic -c alembic_sdlc.ini current
alembic -c alembic_sdlc.ini heads

# Check pending content migrations (if applicable)
alembic -c alembic_content.ini current

# Run pending migrations
alembic -c alembic_sdlc.ini upgrade head

``` ext

**Verification Checklist**:

- [ ] All migrations applied (`current` matches `heads`)
- [ ] ORM models match database schema
- [ ] No migration errors in logs

**Rollback Procedure** (if migration fails):

```bash

# Rollback last migration
alembic -c alembic_sdlc.ini downgrade -1

# Or rollback to specific revision
alembic -c alembic_sdlc.ini downgrade <revision_id>

``` ext

### Step 4: Branch Hygiene Verification (MANDATORY)

**CRITICAL:** Before executing ANY sprint work, verify the current branch matches the sprint.

```bash

# Get current branch
git branch --show-current

# Expected pattern: sprint-{NNN} or sprint-{NNN}-{suffix}

# Example: sprint-073, sprint-073-0

``` ext

**Gate Logic:**

``` ext
current_branch = git branch --show-current
expected_pattern = "sprint-{sprint_number}"

IF current_branch does NOT match expected_pattern:
  OUTPUT: "⚠️ WARNING: Current branch is '{current_branch}', expected 'sprint-{sprint_number}'."
  OUTPUT: "Consider: git checkout -b sprint-{sprint_number} OR git checkout sprint-{sprint_number}"
  ASK: "Proceed anyway? [y/n]"

IF current_branch matches expected_pattern:
  OUTPUT: "✓ Branch hygiene check PASSED. On branch '{current_branch}'."

``` ext

**Verification Checklist:**

- [ ] Current branch matches `sprint-{N}` or `sprint-{N}-{suffix}` pattern
- [ ] Branch name matches sprint folder number
- [ ] Uncommitted changes triaged by OWNERSHIP before assuming the branch is disposable or branching fresh from main: confirm they belong to the prior sprint (commit/stash via /github) and are NOT dependencies of this sprint. (Sprint 104 incident: 131 uncommitted changes assumed disposable were actually the content the sprint depended on.)

**Branch Creation Rule:** If starting a new sprint and no matching branch exists, create it BEFORE any work begins:

```bash
git checkout -b sprint-{NNN}

``` ext

**Source:** Sprint 073 Retrospective Action Item #1 (branch mismatch incident); Sprint 074 incident - work done on sprint-058 branch caused "missing docs" confusion

### Step 5: Sprint Cancellation Authority (MANDATORY)

**HARD RULE:** Developer agents do NOT have authority to cancel sprints.

Sprint cancellation REQUIRES explicit approval from:

- **Blackrod** (orchestrator)
- **ooutwire** (product owner)

**Before cancelling ANY sprint:**

1. STOP and request approval in conversation
2. Document cancellation reason
3. Get explicit written approval from Blackrod or ooutwire
4. Only then proceed with cancellation

**What constitutes cancellation:**

- Creating retrospective.md with CANCELLED status
- Moving sprint to archive with CANCELLED status
- Deleting sprint artifacts
- Any action that terminates an approved sprint

**Gate Logic:**

``` ext
IF story involves sprint cancellation:
  STOP execution immediately
  OUTPUT: "⚠️ AUTHORITY CHECK: Sprint cancellation requires Blackrod or ooutwire approval."
  OUTPUT: "Sprints to cancel: [list]"
  OUTPUT: "Reason: [reason]"
  ASK: "@blackrod or @ooutwire - Approve cancellation? [y/n]"

  IF approval NOT received:
    story.status = "BLOCKED"
    story.blocker = "Awaiting cancellation authority"
    DO NOT proceed with cancellation

  IF explicit approval received:
    PROCEED with cancellation
    DOCUMENT approver in retrospective.md

``` ext

**Violation Response:**

- Immediate halt of cancellation
- Revert any cancellation artifacts created
- Report to Blackrod for review

**Source:** Sprint 068 - unauthorized cancellation attempt by developer agent

### Step 6: Per-Story Commitment/Outcome Tracking (MANDATORY)

**CRITICAL:** Every story MUST submit a Commitment (predictions) at start and an Outcome (actuals) at completion. This is not optional -- it feeds the calibration system.

**Per-Story Protocol:**

``` ext
FOR each story in sprint:
  1. Commitment: Submit predictions before starting work
     - p_success: estimated probability of completion
     - expected_duration_minutes: time estimate
     - expected_outputs: files/artifacts this story will produce

  2. EXECUTE: Do the work

  3. Outcome: Submit actuals after completion
     - actual: 1 (success) or 0 (failure)
     - outputs_produced: actual files created
     - duration_minutes: actual time spent

``` ext

**Hard Gate Logic:**

``` ext
FOR each story transitioning to IN_PROGRESS:
  IF Commitment has NOT been submitted for this story:
    STOP: "BLOCKED: Story {STORY_ID} cannot start without Commitment submission."
    DO NOT begin implementation work.

FOR each story transitioning to DONE:
  IF Outcome has NOT been submitted for this story:
    STOP: "BLOCKED: Story {STORY_ID} cannot close without Outcome submission."
    DO NOT mark as DONE.
    REVERT status to IN_PROGRESS.

``` ext

**Commitment/Outcome Tracking Table (MUST appear in completion.md):**

```markdown

## Commitment/Outcome Tracking

| Story | Commitment Submitted | Outcome Submitted | p_success | actual |
|-------|----------------------|-------------------|-----------|--------|
| STORY-{N}-001 | YES/NO | YES/NO | 0.XX | 1/0 |

``` ext

**Why mandatory:** Sprint 107 retrospective found that skipping per-story Commitment/Outcome tracking means no calibration data is generated. Without Commitment/Outcome per story, the calibration system has nothing to calibrate against.

**Source:** Sprint 107 Retrospective Action Item #1, Sprint 108-0 STORY-108-0-001

### Step 7: Initialize Sprint Board

- Create/update sprint tracking
- Set story statuses to "TODO"
- Initialize burndown

### Step 8: Daily Operations

**Daily Standup (Scrum Master):**

- What was done yesterday?
- What's planned today?
- Any blockers?

**Blocker Destruction (Blackrod):**

- Identify blockers immediately
- Escalate or resolve
- Document resolution

### Step 9: Story Lifecycle

For each story:

``` ext
TODO → IN_PROGRESS → CODE_REVIEW → TESTING → DONE

``` ext

Each transition triggers:

1. Agent assignment (based on story type)
2. **Commitment submission (MUST -- see Step 6 hard gate)**
3. Work execution
4. **Outcome submission (MUST -- see Step 6 hard gate)**
5. Quality gate check

**Enforcement:** IF Commitment was not submitted before work began, STOP and submit it before proceeding. IF Outcome is missing at DONE transition, REVERT to IN_PROGRESS. See Step 6 for full gate logic.

### Step 10: Techne Code Inspector During Implementation (MANDATORY)

**CRITICAL:** Run the Techne Code Inspector **after writing tests for each story**, not just at pre-DONE gate time. Catching weak assertions early avoids rework.

**When to invoke:**

``` ext
FOR each story:
  1. Write implementation code
  1.5 PRE-STUB all referenced Rust child modules (create empty files) to prevent Cargo errors
  2. Write tests
  3. RUN STRICT INSPECTOR on new test files   ← HERE (early catch)
  4. Fix any violations immediately
  5. Continue to pre-DONE gate (Step 11)      ← Final confirmation

``` ext

**Command:**

``` ext

# Invoke the /techne-code-inspector skill on the story's new test files

# (e.g. tests/test_<story_feature>.py, or all new tests/test_*.py).

# Treat a VETO from the inspector as a hard BLOCK (do not mark DONE).

``` ext

**Source:** Sprint 102-0 STORY-102-0-003 — dead gate reference cleanup (tooling absent).

**Why during implementation (not just pre-DONE):** Sprint 107 review noted "re-audit at execution time" but the Techne Code Inspector was never formally run during execution. The pre-DONE gate (Step 11) is a final safety net, but catching issues during implementation is cheaper.

**Source:** Sprint 107 Retrospective Action Item #3

### Step 11: Pre-DONE Quality Gate (MANDATORY - PER STORY - STRICT INSPECTOR)

**CRITICAL:** BEFORE marking ANY story as DONE, run the Techne Code Inspector on that story's test files.

```python

# Gate Logic - Execute for EACH story before DONE
for story in stories_to_mark_done:
    # Identify test files for this story
    test_files = story.test_file_paths  # From story's Test Requirements section

    if not test_files:
        story.status = "BLOCKED"
        story.blocker = "No test files specified in story"
        continue

    # Invoke the /techne-code-inspector skill on the story's tests and use its verdict.
    result = invoke_techne_code_inspector_skill(test_files)  # /techne-code-inspector

    if result.verdict == "VETO":  # weak/missing/fake tests
        story.status = "BLOCKED"
        story.blocker = f"Test quality VETO: {result.violations}"
        OUTPUT: f"STORY {story.id} BLOCKED by /techne-code-inspector"
        OUTPUT: result.violations
        # DO NOT mark as DONE

    elif result.verdict == "PASS":
        story.status = "DONE"
        OUTPUT: f"STORY {story.id} test quality APPROVED"

``` ext

**Source:** Sprint 102-0 STORY-102-0-003 — dead gate reference cleanup (tooling absent).

#### Core Truth Verification (Part of Pre-DONE Gate)

REMOVED (Sprint 102-0, STORY-102-0-003): the CoreAssigner engine does not exist
in this repo. Core-truth verification is deferred until a real implementation
exists. There is no live call here.

**Source:** Sprint 102-0 STORY-102-0-003 — dead gate reference cleanup (tooling absent).

**Command to Run:**

``` ext

# Invoke the /techne-code-inspector skill on the story's test files

# (single file, or several files for a feature plus its integration tests).

# Treat a VETO from the inspector as a hard BLOCK (do not mark DONE).

``` ext

**Source:** Sprint 102-0 STORY-102-0-003 — dead gate reference cleanup (tooling absent).

**VETO Conditions (Story remains BLOCKED):**

| Condition | Result |
|-----------|--------|
| Weak assertions found | BLOCKED - fix assertions |
| Missing downgrade test | BLOCKED - add downgrade test |
| No test file exists | BLOCKED - create tests first |
| Coverage below threshold | BLOCKED - add more tests |

**DONE Requirements (ALL must pass):**

- [ ] Test file(s) exist for the story
- [ ] Techne Code Inspector returns exit code 0 (PASS)
- [ ] All acceptance criteria have corresponding assertions
- [ ] No weak assertion patterns detected
- [ ] **Witness Artifact:** Evidence path under `coda_project_planning/sprints/{N}/evidence/` exists (log, screenshot hash, or test report). No path = No credit; do not mark DONE without it.

**No story closes with weak tests or without an evidence path. Period.**

**Source:** Sprint Workflow Quality Enforcement (Techne Code Inspector Model)

### Step 12: Quality Enforcement (Blackrod)

Before any merge:

- [ ] Tests pass (100%)
- [ ] **Test quality verified (no weak assertions)** - audit against **[test_quality_law.md](../../_shared/test_quality_law.md)**
- [ ] Linter clean
- [ ] Security scan clean
- [ ] Code reviewed
- [ ] Acceptance criteria met

**Test Quality Gate (MANDATORY):**

Before marking ANY story DONE, run test quality scan:

```bash

# Check for weak assertions
grep -rn "assert.*>=\s*[01]" tests/ --include="*.py"
grep -rn "assert\s+True" tests/ --include="*.py"

``` ext

If weak assertions found, story is BLOCKED until fixed.

**Test-Tier Presence Gate (MANDATORY for code stories):**

A DONE story must have added the test tiers it declared in `quality_gates.md` (see `_shared/sprint_gates.md` → **Test-Tier Coverage**): a **unit** test for any new module, an **integration** test for cross-crate behavior, and ≥1 **e2e** path where the story adds end-to-end behavior (`cargo test -j 1 --test '*_e2e'` / `pytest -m e2e`). A behavior-adding story missing its declared tier is BLOCKED (alongside the `/techne-code-inspector` weak-test veto).

**PyO3 Register Verification Gate (CONDITIONAL — only when a PyO3 `core_core` bridge is present):**

> **Status (2026-06-19):** the PyO3 `core_core` bridge is currently **dormant** — `engine/src/lib.rs` is a stub with no `#[pymodule]`. This gate is **N/A** unless a story actually (re)introduces a PyO3 `#[pyfunction]`/`#[pyclass]` AND the bridge entry exists.

For any story that adds a `#[pyfunction]` or `#[pyclass]` to engine (bridge present), verify the register call exists in `engine/src/lib.rs` before marking DONE:

```bash

# Verify register call exists for the new module
grep -n "register" engine/src/lib.rs | grep "<module_name>"

``` ext

**Gate Logic:**

``` ext
IF story adds #[pyfunction] or #[pyclass] to a Rust module:
  VERIFY: A register call for that module exists in the core_core module register fn (engine/src/lib.rs)
  IF register call NOT found:
    STOP: "BLOCKED: Story adds pyo3 function but register call missing from lib.rs"
    DO NOT mark as DONE until register call is added and cargo check passes

``` ext

**Source:** Sprint 321 retrospective -- 4 code stories wrote pyo3 implementations but register calls were never committed to lib.rs, making all new functions unreachable from Python.

### Step 13: Verification Before Completion (MANDATORY)

**Pattern adopted from:** obra/superpowers

Before marking ANY story as DONE, verify the fix actually works:

``` ext
VERIFICATION_BEFORE_COMPLETION:
1. REPRODUCE: Can you trigger the original problem/need? (should fail before fix)
2. FIX: Apply the implementation
3. VERIFY: Does the same trigger now produce the expected result?
4. REGRESS: Run broader regression to ensure no breakage
5. DOCUMENT: Record what was verified and how

``` ext

**Verification Checklist:**

| Step | Action | Must Pass |
|------|--------|-----------|
| 1 | Reproduce original state/problem | Y |
| 2 | Apply implementation | Y |
| 3 | Verify expected behavior | Y |
| 4 | Run related tests | Y |
| 5 | Manual spot-check if UI change | Y (if applicable) |

**Anti-pattern:** Marking DONE based on "code looks right" without verification.

**Source:** obra/superpowers verification-before-completion pattern (Sprint 069)

### Step 14: Sprint Completion

When all stories DONE:

1. Final quality gate check
2. Sprint metrics compiled
3. Outcome submitted
4. **Write completion.md** (MANDATORY -- see below)
5. Handoff to retrospective

### Step 14.5: Crystallization Sweep (REMOVED)

REMOVED (Sprint 102-0, STORY-102-0-003): the CrystallizationWatchdog engine does
not exist in this repo. This step is a no-op note; there is no live call to any
crystallization sweep engine. Crystallization-sweep automation is deferred until a
real implementation exists.

**Source:** Sprint 102-0 STORY-102-0-003 — dead gate reference cleanup (tooling absent).

### Step 15: Write completion.md (MANDATORY -- BEFORE Retrospective)

**CRITICAL:** `completion.md` MUST be written as the final execution step, BEFORE `/sprint-retrospective` is invoked. The retrospective's pre-gate check requires this file.

**File existence check:** Before writing completion.md, check if it already exists (may have been pre-created during planning or partially completed during execution):

```bash
test -f "coda_project_planning/sprints/{NNN}/completion.md" && echo "EXISTS" || echo "NEW"

``` ext

- **If EXISTS:** Read the file first using the Read tool, then update sections as needed using Edit tool
- **If NEW:** Use Write tool to create the file with the full template

**Review Constraint (Witness Artifact):** Before marking any story DONE, an **Evidence path** under `coda_project_planning/sprints/{N}/evidence/` must exist (log, screenshot hash file, or test report). No path = No credit; do not mark the story as DONE without a path.

**Template:**

```markdown

# Sprint {N} Completion

**Date:** YYYY-MM-DD
**Status:** COMPLETE
**Points Delivered:** X/Y (Z%)

## Story Completion

Evidence path required for DONE. No path = No credit. Path must be under `coda_project_planning/sprints/{N}/evidence/`.

| Story | Pts | Status | Evidence path (required for DONE) | Notes |
|-------|-----|--------|-----------------------------------|-------|
| STORY-{N}-001: ... | X | DONE | coda_project_planning/sprints/{N}/evidence/STORY-{N}-001_test_report.txt | ... |
...

## Exit Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| ... | PASS/FAIL | ... |

## Quality Gates

| Gate | Status |
|------|--------|
| All tests pass | PASS/FAIL |
| ... | ... |

``` ext

**Completion Verification Gate (MANDATORY):**

Before writing completion.md, verify each code story's claimed deliverables actually exist in the codebase:

```bash

# For each code story, grep for the key deliverable
grep -n "<key_function_or_type>" <claimed_file>

``` ext

Do NOT copy story claims from the sprint plan into completion.md without verification. If a claimed change is not in the codebase, mark the story as INCOMPLETE, not DONE.

**AC disposition rule:** never mark an acceptance criterion "N/A" / "deferred" / "satisfied" without **testing its literal condition** first. If an AC says "X references Y at location Z," check location Z — not a generic reference elsewhere. A mislabeled "N/A" hides unmet scope.

**Source:** Sprint 321 retrospective -- completion.md claimed lib.rs register call changes that did not exist in the codebase. Four code stories (14 points) were marked DONE with unmet acceptance criteria. Sprint 107-0 -- AC3 mislabeled "N/A" while the inline gate did not reference the exception at its HARD-BLOCK (advisor-caught).

**Structural Verification Mode:**

When operating under a no-execute constraint (e.g., "DO NOT EXECUTE OR COMPILE"):

- Verify test existence by counting `def test_` functions (Python) or `#[test]` (Rust)
- Verify file creation by checking paths exist
- Mark quality gates as "PASS (structural)" to distinguish from execution-verified
- Document the constraint in completion.md
- Next sprint MUST include at least one execution pass to validate structural claims

**Source:** Sprint 322 -- operated under no-execute constraint; all 8 quality gates verified structurally.

**Why mandatory:** Sprint 107's retrospective was blocked by the PPT gate because completion.md was missing -- it had to be written on-the-fly during the retrospective, which defeats the purpose of the gate.

**Source:** Sprint 107 Retrospective Action Item #4

### Step 15.5: Completion Gate (MANDATORY -- HARD BLOCK)

**CRITICAL:** Before handing off to retrospective, verify completion.md exists and contains required sections.

**Gate Logic:**

``` ext
SPRINT_DIR = "coda_project_planning/sprints/{NNN}"
COMPLETION = "$SPRINT_DIR/completion.md"

IF completion.md does NOT exist:
  STOP: "HARD BLOCK: completion.md missing. Cannot hand off to retrospective."
  OUTPUT: "Write completion.md (Step 15) before proceeding."
  EXIT without handoff.

IF completion.md exists:
  content = read(COMPLETION)

  IF "Story Completion" NOT in content:
    STOP: "HARD BLOCK: completion.md missing 'Story Completion' section."
    EXIT without handoff.

  IF "Quality Gates" NOT in content:
    STOP: "HARD BLOCK: completion.md missing 'Quality Gates' section."
    EXIT without handoff.

  OUTPUT: "Completion gate PASSED. completion.md verified."

``` ext

**Error Messages:**

| Condition | Message |
|-----------|---------|
| File missing | `HARD BLOCK: completion.md does not exist in sprint folder. Write it (Step 15) before retrospective handoff.` |
| Missing Story Completion | `HARD BLOCK: completion.md exists but missing "Story Completion" header. Incomplete completion document.` |
| Missing Quality Gates | `HARD BLOCK: completion.md exists but missing "Quality Gates" header. Incomplete completion document.` |
| All checks pass | `Completion gate PASSED. completion.md verified with required sections.` |

**Why mandatory:** Sprint 301-0 retrospective was blocked because completion.md was missing at handoff time. This gate prevents that incident from recurring.

**Source:** Sprint 301-0 incident; Sprint 302 STORY-302-007

### Evidence Artifact Quality Standard (Sprint 322-0 Model)

Evidence artifacts should meet these quality criteria:

**Content requirements:**

- List all files modified with before/after line counts where applicable
- Map each acceptance criterion to specific verification (file existence, line numbers, test counts)
- Include verification commands or code excerpts demonstrating completion
- Reference quality gate verification results

**Format example** (from Sprint 322-0 STORY-001):

``` ext
STORY-322-0-001: Extract operational CoT generators into shared module
Status: DONE
Date: 2026-03-24

Files modified:
  1. engine/engine/cot_trace_generator.py (360 -> ~1013 lines)
     - Added ATP_SCAFFOLDS dict (6 domain-specific reasoning scaffolds)
     - Added LEVEL_A_HINTS dict (6 terse operational fallbacks)
     [... detailed change list ...]

Acceptance criteria verification:
  [x] cot_trace_generator.py enhanced with ATP_SCAFFOLDS, LEVEL_A_HINTS, all 11 _cot_*() -- PASS
  [x] all 12 prompt parser functions in shared module -- PASS
  [... complete checklist ...]

QG-2: test_cot_trace_generator.py has 15 new tests (>= 6 minimum) -- PASS

``` ext

**Anti-pattern:** Evidence artifacts that simply restate the story description without verification details.

**Source:** Sprint 322-0 retrospective - evidence artifact quality noted as "detailed and trace acceptance criteria to specific line numbers"

### Step 16: Handoff

``` ext
SPRINT_EXECUTION COMPLETE

Sprint {{SPRINT_NUMBER}} execution finished:
- Stories completed: X/Y
- Points delivered: Z
- Quality gates: PASSED

NEXT WORKFLOW: sprint_devops_review
REQUEST: Run /sprint-devops-review to conduct DevOps audit

``` ext
