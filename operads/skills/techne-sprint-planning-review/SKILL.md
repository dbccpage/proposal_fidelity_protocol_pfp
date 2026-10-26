---
name: techne-sprint-planning-review
description: "Reviews sprint plans against engineering capacity, defect backlogs, and product roadmaps."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# techne-sprint-planning-review

## Prerequisites

## Usage

**Shared gates** (IAK-007, already-committed check, required documents, pre-execution gate, + Current-System Gates: contracts · governance-strict · test-tier · obstruction/clippy · worktree-isolation · devops-review): See [sprint_gates.md](../_shared/sprint_gates.md).
**Source:** Sprint 061 - explicit correction to always insert sprint review between planning and execution, and to follow this workflow consistently.
**AUTOMATIC TRIGGER (MANDATORY):**

## When to Activate

## description: Sprint plan review and approval. Use after /sprint-planning to get Product Owner and Blackrod approval before execution. Triggers on "/sprint-planning-review", "/sprint-review", "review sprint", "approve sprint"

## Workflow Overview

| Step | Duration | Agent | Deliverable |
| ------ | ---------- | ------- | ------------- |
| 1 | 10 min | product_owner | Requirements validation |
| 2 | 15 min | blackrod | Quality gate review |
| 3 | 10 min | scrum_master | Final approval |

**Review instructions:** See [`instructions.md`](references/instructions.md).

## Post-Approval Tracking (MANDATORY)

After sprint review approval, the sprint enters "APPROVED_PENDING_EXECUTION" state.

**Handoff checklist:**

1. Document approval in review.md with status: APPROVED
2. Check for orphaned sprints before user proceeds (see below)
3. Inform user: "Sprint {N} approved. Run `/sprint-execution {N}` to begin."

**Orphan Sprint Check:**
Before approving a new sprint, check for approved-but-not-executed sprints:

```bash

# Check for sprints with review.md (APPROVED) but no completion.md
for dir in coda_project_planning/sprints/*/; do
  if [[ -f "$dir/review.md" ]] && [[ ! -f "$dir/completion.md" ]]; then
    grep -l "Status.*APPROVED" "$dir/review.md" 2>/dev/null && echo "ORPHAN: $dir"
  fi
done

``` ext

If orphans found, **mention briefly in review findings** but do NOT
escalate to blocking options or repeated next-step suggestions.
Report orphans once in the review document, then move on.

``` ext
NOTE: [N] orphaned sprints detected ([list]). Tracked for future disposition.

``` ext

Do NOT offer "disposition orphaned sprints" as a next-step option unless
the user specifically asks about orphans.

**Source:** Sprint 055-0 discovered as orphan during Sprint 056 retrospective.
Updated Sprint 113-0 session -- user directive "Ignore orphans"

## Review Criteria

### Stories Must Have

| Criterion | Required |
|-----------|----------|
| User story format | Yes |
| Acceptance criteria | Yes |
| Test requirements | Yes |
| Point estimate | Yes |
| Technical notes | Recommended |

### Quality Gates Must Define

| Gate | Required |
|------|----------|
| Lint check | Yes |
| Type check | Yes |
| Unit tests | Yes |
| Coverage threshold | Yes |
| Security scan | Yes (for backend changes) |

## UROS Tier Mapping

| Sprint Phase | UROS Tier | CODEX Lambda | Sovereign Role | 4E Mode |
|-------------|-----------|-------------|---------------|---------|
| Sprint Review | Tier 11 | LAMBDA-129 | Inspector | Enacted |
| Product Owner Review | Tier 11 | LAMBDA-129 | Inspector | Embedded |
| Blackrod Quality Review | Tier 14 | LAMBDA-151 | Analyst | Extended |
| Techne Code Soviet Inspector | Tier 10 | LAMBDA-100 | Inspector | Enacted |
| Scrum Master Approval | Tier 7 | LAMBDA-046 | Analyst | Embodied |

### Mandatory Defect Investigation Logging (`RULE_DEFECT_INVESTIGATION_LOGGING_001`)

Whenever this skill encounters any error, build failure, veto, linter defect, anti-pattern breach, proof/contract obstruction, or process violation:
1. Automatically create a formal investigation report under:
   `omega_engine/anomalon_councils/councils/blackrod/investigations/investigation_{YYYYMMDD}_{skill_name}_{defect_id}.md`
2. Include full error trace/context, root cause analysis, affected files, and recommended workflow remediation plan for Blackrod review.

## Related Skills

| Skill | Relationship |
|-------|-------------|
| sprint-planning | Precedes: provides plan to review |
| sprint-execution | Follows: executes after approval |
| sprint-retrospective | Follows execution: reviews outcomes |
| blackrod | Co-reviewer: enforces quality gates |
| `techne-code-soviet-inspector` | MANDATORY: validates test assertions before approval |

**Family:** sprint-workflow (see [family_registry.md](../_shared/family_registry.md))

## Witness Artifact and Review Constraint (MANDATORY)

**Witness Artifact** = one of: Log file, Screenshot hash file, or Test report — stored under `omega_engine/omega_engine_operations/evidence/` and referenced by **file path**.

**Demo step — no text-only credit:**

- Reject demo output that is **only** text (e.g. "It works"). Such output is not verifiable and is treated as assertion, not evidence.
- For each completed ticket or demo outcome, require at least one **Witness Artifact path** under `omega_engine/omega_engine_operations/evidence/`, or an explicit approved exception (e.g. "Planning-only sprint; no demo artifacts" with Product Owner/Blackrod note).

**Review Constraint:** A story **cannot be CLOSED** (marked DONE for review/credit) unless a Witness Artifact exists at a stated path in `omega_engine/omega_engine_operations/evidence/`. **No path = No credit.**

In `review.md`, every completed ticket must list an **Evidence path** (file path under `omega_engine/omega_engine_operations/evidence/`). Missing path → story not counted as completed.

## Constraints

See: [constraints.md](../_shared/constraints.md)

Required: APPROVAL_REQUIRED, EVIDENCE_BASED, EVIDENCE_PATH_REQUIRED

Summary:

- Sprint cannot proceed without explicit approval (APPROVAL_REQUIRED)
- Review decisions must cite specific evidence from artifacts (EVIDENCE_BASED)
- Every completed ticket in review must have a file path under `omega_engine/omega_engine_operations/evidence/` (EVIDENCE_PATH_REQUIRED). No path = No credit.

## Integration Points

| Direction | Skill | Handoff |
|-----------|-------|---------|
| Inbound | sprint-planning | Review consumes plan, kickoff, and quality_gates artifacts produced by planning |
| Outbound | sprint-execution | After approval, execution begins using the reviewed and approved plan |
| Bidirectional | blackrod | Blackrod co-reviews quality gates (Step 8) and can block approval; review findings may trigger Blackrod escalations |
| Inbound | `techne-code-soviet-inspector` | Techne Code Soviet Inspector audit (Step 7) must pass before Blackrod quality review proceeds |
| Outbound | sprint-planning | If changes requested, review sends feedback back to planning for revision |

**Example session:** See [`example-session.md`](references/example-session.md).

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
