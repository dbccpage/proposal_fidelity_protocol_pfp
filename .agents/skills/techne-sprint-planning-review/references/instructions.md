# Review instructions

`AuthorityEffect: None.` Reference material for [`sprint-planning-review`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Instructions

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

### Step 2: Load Required Agents

```python

# Product Owner for requirements review
Load agent prompt: product-owner

# Blackrod for quality approval
Load agent prompt: blackrod

# Scrum Master for facilitation
Load agent prompt: scrum

``` ext

### Step 3: Pre-Review Verification Gate & Non-Canonical File Consolidation (MANDATORY)

Run `/techne-documentation-manager` to verify sprint directory layout and consolidate non-canonical files:
1. **File & Directory Layout Verification:** Ensure all 8 canonical sprint docs exist (`kickoff.md`, `quality_gates.md`, `review.md`, `completion.md`, `retrospective.md`, `pre_sprint_checklist.md`, `README.md`, `sprint_{NNN}_plan.md`) and mandatory subdirectories `0_planning_documents/` and `1_sprint_impl_documents/` are present.
2. **Non-Canonical File Consolidation:** Mechanically move any loose non-canonical files in the sprint root folder (such as `ooutwire_backlog.md`, unclassified scratch notes, or working documents) into `0_planning_documents/` or `1_sprint_impl_documents/` before review proceeds.


**CRITICAL - HARD BLOCK:** Before starting review, verify ALL planning documents exist.

```bash

# Pre-Review Verification Gate
SPRINT_DIR="coda_project_planning/sprints/{NNN}"
MISSING=""
test -f "$SPRINT_DIR/kickoff.md" || MISSING="$MISSING kickoff.md"
test -f "$SPRINT_DIR/quality_gates.md" || MISSING="$MISSING quality_gates.md"
test -f "$SPRINT_DIR/sprint_{NNN}_plan.md" || MISSING="$MISSING sprint_{NNN}_plan.md"

# Check 0_planning_documents exists and is not empty.

# PROGRAMMATIC EXCEPTION (Sprint 108 STORY-108-005, wiring 107-0 action item #1):

# a no-code / design-spike / cleanup sprint may legitimately leave it empty. At REVIEW

# time review.md does not exist yet, so the canonical marker `0_PLANNING_DOCUMENTS_EMPTY_OK` ext

# must be declared in quality_gates.md (written at planning). Empty WITH the marker passes

# with a NOTE; empty WITHOUT it still HARD-BLOCKS.
if [ ! -d "$SPRINT_DIR/0_planning_documents" ]; then
  MISSING="$MISSING 0_planning_documents/(missing or empty)"
else
  CONTENTS=$(ls -A "$SPRINT_DIR/0_planning_documents")
  if [ -z "$CONTENTS" ]; then
    if grep -qs "0_PLANNING_DOCUMENTS_EMPTY_OK" "$SPRINT_DIR/quality_gates.md"; then
      echo "NOTE: 0_planning_documents/ empty but documented exception (0_PLANNING_DOCUMENTS_EMPTY_OK) in quality_gates.md — gate satisfied."
    else
      MISSING="$MISSING 0_planning_documents/(empty, no 0_PLANNING_DOCUMENTS_EMPTY_OK marker)"
    fi
  fi
fi
if [ -n "$MISSING" ]; then
  echo "HARD BLOCK: Cannot review. Missing:$MISSING"
  echo "ACTION: Run /sprint-planning first to create required artifacts"
  exit 1
else
  echo "Pre-review verification PASSED. Proceeding with review."
fi

``` ext

**Gate Logic:**

``` ext
IF any required planning document is missing:
  STOP review immediately
  OUTPUT: "HARD BLOCK: Cannot review sprint {NNN}. Missing: [list]"
  OUTPUT: "ACTION: Run /sprint-planning {NNN} first"
  DO NOT write review.md
  EXIT

IF 0_planning_documents/ exists but is empty:
  IF quality_gates.md contains the marker `0_PLANNING_DOCUMENTS_EMPTY_OK`:
    OUTPUT: "NOTE: empty 0_planning_documents/ honored via documented exception."
    PROCEED  # no-code / design-spike / cleanup sprint — programmatically satisfied
  ELSE:
    STOP review immediately
    OUTPUT: "HARD BLOCK: 0_planning_documents/ is empty and no 0_PLANNING_DOCUMENTS_EMPTY_OK marker"
    EXIT
  # See _shared/sprint_gates.md "Required Sprint Documents" for the canonical marker.

IF all documents exist AND have content:
  PROCEED with review steps

``` ext

**Error Messages:**

| Condition | Message |
|-----------|---------|
| Missing any planning doc | `HARD BLOCK: Cannot review sprint {NNN}. Missing: [list]`<br>`ACTION: Run /sprint-planning {NNN} first.` |
| Empty 0_planning_documents | `HARD BLOCK: 0_planning_documents/ is empty. Planning incomplete.` |
| All gates pass | `Pre-review verification PASSED. All planning documents verified.` |

**NO EXCEPTIONS:** Never write "Planning documents complete: PASS" without file existence verification.

**Source:** Sprint 087/087-0 documentation integrity audit 2026-01-31

### Step 4: Read Sprint Artifacts

```python

# Read the sprint plan
Read(file_path=f"coda_project_planning/sprints/{sprint_number}/sprint_{sprint_number}_plan.md")

# Read quality gates
Read(file_path=f"coda_project_planning/sprints/{sprint_number}/quality_gates.md")

# Read kickoff if available
Read(file_path=f"coda_project_planning/sprints/{sprint_number}/kickoff.md")

``` ext

### Step 5: Submit Commitment (activation)

```python
submit_commitment(
    sprint_id=int(sprint_number),
    agent_code="blackrod",
    task_code=f"SPRINT-{sprint_number}-REVIEW",
    predictions={
        "p_success": 0.85,
        "plan_will_be_approved": 0.80,
        "no_major_changes_required": 0.70,
        "quality_gates_adequate": 0.90
    }
)

# Save epistemic_state_id for Outcome

``` ext

### Step 6: Product Owner Review

Product Owner validates:

- [ ] Sprint goal aligns with business objectives
- [ ] Story priorities reflect value delivery
- [ ] Acceptance criteria are clear and testable
- [ ] Dependencies identified and manageable
- [ ] Capacity allocation is appropriate

**Decision Points:**

- APPROVED: Proceed to Techne Code Inspector audit
- CHANGES REQUESTED: Return to `/sprint-planning` with feedback
- BLOCKED: Escalate to ooutwire

### Step 7: Techne Code Inspector Audit (MANDATORY - BLOCKING)

**CRITICAL:** BEFORE Blackrod quality review, audit test quality on ALL test files.

**Mechanism:** Invoke the real `/techne-code-inspector` skill on the sprint's test files. The Inspector is the live test-quality enforcement authority in this repo; there is no standalone script. Treat its VETO (BLOCKED) verdict as a HARD BLOCK of the sprint review.

``` ext

# Invoke the Techne Code Inspector skill on all test files
/techne-code-inspector tests/

``` ext

**Source:** Sprint 102-0 STORY-102-0-003 — dead gate reference cleanup (tooling absent).

**Gate Logic:**

``` ext

# Audit test quality via the /techne-code-inspector skill
inspector_verdict = /techne-code-inspector tests/

IF inspector_verdict == VETO (BLOCKED):
    review_status = "BLOCKED"
    OUTPUT: "SPRINT REVIEW BLOCKED by /techne-code-inspector"
    OUTPUT: inspector findings  # List of all violations
    STOP: "Do not proceed to Step 8"

IF inspector_verdict == PASS:
    OUTPUT: "Techne Code Inspector: PASS - Test quality verified"
    PROCEED: "Continue to Step 8 (Blackrod Quality Review)"

``` ext

**VETO Conditions (ANY triggers block):**

| Condition | Example | Action |
|-----------|---------|--------|
| Weak assertion | `assert count >= 1` | BLOCKED |
| Tautological | `assert True` | BLOCKED |
| Missing downgrade test | Migration without downgrade | BLOCKED |
| Unclaimed test | Docstring claim without test | BLOCKED |

**This step is NON-NEGOTIABLE. No sprint proceeds with bad tests.**

**Output Format:**

``` ext
SPRINT REVIEW: Step 7 - Techne Code Inspector Audit

Running: /techne-code-inspector tests/

Result: [PASS/VETO]
Files scanned: N
Violations: X

[If VETO:]
BLOCKED: Sprint review cannot proceed.
Fix these issues:
- tests/test_foo.py:42 - Weak assertion >= 1
- tests/test_bar.py:88 - Missing downgrade test

[If PASS:]
APPROVED: Test quality verified. Proceeding to Blackrod review.

``` ext

**Source:** Sprint Workflow Quality Enforcement (Techne Code Inspector Model)

### Step 7.5: Core Truth Assignment Review

REMOVED (Sprint 102-0, STORY-102-0-003): the CoreAssigner engine does not exist in this repo. Core-truth review is deferred until a real implementation exists. There is no live call in this step.

**Source:** Sprint 102-0 STORY-102-0-003 — dead gate reference cleanup (tooling absent).

### Step 7.6: Current-System Gates (Governance-Strict + Contracts + Test-Tier)

Apply the modernized gates from `_shared/sprint_gates.md` → **Current-System Gates (2026-06 modernization)**:

- **Governance-Strict (scoped, HARD):** if any story expands authority / mutates doctrine / relaxes a boundary / promotes a residual, require its 10-field `GovernanceRecord` and a passing `check_governance_strict` (role-power separation; no self-cert); `PontiusIntegrityAuditor::judge` adjudicates the contract↔code binding. Otherwise confirm the `[ ] No authority change` attestation in `quality_gates.md`.
- **Contracts (scoped, HARD):** if any story touches `core_contracts` / `sentinel_councils` / authority crates, require the v1 corpus gate green (`cargo test -j 1 -p core_contracts -p sentinel_councils`). Otherwise confirm `[ ] No contract change`.
- **Test-Tier (HARD):** confirm each code story declares unit / integration / e2e in the `quality_gates.md` Test-Tier table; a behavior-adding story missing its required tier is a VETO (alongside the Step 7 Techne Code Inspector veto).

### Step 8: Blackrod Quality Review

Blackrod validates:

- [ ] Quality gates are defined and measurable
- [ ] Test requirements specified per story
- [ ] **Test quality standards enforced (see [test_quality_law.md](../../_shared/test_quality_law.md))**
- [ ] Security considerations addressed
- [ ] Performance impact assessed (see planning skill)
- [ ] Tech debt tracked appropriately

**Quality Gate Checklist:**

```markdown

| Gate | Defined | Threshold | Status |
|------|---------|-----------|--------|
| Ruff lint | [y/n] | 0 errors | |
| mypy | [y/n] | 0 errors | |
| pytest | [y/n] | All pass | |
| Coverage | [y/n] | >= X% | |
| Security | [y/n] | 0 HIGH/CRITICAL | |
| **Test quality** | [y/n] | 0 weak assertions | |

``` ext

**Test Quality Review (MANDATORY):**

| Check | Status |
|-------|--------|
| No weak assertions (`>= 1`, `>= 0`, `assert True`) | PASS/FAIL |
| All docstring claims have corresponding tests | PASS/FAIL |
| Migration tests include upgrade AND downgrade | PASS/FAIL |
| Type annotations properly guarded | PASS/FAIL |

Audit all new test files against **[test_quality_law.md](../../_shared/test_quality_law.md)** before approval.

**Decision Points:**

- APPROVED: Proceed to final approval
- CHANGES REQUIRED: Quality gates need strengthening
- BLOCKED: Critical quality concerns

### Step 8.5: Crystallization Score Check

REMOVED (Sprint 102-0, STORY-102-0-003): the CrystallizationWatchdog engine does not exist in this repo. Crystallization scoring is deferred until a real implementation exists. There is no live call in this step.

**Source:** Sprint 102-0 STORY-102-0-003 — dead gate reference cleanup (tooling absent).

### Step 9: Scrum Master Final Approval

Scrum Master confirms:

- [ ] Team capacity matches story points
- [ ] Timeline is realistic
- [ ] All blockers addressed
- [ ] Kickoff meeting can proceed

### Step 10: Submit Outcome (deactivation)

```python
submit_outcome(
    epistemic_state_id=<from_commitment>,
    agent_code="blackrod",
    actuals={
        "actual": 1,  # or 0 if rejected
        "plan_approved": True,
        "changes_requested": 0,
        "quality_gates_adequate": True
    },
    outcome={"status": "approved"}  # or "changes_requested" or "blocked"
)

``` ext

### Step 11: Document Review Outcome

**CRITICAL — Evidence path required:** For every completed ticket, you MUST record an **Evidence path** (file under `coda_project_planning/sprints/{N}/evidence/`). No path = No credit; do not list the story as DONE without a path.

Create or update `coda_project_planning/sprints/{N}/review.md`:

```markdown

# Sprint {N} Review

**Date:** YYYY-MM-DD
**Status:** APPROVED / CHANGES_REQUESTED / BLOCKED

## Product Owner Review

- Business alignment: [PASS/FAIL]
- Priority validation: [PASS/FAIL]
- Notes: [feedback]

## Blackrod Quality Review

- Quality gates: [PASS/FAIL]
- Test coverage: [PASS/FAIL]
- Security review: [PASS/FAIL]
- Notes: [feedback]

## Demo / Witness Artifacts

Do not accept text-only demo output ("It works"). Each completed ticket must have an Evidence path. No path = No credit.

Consistent naming for sprint transition evidence:
- **Planning**: `sprint_{N}_plan.md` ext
- **Audit/Review**: `sprint_vp_review.md` (formerly `vp_sadc_walkthrough.md`)
- **Retrospective**: `retrospective.md` ext

| Ticket | Status | Evidence path (required for DONE) |
|--------|--------|-----------------------------------|
| STORY-{N}-001 | DONE | coda_project_planning/sprints/{N}/evidence/STORY-{N}-001_test_report.txt |
| STORY-{N}-002 | DONE | coda_project_planning/sprints/{N}/evidence/STORY-{N}-002_screenshot_sha256.txt |
| ... | ... | ... |

(If planning-only sprint with no demo artifacts, document explicit exception and approval.)

## Scrum Master Approval

- Capacity check: [PASS/FAIL]
- Timeline check: [PASS/FAIL]
- Final status: [APPROVED/BLOCKED]

## Next Steps

[Action items if changes requested, or proceed to execution]

``` ext

### Step 12: Handoff

**If APPROVED:**

``` ext
SPRINT_REVIEW COMPLETE

Sprint {N} has been APPROVED.

Artifacts:
- coda_project_planning/sprints/{N}/review.md

NEXT: Run /sprint-execution to begin sprint

``` ext

**If CHANGES REQUESTED:**

``` ext
SPRINT_REVIEW CHANGES REQUESTED

Sprint {N} requires revisions:
- [List of required changes]

NEXT: Update sprint plan, then run /sprint-review again

``` ext

**If BLOCKED:**

``` ext
SPRINT_REVIEW BLOCKED

Sprint {N} has critical issues:
- [List of blocking issues]

NEXT: Escalate to ooutwire, resolve blockers, then restart planning

``` ext
