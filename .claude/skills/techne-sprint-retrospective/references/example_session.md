# Example session

`AuthorityEffect: None.` Reference material for [`sprint-retrospective`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Example Session

``` ext
User: /sprint-retrospective 055

Core: I'll run the Sprint 055 retrospective.

**Pre-Retrospective Gate:**
  Checking prerequisite documents...
  - kickoff.md: EXISTS
  - quality_gates.md: EXISTS
  - sprint_055_plan.md: EXISTS
  - review.md: EXISTS
  - completion.md: EXISTS
  Pre-retrospective gate PASSED. All 5 documents verified.

**Step 1:** Loading Scrum Master facilitator...

**Step 3:** Sprint 055 Metrics:
  - Stories: 3 planned, 3 completed (100%)
  - Points: 10 planned, 10 delivered (100%)
  - Quality gates: 100% pass rate
  - Blockers: 0

**Step 4:** Techne Code Inspector Report:
  | Metric | Value |
  | VETO events | 0 |
  | Violations fixed | 2 |
  | Final status | PASS |

**Step 6:** Blackrod Assessment: Team health GREEN. No escalations.

**Step 7:** Action Items:
  | Action | Owner | Priority |
  | Add inspector to CI pipeline | devops | P2 |

**Step 8:** Creating cleanup sprint coda_project_planning/sprints/055-0/...

**Step 10:** Writing retrospective.md...

**Step 11:** Running /autoskill...
  Autoskill Hash: abc1234

**Step 13:** Recording hashes in retrospective.md...

SPRINT_RETROSPECTIVE COMPLETE

Sprint 055 retrospective documented.
Action Items: 1 (tracked in Sprint 055-0)
SPRINT CYCLE COMPLETE

Next steps:
1. Execute cleanup sprint: /sprint-execution 055-0
2. Then start next sprint: /sprint-planning 056

``` ext
