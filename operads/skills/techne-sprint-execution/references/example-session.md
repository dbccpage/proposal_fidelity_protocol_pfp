# Example session

`AuthorityEffect: None.` Reference material for [`sprint-execution`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Example Session

``` ext
User: /sprint-execution 055

Omega: I'll begin execution of Sprint 055.

**Pre-Execution Gate:**
  Checking planning documents...
  - kickoff.md: EXISTS
  - quality_gates.md: EXISTS
  - sprint_055_plan.md: EXISTS
  - review.md: EXISTS (Status: APPROVED)
  Pre-execution gate PASSED. All 4 planning documents verified.

**Commitment/Outcome Readiness:** Tools available. Per-story tracking enabled.

**Branch Hygiene:** On branch 'sprint-055'. Branch check PASSED.

**Database Migration:** alembic current matches heads. Schema is current.

Executing 3 stories (10 points)...

### STORY-055-001: Add Techne Code Soviet Inspector pre-DONE gate (3 pts)

Commitment submitted: p_success=0.85

Implementing pre-DONE gate logic in sprint-execution skill...
Writing tests in tests/test_techne_code_soviet_inspector.py...
Running Techne Code Soviet Inspector on new tests... PASS

Outcome submitted: actual=1

Status: DONE

[... remaining stories ...]

**Sprint Completion:**
- Stories completed: 3/3
- Points delivered: 10/10
- Quality gates: PASSED

Writing completion.md...

SPRINT_EXECUTION COMPLETE

NEXT: Run /sprint-devops-review to conduct DevOps audit

``` ext
