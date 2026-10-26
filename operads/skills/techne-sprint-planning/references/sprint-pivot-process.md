# Sprint pivot process

`AuthorityEffect: None.` Reference material for [`sprint-planning`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Reference: Sprint Pivot Process

This process applies when sprint scope changes significantly mid-flight. It is not a numbered planning step -- it is invoked as needed during execution.

### Pivot Triggers

A pivot is required when:

- User requests fundamentally different work than planned
- Blocker makes original plan unachievable
- External priority change (e.g., production incident)
- Discovery during execution invalidates original stories

A pivot is NOT required for:

- Minor story adjustments (clarification, small scope tweaks)
- Story reordering within same sprint goal
- Adding small related stories under original theme

### Pivot Approval

``` ext
IF pivot requested:
  1. DOCUMENT pivot reason in sprint folder
  2. GET user approval for new direction
  3. UPDATE sprint plan with new stories
  4. KEEP original plan for comparison
  5. PROCEED with new scope

``` ext

### Pivot Documentation

Create `coda_project_planning/sprints/{N}/pivot.md`:

```markdown

# Sprint {N} Pivot

**Date:** YYYY-MM-DD
**Original Goal:** [original sprint goal]
**New Goal:** [revised sprint goal]
**Reason:** [why pivot was necessary]

## Original Stories (Cancelled/Deferred)

| Story | Points | Disposition |
|-------|--------|-------------|
| STORY-{N}-001 | X | Cancelled / Deferred to Sprint {M} |

## New Stories (Added)

| Story | Points | Rationale |
|-------|--------|-----------|
| STORY-{N}-NEW-001 | X | [why added] |

## Approval

- [ ] User approved pivot
- [ ] Original plan preserved
- [ ] New stories defined
- [ ] Retrospective will track pivot outcome

``` ext

### Retrospective Integration

When a sprint pivots, the retrospective MUST include:

```markdown

## Sprint Pivot Analysis

| Metric | Planned | Actual (Post-Pivot) |
|--------|---------|---------------------|
| Original stories | X | Y completed |
| Pivot stories | Z | W completed |
| Total points | A | B |

**Pivot Effectiveness:**
- Was the pivot justified? [y/n + evidence]
- What was learned? [lessons]
- Process improvement: [if any]

``` ext

**Source**: Sprint 058 Retrospective Action Item #2
