# Example session

`AuthorityEffect: None.` Reference material for [`sprint-planning-review`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Example Session

``` ext
User: /sprint-review 051

Core: I'll review Sprint 051 for approval.

Loading agents: Product Owner, Blackrod, Scrum Master...

## Sprint 051 Review

Reading sprint artifacts...
- coda_project_planning/sprints/051/sprint_051_plan.md
- coda_project_planning/sprints/051/quality_gates.md

### Product Owner Review

Reviewing 9 stories totaling 21 points...

- [x] Sprint goal aligns with skill ecosystem standardization
- [x] Story priorities reflect cleanup before new features
- [x] Acceptance criteria are clear and testable
- [x] No external dependencies
- [x] Capacity appropriate for documentation sprint

Status: APPROVED

### Blackrod Quality Review

Reviewing quality gates...

| Gate | Defined | Status |
|------|---------|--------|
| YAML validation | Yes | PASS |
| Markdown lint | Yes | PASS |
| Skill loading | Yes | PASS |

- [x] Quality gates are measurable
- [x] Test requirements appropriate (documentation sprint)
- [x] No security-critical changes

Status: APPROVED

### Scrum Master Approval

- [x] Capacity matches points (21 pts, documentation focused)
- [x] Timeline realistic (5 days)
- [x] No blockers identified

Status: APPROVED

---

SPRINT_REVIEW COMPLETE

Sprint 051 has been APPROVED.

NEXT: Run /sprint-execution to begin sprint

``` ext
