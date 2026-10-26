---
name: techne-sprint-execution
description: "Orchestrates agile sprint execution, task breakdown, burn-down tracking, and blocker escalation."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# techne-sprint-execution

**Files:**

## Stage: Retrospective (created after execution)

**Files:**

## Stage: Execution (created during execution)

**Files:**

## Stage: Review (must exist before execution)

**Files:**
**Directories:**

## Stage: Planning (must exist before execution)

## PPT Document Flow

**CRITICAL: All planning documents must exist BEFORE execution begins.**

## Required Sprint Documents

**Source:** Sprint 0021-0022 MSS-N Grammar Pipeline implementation, Sprint 0025 Retrospective

### Test Pipeline Modification Care

**Source:** Sprint 103-0 session - ooutwire directive: "Blackrod should not orchestrate sprints. He can if asked, since he has god-level rights, but we need an orch team."
**Blackrod Role:** Auditor/Enforcer only, NOT orchestrator.

### Governance Model (Sprint 104)

**Source:** Sprint 103-0 session - ooutwire correction: "Create sprint plans before we change anything. You have a vibe coder's mental illness."
**CRITICAL:** Do not start implementing code changes before sprint planning is complete.

### Anti-Pattern: Vibe Coding

**Source:** Sprint 058 Retrospective Action Item #1, PPT failures 2026-01-30
**NO EXCEPTIONS:** Do not proceed with "we'll document later" - this caused PPT failures in Sprints 062, 063.
**Source:** Sprint 112 Retrospective Action Item #2 (zero Commitment submissions due to tools being wired mid-sprint), Sprint 113-0 STORY-113-0-001
**This is a WARNING, not a BLOCK.** Sprints can proceed without Commitment/Outcome tools (e.g., prompt-only sprints, tooling unavailable). However, the warning ensures the gap is visible and documented rather than silently ignored.
**Troubleshooting sequence when Commitment/Outcome tools fail:**

### Commitment/Outcome Readiness Check (SOFT GATE)

### Error Messages

### Gate Logic

### Gate Check

**Source:** Sprint 084 - attempted implementation before planning workflow
**Correct response:** "I'll run /sprint-planning to create the official artifacts first."
**Wrong response:** "I'll implement this plan directly."
**CRITICAL:** A detailed sprint plan provided in conversation is INPUT to the planning workflow, NOT a bypass of it.

### Plan Document vs Workflow Bypass

**CRITICAL - HARD BLOCK:** Before executing ANY sprint work, verify ALL planning documents exist.

## Pre-Execution Gate (MANDATORY)

**Source:** Sprint 108 -- user correction (2026-02-05)
**Agent Source:** Primary agents live in `.agents/agents/` (materialized capability slices).

## Prerequisites

**Shared gates** (IAK-007, already-committed check, cleanup sprint, required documents, pre-execution gate, + Current-System Gates: contracts · governance-strict · test-tier · obstruction/clippy · worktree-isolation · devops-review): See [sprint_gates.md](../_shared/sprint_gates.md).

## When to Activate

## description: Kickoff the sprint_execution workflow. Scrum Master leads daily operations, Blackrod enforces quality. Use after /sprint-review approves. Triggers on "/sprint-execution", "start sprint", "begin sprint"

**Rationale**: Sprint documents provide traceability, enable review, and ensure proper workflow. Implementation without documentation is unacceptable.

## Workflow Overview

Sprint execution is **event-driven**, not step-based:

| Event | Handler | Action |
| ------- | --------- | -------- |
| Story started | rust-principal-developer | Begin implementation |
| PR created | code_reviewer | Review code |
| PR merged | devops | CI/CD pipeline |
| Tests pass | qa_dev | Verify acceptance |
| Story done | scrum_master | Update burndown |

**Execution instructions:** See [`instructions.md`](references/instructions.md).

## Event Handlers

| Event | Agent | Response |
|-------|-------|----------|
| `story.started` | rust-principal-developer | Begin coding |
| `pr.created` | code_reviewer | Review PR |
| `pr.approved` | devops | Merge and deploy |
| `tests.passed` | qa_dev | Verify acceptance |
| `story.blocked` | blackrod | Destroy blocker |
| `quality.failed` | blackrod | Reject and escalate |

## Burndown Tracking

Track daily:

- Points remaining
- Stories in each state
- Blockers active
- Team velocity

**Agent progress monitoring:** See [`agent-progress-monitoring.md`](references/agent-progress-monitoring.md).

## UROS Tier Mapping

| Sprint Phase | UROS Tier | CODEX Lambda | Sovereign Role | 4E Mode |
|-------------|-----------|-------------|---------------|---------|
| Sprint Execution | Tier 7 | LAMBDA-046 | Analyst | Embodied |
| Story Lifecycle | Tier 7 | LAMBDA-046 | Analyst | Enacted |
| Quality Enforcement | Tier 11 | LAMBDA-129 | Inspector | Enacted |
| Pre-DONE Gate | Tier 14 | LAMBDA-151 | Analyst | Extended |
| Completion | Tier 15 | LAMBDA-170 | Inspector | Extended |

## PPT Compliance Gate

**MANDATORY:** Every sprint must create planning documents in `coda_project_planning/sprints/{NNN}/` **before** execution begins — even if the plan originated from Omega Engine plan mode, a backlog item, or ad-hoc user request.

**Required before execution:**

- `kickoff.md` ext
- `quality_gates.md` ext
- `sprint_{NNN}_plan.md` ext

**If sprint was planned outside the PPT workflow** (e.g., Omega Engine plan file, direct user instruction), create the PPT documents from the plan before executing stories.

**Source:** Sprint 307 — PPT workflow bypassed; documents created retroactively. Flagged as process violation in retrospective.

## Cleanup Sprint PPT Enforcement (MANDATORY)

**CRITICAL:** Cleanup sprints (N-0, N-0-0, N-0-0-0 patterns) require the **same full PPT ceremony** as primary sprints. There are no exceptions.

**Required workflow for cleanup sprints:**

``` ext
/sprint-planning {N-0}  →  /sprint-review {N-0}  →  /sprint-execution {N-0}  →  /sprint-retrospective {N-0}

``` ext

**Gate Logic:**

``` ext
IF sprint number matches pattern *-0 or *-0-0 or *-0-0-0:
  ENFORCE: Same pre-execution gate as primary sprints (Step 1)
  REQUIRE: kickoff.md, quality_gates.md, sprint_{N}_plan.md, review.md
  DO NOT skip any planning or review steps

IF cleanup sprint is attempted without planning docs:
  HARD BLOCK: "Cleanup sprint {N} requires full PPT ceremony. Run /sprint-planning {N} first."

``` ext

**Why:** Cleanup sprints address retrospective action items and technical debt. Skipping PPT for "trivial" cleanup sprints caused process violations (Sprint 307, Sprint 308-0) where documents were created retroactively rather than upfront.

**Cross-reference:** See `/sprint-planning` skill — "Cleanup Sprint Workflow (MANDATORY)" section.

**Source:** Sprint 308-0 Retrospective Action Item #2; Sprint 308-0-0 STORY-308-0-0-002

## Related Skills

| Skill | Relationship |
|-------|--------------|
| sprint-planning | Provides the plan this skill executes |
| sprint-review | Must pass before execution begins |
| sprint-devops-review | Next step: DevOps audit before retrospective |
| sprint-retrospective | Reviews execution outcomes after DevOps review |
| blackrod | Enforces quality during execution |
| run-tests | Validates code changes during execution |
| `techne-code-soviet-inspector` | MANDATORY: validates test assertions before story DONE |
| code-review | Reviews PRs created during execution |
| commit | Used for committing story implementations |

**Family:** sprint-workflow (see [family_registry.md](../_shared/family_registry.md))

## Constraints

See: [constraints.md](../_shared/constraints.md)

Required: APPROVAL_REQUIRED, QUALITY_GATES

Summary:

- Must have sprint-review approval before starting (APPROVAL_REQUIRED)
- All quality gates must pass before story completion (QUALITY_GATES)
- Blockers must be escalated immediately to blackrod

**Example session:** See [`example-session.md`](references/example-session.md).

## Integration Points

| Direction | Skill | Handoff |
|-----------|-------|---------|
| Inbound | sprint-review | Execution begins only after sprint-review sets status to APPROVED in review.md |
| Inbound | blackrod | Blackrod enforces quality gates during execution; escalations flow to Blackrod for blocker destruction |
| Outbound | run-tests | Tests are invoked per-story during execution (Steps 10-11) and at sprint completion (Step 12) |
| Outbound | sprint-retrospective | After execution and DevOps review complete, retrospective consumes completion.md and sprint metrics |
| Bidirectional | blackrod | Blackrod receives escalations during execution and can halt stories or the sprint |

## Next Workflow

After completion, run `/sprint-devops-review` to conduct the DevOps audit, then `/sprint-retrospective` for the retrospective.

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
