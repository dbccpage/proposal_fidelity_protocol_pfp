# Sprint Workflow Compliance Checklist

**Source:** Sprint 061 Retrospective, Sprint 061-0 Cleanup (STORY-061-0-001)
**Version:** 1.0
**Date:** 2026-01-30

## Overview

This checklist ensures every sprint (primary and cleanup) follows the complete workflow.

**The workflow MUST be:**

``` ext
/sprint-planning → /sprint-review → /sprint-execution → /sprint-retrospective

``` ext

**No exceptions.** Cleanup sprints (N-0 pattern) require the same rigor as primary sprints.

---

## Phase 1: Planning (`/sprint-planning`)

### Required Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Sprint folder | `engine/research/product_planning_office/plans/engine/research/product_planning_office/plans/sprints/{N}/` | Required |
| Planning documents dir | `engine/research/product_planning_office/plans/sprints/{N}/0_planning_documents/` | Required |
| Issues dir | `engine/research/product_planning_office/plans/sprints/{N}/1_issues/` | Required |
| Sprint plan | `engine/research/product_planning_office/plans/sprints/{N}/sprint_{N}_plan.md` | Required |
| Kickoff document | `engine/research/product_planning_office/plans/sprints/{N}/kickoff.md` | Required |
| Quality gates | `engine/research/product_planning_office/plans/sprints/{N}/quality_gates.md` | Required |
| Backlog | `engine/research/product_planning_office/plans/sprints/{N}/backlog.md` | Optional (ooutwire input) |

### Pre-Flight Checks

- [ ] PostgreSQL available on port 5432
- [ ] Alembic available (`py -3.12 -m alembic --version`)
- [ ] Git branch matches sprint number
- [ ] Working directory clean (recommended)

### Completion Criteria

- [ ] All required artifacts created
- [ ] Stories use user story format
- [ ] Acceptance criteria defined per story
- [ ] Point estimates assigned
- [ ] Quality gates are measurable

---

## Phase 2: Review (`/sprint-review`)

### Required Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Review document | `engine/research/product_planning_office/plans/sprints/{N}/review.md` | Required |

### Review Checklist

- [ ] Product Owner reviewed and approved
- [ ] Blackrod quality review passed
- [ ] Scrum Master capacity check passed
- [ ] Review status is APPROVED

### Gate

**BLOCKING:** Sprint execution CANNOT begin without `review.md` containing APPROVED status.

---

## Phase 3: Execution (`/sprint-execution`)

### Pre-Execution Gate

```bash

# This check is MANDATORY before any story work begins
test -f engine/research/product_planning_office/plans/sprints/{N}/review.md && grep -q "APPROVED" engine/research/product_planning_office/plans/sprints/{N}/review.md

``` ext

### Execution Checklist

- [ ] Pre-execution gate passed
- [ ] Database migrations checked (`alembic current`, `alembic heads`)
- [ ] Stories executed in dependency order
- [ ] Quality gates validated per story
- [ ] All acceptance criteria verified

### Completion Criteria

- [ ] All stories in DONE state
- [ ] All quality gates passed
- [ ] Tests passing

---

## Evidence Path Requirements

Every DONE story must include:

- [ ] Story ID
- [ ] Changed files
- [ ] Tests run
- [ ] Test result: PASS / FAIL / NOT PROVIDED / STALE
- [ ] Reviewer/auditor
- [ ] Known limitations
- [ ] Blackrod credit decision

A story cannot be marked DONE if evidence is NOT PROVIDED or STALE.

## Fake DONE Handling

If a story is marked DONE without evidence:

1. Strip DONE credit
2. Move story to QUARANTINED or REVIEW_REQUIRED
3. Record missing evidence
4. Require VP Engineering audit before re-credit
5. Escalate repeated violations to Blackrod

---

## Phase 4: Retrospective (`/sprint-retrospective`)

### Required Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Retrospective | `engine/research/product_planning_office/plans/sprints/{N}/retrospective.md` | Required |
| Completion doc | `engine/research/product_planning_office/plans/sprints/{N}/completion.md` | Required |

### Retrospective Checklist

- [ ] Sprint metrics documented
- [ ] "What went well" captured
- [ ] "What could improve" captured
- [ ] Action items assigned owners
- [ ] Cleanup sprint created if action items exist

### Mandatory Steps

1. **Create cleanup sprint if action items exist** (Step 6.5)
   - Create `engine/research/product_planning_office/plans/sprints/{N}-0/` directory
   - Write sprint plan with stories for each action item
   - Direct user to run full workflow on cleanup sprint

2. **Capture technical debt** (Step 6.6)
   - Document in retrospective
   - Include in next sprint plan

3. **Run meta-learning** (Step 9.5)
   - Execute `/auto-improve-autoskill` or `/autoskill` ext

---

## Cleanup Sprints (N-0 Pattern)

**CRITICAL:** Cleanup sprints are NOT shortcuts. They require the FULL workflow.

### Why?

Cleanup sprints address:

- Retrospective action items
- Technical debt
- Process improvements

These deserve the same rigor as primary sprints.

### Workflow

``` ext
/sprint-planning {N}-0 → /sprint-review {N}-0 → /sprint-execution {N}-0 → /sprint-retrospective {N}-0

``` ext

### Violation Handling

Skipping any phase triggers Blackrod escalation.

---

## Skill Integration

The following skills enforce this workflow automatically:

| Skill | Enforcement |
|-------|-------------|
| `sprint-review` | Auto-triggers `/sprint-execution` after APPROVED; `/sprint-retrospective` remains a separate phase |
| `sprint-retrospective` | Directs to full workflow for cleanup sprints |
| `sprint-planning` | Documents cleanup sprint workflow requirements |
| `sprint-execution` | Blocks without review.md APPROVED status |

---

## Audit Trail

Sprint compliance can be verified via:

```bash

# Check all required artifacts exist
for phase in "sprint_*_plan.md" "kickoff.md" "quality_gates.md" "review.md" "retrospective.md"; do
  test -f "engine/research/product_planning_office/plans/sprints/{N}/$phase" && echo "PASS: $phase" || echo "FAIL: $phase"
done

``` ext

---

**Source:** Sprint 061 learning - "WE NEED TO REVIEW THESE SPRINTS THE SAME WAY EVERY TIME"
