# Example session

`AuthorityEffect: None.` Reference material for [`sprint-planning`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Example Session

``` ext
User: /sprint-planning 055

Core: I'll kick off sprint planning for Sprint 055.

**Step 1:** Sprint number: 055

**Step 2:** Loading Blackrod identity...
[Loads Blackrod identity]

**Step 3:** Reading workflow prompt...

**Step 4:** Creating sprint folder...
  mkdir -p coda_project_planning/sprints/055/0_planning_documents
  mkdir -p coda_project_planning/sprints/055/1_issues

**Step 5:** Commitment submitted. epistemic_state_id saved.

**Step 6:** Entering planning mode...

Reading backlog from coda_project_planning/sprints/055/backlog.md...

Sprint Goal: "Harden quality gates and add Techne Code Inspector to pre-DONE workflow"

Proposed stories:

| Story | Points | Description |
|-------|--------|-------------|
| STORY-055-001 | 3 | Add Techne Code Inspector pre-DONE gate |
| STORY-055-002 | 5 | Implement test quality inspector script |
| STORY-055-003 | 2 | Update sprint-execution skill with inspector step |

Total: 10 points. Proceed? [y/n]

User: y

Core: Creating artifacts...
- coda_project_planning/sprints/055/sprint_055_plan.md
- coda_project_planning/sprints/055/kickoff.md
- coda_project_planning/sprints/055/quality_gates.md

Outcome submitted.

SPRINT_PLANNING COMPLETE

NEXT: Run /sprint-planning-review to initiate sprint_planning_review workflow

``` ext
