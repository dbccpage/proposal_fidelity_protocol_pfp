# Retrospective instructions

`AuthorityEffect: None.` Reference material for [`sprint-retrospective`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Instructions

### Step 1: Load Facilitator

```python
Load agent prompt: scrum

``` ext

### Step 2: Submit Commitment (activation)

Scrum Master submits Commitment.

### Step 3: Present Sprint Metrics

Scrum Master presents:

- Stories completed vs planned
- Points delivered vs committed
- Quality gate pass rate
- Blocker count and resolution time
- Team velocity trend
- **Async work discovered** (pre-complete stories from code audit)

**Async Work Check:**

- [ ] Review `coda_project_planning/sprints/{N}/async_work_log.md` if it exists
- [ ] Note any work done between sprints that affected this sprint
- [ ] If verification sprint pattern occurred, flag for process discussion

### Step 4: Techne Code Inspector Retrospective Report (MANDATORY)

During the metrics presentation, include test-quality enforcement statistics for the sprint.

**Gather Inspector Metrics:**

```bash

# Count VETO events in sprint logs (if tracked)
grep -r "VETO" coda_project_planning/sprints/{N}/ | wc -l

# Count weak assertions found and fixed
git log --oneline --grep="weak assertion" -- tests/

# Run final inspector check on all tests:

# invoke the /techne-code-inspector skill on tests/ (its VETO is the test-quality block).

``` ext

**Source:** Sprint 102-0 STORY-102-0-003 — dead gate reference cleanup (tooling absent): the
nonexistent `scripts/test_quality_inspector.py` is repointed to the real `/techne-code-inspector` skill.

**Present in Retrospective:**

| Metric | Value | Notes |
|--------|-------|-------|
| VETO events issued | X | Times inspector blocked workflow |
| Stories blocked by inspector | Y | Stories that failed pre-DONE gate |
| Commits blocked by inspector | Z | Commits rejected for test quality |
| Violations found and fixed | N | Total weak assertions corrected |
| Final test quality status | PASS/FAIL | Current state at sprint end |

**Include in retrospective.md:**

```markdown

## Techne Code Inspector Report

### Test Quality Enforcement Metrics

| Metric | Value |
|--------|-------|
| VETO events | X |
| Stories blocked | Y |
| Commits blocked | Z |
| Violations fixed | N |

### Lessons Learned: Test Quality

- What patterns triggered VETOs?
- Were any VETOs overridden? By whom? Why?
- Should any new patterns be added to inspector?
- Were there false positives that need tuning?

### Action Items

| Action | Owner | Priority |
|--------|-------|----------|
| [Pattern to add/remove] | [Agent] | [P1/P2] |

``` ext

**Why mandatory:** Without tracking enforcement metrics, we cannot measure whether the Techne Code Inspector is effective or needs tuning.

**Source:** Sprint Workflow Quality Enforcement (Techne Code Inspector Model)

### Step 5: Architect Lightning Rounds (1 min each)

Each architect presents:

- **What went well**
- **What could improve**
- **One action item**

Participants:

```python
architects = [
    "rust-principal-developer (level=architect)",
    "database_sme",
    "devops_dev (level=architect)",
    "security_dev (level=architect)",
    "qa_dev (level=architect)",
]

``` ext

### Step 6: Blackrod Independent Assessment & Audit (Official Check 2)

Blackrod executes Official Check 2 (independent of documentation manager):

- Independent audit of sprint files, delivered work, deferred work, missing work, and test quality/coverage
- Checks alignment with parent Epic plan doc (`epic_{slug}_plan.md`) and parent Saga plan doc (`saga_{slug}_plan.md`)
- Verifies that ONLY `OOUTWIRE` and `BLACKROD` have signed off any completed epic
- Quality enforcement summary, blockers destroyed, escalations handled
- Team health assessment & test quality metrics

### Step 7: Action Items

Capture:

- **Start doing:** New practices to adopt
- **Stop doing:** Practices to abandon
- **Continue doing:** Practices working well

### Step 8: Create Cleanup Sprint (MANDATORY)

**CRITICAL:** Action items MUST become tracked stories. Do NOT skip this step.

**NO JUDGMENT CALLS:** Do not assess whether items "warrant" a cleanup sprint.
If there are action items, create the sprint. The rule is binary:

- Action items exist → Create Sprint N-0
- No action items → No cleanup sprint needed

Violation of this step triggers Blackrod escalation. (Sprint 041 Learning)

For each action item from the retrospective:

1. Create `coda_project_planning/sprints/{N}-0/` directory (cleanup sprint)
2. Write `sprint_{N}-0_plan.md` with stories for EACH action item
3. Link action items in retrospective to their story codes

```bash
mkdir -p coda_project_planning/sprints/{N}-0

``` ext

```markdown

# Sprint {N}-0: Cleanup Sprint

**Source:** Sprint {N} Retrospective Action Items

## Sprint Backlog

| Story | Points | Priority | Owner | Source |
|-------|--------|----------|-------|--------|
| STORY-{N}-0-001: [Action Item 1] | X | P1 | owner | Retro Action #1 |
| STORY-{N}-0-002: [Action Item 2] | X | P2 | owner | Retro Action #2 |
...

``` ext

**Why mandatory:** Action items documented but not tracked get lost. Every retrospective that produced action items MUST produce a cleanup sprint. Sprint N-0 must complete before Sprint N+1 starts.

**CRITICAL:** After creating the cleanup sprint, inform user to run the FULL workflow:

``` ext
NEXT: Run /sprint-planning {N}-0 to begin cleanup sprint workflow

``` ext

Do NOT offer to skip directly to execution. Cleanup sprints require:
`/sprint-planning` → `/sprint-review` → `/sprint-execution` → `/sprint-retrospective` ext

**Source:** Sprint 061-0 - cleanup sprints need full workflow like primary sprints

### Step 9: Capture Technical Debt and Deferred Work (MANDATORY)

**CRITICAL:** All technical debt and deferred items MUST be tracked in the NEXT sprint's plan.

When writing the retrospective, capture in the "Technical Debt Created" table:

- Missing tests identified (e.g., "Navigation component tests missing")
- Deferred stories that didn't fit current sprint
- Code quality issues discovered but not fixed
- Accessibility, performance, or security gaps

For EACH item, specify:

| Item | Priority | Target Sprint |
|------|----------|---------------|
| [Specific debt item] | High/Medium/Low | {N+1} or {N+2} |

Then in the NEXT sprint's plan (or a dedicated tech debt sprint):

1. Create stories from each tech debt item
2. Include "Source: Sprint {N} Retrospective" in story description
3. Add to "Tech Debt Tracking" table in quality_gates.md

**Why mandatory:** Tech debt that isn't tracked compounds. Missing tests lead to regressions. Deferred work that isn't captured is work that will be rediscovered painfully later.

### Step 9.5: Batch Signal Extraction (REMOVED — tooling absent)

> **REMOVED (Sprint 102-0, STORY-102-0-003):** the crystallizer engine does not exist
> in this repo. There is no live call in this step. Batch signal extraction is deferred until a real
> implementation exists. The gate logic and report template below are retained for reference only.

**Source:** Sprint 102-0 STORY-102-0-003 — dead gate reference cleanup (tooling absent).

**Gate Logic:**

``` ext
IF signals["patterns_detected"] == 0:
  OUTPUT: "WARNING: No patterns detected in EventSpine for Sprint {N}."
  OUTPUT: "Verify EventSpine dual-write is enabled."
  # SOFT gate — proceed but flag for investigation

IF signals["patterns_crystallized"] > 0:
  OUTPUT: f"CRYSTALLIZED: {signals['patterns_crystallized']} patterns promoted to Bedrock constants"
  # Record in retrospective.md under Signal Extraction Report

IF signals["patterns_detected"] > 0 AND signals["patterns_crystallized"] == 0:
  OUTPUT: f"PENDING: {signals['patterns_detected']} patterns detected but below crystallization threshold"
  OUTPUT: "Will accumulate across sprints."

``` ext

**Signal Extraction Report Template (add to retrospective.md):**

```markdown

## Signal Extraction Report (P4 — Batch Signal Extraction)

| Metric | Value |
|--------|-------|
| Patterns Detected | {patterns_detected} |
| Patterns Crystallized | {patterns_crystallized} |
| New Bedrock Constants | {count} |
| EventSpine Events Scanned | {events_scanned} |

### Crystallized Patterns

| Pattern ID | Occurrences | Status | Bedrock Constant |
|-----------|-------------|--------|-----------------|
| PAT-001 | N | Crystallized | CONST_NAME |

``` ext

**Source:** Sprint 151 mandate — Batch Signal Extraction as mandatory automated gate

### Step 9.6: Web Edit Detection (MANDATORY AUTOMATED GATE)

**CRITICAL:** Detect any edits made via GitHub web interface during the sprint that bypassed the standard workflow.

```bash

# Detect web edits in sprint branch commits
git log --format="%H %s" sprint-{N}..HEAD | while read hash msg; do
  # Check if commit was made via GitHub web (no GPG signature + single-file change)
  file_count=$(git diff-tree --no-commit-id --name-only -r "$hash" | wc -l)
  author_email=$(git log -1 --format="%ae" "$hash")

  if [[ "$author_email" == *"users.noreply.github.com"* ]] && [[ "$file_count" -le 2 ]]; then
    echo "WEB_EDIT_DETECTED: $hash — $msg"
  fi
done

``` ext

**Gate Logic:**

``` ext
IF web_edits_detected > 0:
  OUTPUT: f"WARNING: {web_edits_detected} web edits detected during Sprint {N}"
  OUTPUT: "Web edits bypass pre-commit hooks and CI validation."
  OUTPUT: "ACTION: Verify each web edit passes sovereign_inversion.py"

  # Run sovereign inversion on affected files
  for edit in web_edits:
    run_sovereign_inversion(edit.files)

  # NOT a hard block, but MUST be documented in retrospective
  ADD_TO_RETROSPECTIVE: "Web Edit Audit" section

``` ext

**Web Edit Audit Template (add to retrospective.md):**

```markdown

## Web Edit Audit (P2 — Web Edit Detection)

| Commit | Author | Files Changed | Sovereign Inversion | Status |
|--------|--------|---------------|---------------------|--------|
| {hash} | {author} | {files} | PASS/FAIL | Verified/Needs Fix |

``` ext

**Source:** Sprint 151 mandate — Web Edit Detection as mandatory automated gate

### Step 9.7: Techne Documentation Manager Audit Pass (Official Check 1)

Run `/techne-documentation-manager` to execute Official Check 1:
1. Verify mandatory subdirectories exist (`0_planning_documents/`, `1_sprint_impl_documents/`).
2. Verify all 8 canonical sprint docs exist (`sprint_NNN_plan.md`, `pre_sprint_checklist.md`, `kickoff.md`, `review.md`, `quality_gates.md`, `completion.md`, `retrospective.md`, `README.md`).
3. Verify at least one parent **Epic Plan document** and one parent **Saga Plan document** exist.
4. Sign off on all sprint docs and stamp the plan document header with **`DOC_MGR_REVIEWED: <YYYY-MM-DD>`**.
5. Immediately notify **`blackrod`** to execute Official Check 2.

### Step 9.8: Forgery Nemesis Escalation Cascade (FORGERY BREACH TRIGGER)

If either `techne-documentation-manager` or `blackrod` discovers signature forgery or unauthorized completion sign-off during retrospective:
1. **Activate Nemesis:** Immediately invoke `/thanatos-nemesis` for emergency quarantine.
2. **Notify VP of Engineering:** Notify `techne-vp` during `/sprint-vp-briefing`.
3. **Notify Senior VP of Engineering:** Notify `techne-svp` via executive report from `/sprint-svp-briefing`.
4. **Log Investigation:** Create investigation report in `engine/sentinel_councils/councils/blackrod/investigations/investigation_{YYYYMMDD}_{breach_id}.md`.

### Step 10: Document

Create `coda_project_planning/sprints/{N}/retrospective.md` (Meta-Learning table is filled in Step 13; hashes are produced in Steps 11–12 and recorded in Step 13):

```markdown

# Sprint {{SPRINT_NUMBER}} Retrospective

**Date:** YYYY-MM-DD
**Facilitator:** Scrum Master

## Metrics

| Metric | Planned | Actual |
|--------|---------|--------|
| Stories | X | Y |
| Points | X | Y |
| Quality Gates | 100% | Z% |

## What Went Well

- [List]

## What Could Improve

- [List]

## Action Items

| Action | Owner | Due |
|--------|-------|-----|
| [Action] | [Agent] | [Date] |

## Team Health

[Blackrod assessment]

## Deferred Work (from Plan)

| Item | Target |
|------|--------|
| [Deferred item from sprint plan] | Sprint N+1 |

## Meta-Learning (REQUIRED — retro INVALID without both hashes)

| Field | Value |
|-------|--------|
| Autoskill Hash | \<produced in Step 11, recorded in Step 13\> |
| Improve Autoskill Hash | \<produced in Step 12, recorded in Step 13\> |

``` ext

**Source:** Sprint 122 session -- user added deferred work tracking to retrospective

### Step 10.5: CrystallizationWatchdog Final Sweep (REMOVED — tooling absent)

> **REMOVED (Sprint 102-0, STORY-102-0-003):** the `CrystallizationWatchdog` engine
> (`engine.engines.crystallization_watchdog`) does not exist in this repo. There is no live
> call in this step. The crystallization sweep is deferred until a real implementation exists.

**Source:** Sprint 102-0 STORY-102-0-003 — dead gate reference cleanup (tooling absent).

### Step 11: Autoskill Latch — Run /autoskill (BLOCKING)

**CRITICAL:** The retrospective MUST NOT close until this step, Step 12, Step 13 (recording hashes in `retrospective.md`), and Step 14 (Submit Outcome) are complete.

1. Run `/autoskill`.
2. Apply approved proposals; if any commit is made to engine/.core_skills/ (e.g. chore(autoskill):), note the commit hash.
3. **Autoskill Hash** = that commit hash, or `none` if no skill commit was made.

### Step 11.5: Core Doctrine Refresh (Sprint-Close)

Fire the two core-doctrine update channels defined in `autoskill` ext
(`## Core Doctrine Wiring`) and governed by
`.claude/skills/_shared/meta_skill_governance.md`:

1. **Channel 1 (always):** regenerate the Wizard manifest from source-of-truth
   and commit it if it changed:

       python .claude/skills/panep-math-and-physics-prof/regen_spine_index.py

2. **Channel 2:** the `/autoskill` run in Step 11 applies any session-sourced
   GT*/Wizard doctrine edits (auto-commit, no approval gate); follow with
   `/auto-symmetry-hunter` so the six GT* skills stay consistent.

### Step 12: Improve-Autoskill Latch — Run /auto-improve-autoskill (DEPRECATED)

- skip

### Step 13: Record hashes in retrospective.md

Update `coda_project_planning/sprints/{N}/retrospective.md`: set **Autoskill Hash** in the Meta-Learning table. If missing, the artifact is INVALID and the retrospective must not be closed.

### Step 13.5: Version Control Commit (MANDATORY LATCH)

**CRITICAL:** To prevent loss of the sprint's code and evidence, you MUST commit the repository state.
**Stage EXPLICITLY — never `git add -A`/`git add .`** (Sprint 121: a blanket add by a concurrent agent swept a
233k-line unrelated purge into the sprint commit). List the sprint's own paths:

```bash
git add coda_project_planning/sprints/{SPRINT_NUMBER}/ <other named sprint paths>
git status --short   # eyeball: ONLY this sprint's files staged; nothing else
git commit -m "chore(sprint): complete Sprint {SPRINT_NUMBER} and retrospective"

``` ext

Record the resulting Git Commit Hash to include in your final handoff.

### Step 14: Submit Outcome (deactivation)

Scrum Master submits Outcome.

### Step 15: Close

``` ext
SPRINT_RETROSPECTIVE COMPLETE

Sprint {{SPRINT_NUMBER}} retrospective documented:
- coda_project_planning/sprints/{{SPRINT_NUMBER}}/retrospective.md
- Meta-Learning: Autoskill Hash and Improve Autoskill Hash recorded (or none)
- Git Commit: <commit-hash>

Action Items: X (ALL TRACKED in Sprint {{SPRINT_NUMBER}}-0)
Improvements Identified: Y
Cleanup Sprint: coda_project_planning/sprints/{{SPRINT_NUMBER}}-0/sprint_{{SPRINT_NUMBER}}-0_plan.md

SPRINT CYCLE COMPLETE

Next steps:
1. Execute cleanup sprint: /sprint-execution {{SPRINT_NUMBER}}-0
2. Then start next sprint: /sprint-planning {{NEXT_SPRINT}}

``` ext

**Gate:** Do not output "SPRINT CYCLE COMPLETE" until Steps 11–14 are done and retrospective.md contains both Autoskill Hash and Improve Autoskill Hash.
