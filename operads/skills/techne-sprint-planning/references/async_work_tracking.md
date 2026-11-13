# Async work tracking protocol

`AuthorityEffect: None.` Reference material for [`sprint-planning`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Reference: Async Work Tracking Protocol

This protocol applies when code audit (Step 8) reveals that sprint stories are **already implemented** (partially or fully). It is not a numbered planning step -- it is invoked as needed during audit.

### Identifying Pre-Completed Work

During planning, stories may be discovered as already complete if:

- Code exists that fulfills acceptance criteria
- Feature was implemented in a previous session without formal sprint tracking
- Work was done between sprints or during async development

### Marking Stories as Pre-Complete

In the sprint plan, mark pre-completed stories with:

```markdown

### [STORY-{N}-00X] Title

**Status**: COMPLETE (pre-existing implementation verified)

#### Acceptance Criteria
- [x] Criterion 1 (verified: path/to/file.py:123)
- [x] Criterion 2 (verified: path/to/other.py:456)

#### Pre-Completion Notes
- **Discovered**: YYYY-MM-DD during sprint planning code audit
- **Evidence**: [file paths, commit hashes, test results]
- **Verification**: [what was checked to confirm completion]

``` ext

### Verification Sprint Pattern

When **all stories** are pre-complete during sprint execution:

1. **During Execution**: Document as a "verification sprint" in sprint plan
2. **Run Quality Gates**: Still execute all quality checks (tests, lint, security)
3. **In Retrospective**: Record in metrics with note "verification sprint"

```markdown

## Metrics

| Metric | Planned | Actual |
|--------|---------|--------|
| Stories | 7 | 7 (100%) |
| Points | 18 | 18 (100%) |

**Finding:** Sprint {N} was a "verification sprint" - all work had been
completed in prior sessions. Sprint execution validated deliverables and
ran quality gates.

``` ext

4. **Action Item**: If this pattern recurs, consider:
   - More frequent sprint execution to catch completed work sooner
   - Explicit "development sprint" vs "verification sprint" distinction
   - Better tracking of work done between sprints

### 0-Point Verification Stories

When a cleanup sprint contains items that were **already completed** before sprint execution begins (e.g., a retrospective action item that was addressed in the previous sprint's final commit), use 0-point verification stories to track them without inflating velocity.

**When to use:**

- Item was completed before the cleanup sprint started
- Cleanup sprint needs to verify/document the completion, not implement it
- The work was done as part of a prior sprint or async work

**When NOT to use:**

- Item requires new implementation (use normal point estimates)
- Item is only partially complete (estimate remaining work)
- Regular feature sprints (0-point stories are specific to cleanup/verification contexts)

**Format template:**

```markdown

### [STORY-{N}-00X] Verify: {description}

**Status**: COMPLETE (pre-existing implementation verified)
**Points**: 0 (verification only)
**Label**: verification

#### Acceptance Criteria
- [x] Criterion 1 (verified: path/to/evidence)

#### Pre-Completion Notes
- **Completed in**: Sprint {M} / commit {hash}
- **Verified**: YYYY-MM-DD during cleanup sprint planning

``` ext

**Impact on velocity:**

- 0-point stories are **excluded** from velocity calculations
- They count toward story completion percentage but not point totals
- Retrospective should note: "N stories were 0-point verifications"

**Source**: Sprint 307-0 retrospective action item #1

### Retrospective Handling

When documenting sprints with pre-completed work:

- Acknowledge the pattern in "What Could Improve"
- Track as action item: improve async work tracking
- Do NOT artificially inflate velocity - note actual development timing
- Consider cleanup sprint if process improvements needed

**Source**: Sprint 046 retrospective (verification sprint pattern discovered)

### Real-Time Async Work Tracking

To **prevent** verification sprints, track work as it happens:

**When work is done outside a sprint:**

1. **Create async work log** in current or next sprint folder:

   ``` ext
   coda_project_planning/sprints/{N}/async_work_log.md
   ``` ext

2. **Log format:**

   ```markdown
   ## Async Work Log

   ### YYYY-MM-DD: [Brief Description]
   - **What:** [What was implemented]
   - **Why:** [Why it was done outside sprint]
   - **Files:** [Key files changed]
   - **Commit:** [Commit hash if applicable]
   - **Points estimate:** [Rough estimate]
   - **Sprint impact:** [Which planned story this affects, if any]
   ``` ext

3. **During next sprint planning:**
   - Review async_work_log.md
   - Mark affected stories as pre-complete or adjust scope
   - Include async work in velocity calculations

**When to log async work:**

- Bug fixes done urgently outside sprint
- Exploratory work that resulted in implementation
- User-requested changes between sprints
- Opportunistic improvements during other work

**REMINDER:** When implementing ANY feature outside an active sprint:

1. Stop and ask: "Should I log this in async_work_log.md?"
2. If the work would take more than 1 story point (>1 hour), LOG IT
3. If the work affects any planned story in any sprint, LOG IT

**Creating async_work_log.md:**

Create the log file when:

- Starting unplanned implementation work
- Completing a bug fix outside sprint context
- Finishing exploratory work that resulted in code changes

```bash

# Create async work log for next sprint
touch coda_project_planning/sprints/{NEXT_SPRINT}/async_work_log.md

``` ext

**Async Work Log Template:**

```markdown

# Async Work Log

This file tracks work completed outside formal sprint execution.
Review during sprint planning to identify pre-completed stories.

---

## Entry Template

### YYYY-MM-DD: [Brief Description]

- **What:** [What was implemented - be specific]
- **Why:** [Why it was done outside sprint]
- **Files Changed:**
  - `path/to/file1.py` - [what changed]
  - `path/to/file2.py` - [what changed]
- **Tests Added/Modified:** [test file paths or "none"]
- **Commit:** [commit hash if applicable, or "uncommitted"]
- **Points Estimate:** [1/2/3/5/8]
- **Sprint Impact:** [STORY-XXX-YYY or "none"]
- **Quality Gates Run:** [y/n - did you run tests/lint?]

---
``` ext

**Source**: Sprint 053 retrospective action item (STORY-053-0-001), Sprint 074 action item (STORY-074-0-001)

---
