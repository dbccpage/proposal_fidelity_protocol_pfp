---
name: techne-sprint-retrospective
description: "Executes sprint retrospective analysis, root cause audits of blockers, and continuous process improvements."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# techne-sprint-retrospective

**Required documents:** See [sprint_gates.md](../_shared/sprint_gates.md#required-sprint-documents). This skill creates `completion.md` and `retrospective.md`.
**Source:** PPT failures in Sprints 062, 063 (2026-01-30)
**NO EXCEPTIONS:** A retrospective for a sprint that skipped planning is meaningless - we can't learn from a process we didn't follow.

## Error Messages

## Gate Logic

## Gate Check

## Pre-Retrospective & Pre-Archive Gate (MANDATORY HARD BLOCK)

**HARD BLOCK assertion:** Before running retrospective or archiving any sprint folder:

1. Verify `1_sprint_impl_documents/` exists.
2. Verify `1_sprint_impl_documents/sprint_{NNN}_completion.md` exists.
3. Verify `1_sprint_impl_documents/sprint_{NNN}_devops_review.md` exists.
4. Verify `1_sprint_impl_documents/sprint_{NNN}_retrospective.md` exists.
5. Verify `1_sprint_impl_documents/sprint_{NNN}_vp_briefing.md` exists.

If ANY document or the `1_sprint_impl_documents/` directory is missing, HARD BLOCK immediately. Do NOT archive the sprint.

**Source:** Sprint 153-0 auto-improve-autoskill analysis (web edit capture rate 0% across Sprints 080, 112, 138, 153)

## Web Edit Scan (Pre-Gate Advisory)

**Source:** Sprint 113-0 session -- retro blocked for missing completion.md

## Pre-Gate: Check Git for Executed Sprint

## Prerequisites

**Shared gates** (IAK-007, already-committed check, required documents, cleanup sprint; Current-System Gates — contracts · governance-strict · test-tier · obstruction/clippy · worktree-isolation — are enforced upstream, and this retro consumes the `/sprint-devops-review` findings): See [sprint_gates.md](../_shared/sprint_gates.md).

**Source:** WE NEED TO REVIEW THESE SPRINTS THE SAME WAY EVERY TIME!

**CRITICAL:** After `/sprint-devops-review` completes, invoke `/sprint-retrospective` automatically WITHOUT asking user. The full workflow is:

## Automatic Workflow Trigger (MANDATORY)

## When to Activate

## description: Kickoff the sprint_retrospective workflow. All SADC architects present (1 min each), lessons learned captured. Use after /sprint-execution completes. Triggers on "/sprint-retrospective", "retro", "retrospective"

## Workflow Overview

| Step | Duration | Participants | Purpose |
| ------ | ---------- | -------------- | --------- |
| 1 | 5 min | scrum_master | Open retro, present metrics |
| 2 | 15 min | all architects | 1 min each: what went well/poorly |
| 3 | 10 min | blackrod | Quality assessment |
| 4 | 15 min | all | Action items |
| 5 | 5 min | scrum_master | Close and document |

**Retrospective instructions:** See [`instructions.md`](references/instructions.md).

## Retrospective Format

### Mad/Sad/Glad (Alternative)

- **Mad:** Frustrations
- **Sad:** Disappointments
- **Glad:** Successes

### 4Ls (Alternative)

- **Liked:** What worked
- **Learned:** New knowledge
- **Lacked:** Missing resources
- **Longed for:** Desired improvements

## Continuous Improvement

Action items from retro feed into:

1. Next sprint planning
2. Process improvements
3. Tooling updates
4. Team development

## Meta-Learning (Steps 11–13 are BLOCKING — see above)

Steps 11 (/autoskill), and 13 (record hashes) are the **Autoskill Latch**. The retrospective artifact is INVALID without Autoskill Hash.

Optional: Include in the Meta-Learning section additional metrics from the runs (e.g. Autoskill coverage %, proposals count). The **required** content is the two hashes.

### Step 16: Run /system-review (after Autoskill Latch)

As part of closing the sprint cycle, run a comprehensive system health check before declaring it complete:

``` ext
/system-review

``` ext

This assesses:

- Code quality (ruff, mypy)
- Architecture adherence (Clean Architecture, DDD patterns)
- CI/CD health (workflow status, blocking jobs)
- SQL/migrations (indexes, reversibility)
- Test coverage (count, coverage %)
- Security (Bandit, dependency audit)
- Skills/agents inventory

Include findings in `coda_project_planning/sprints/{N}/system_review.md`.

**Why mandatory:** Technical debt accumulates invisibly. Regular system reviews expose degradation before it becomes critical.

### Step 17: Run /auto-symmetry-hunter --families-only (recommended)

Periodically verify skill family compliance:

``` ext
/auto-symmetry-hunter --families-only

``` ext

This checks that all members of each family (sprint-workflow, code-quality, database, meta, testing, etc.) have required sections (Constraints, Related Skills) and flags non-compliant skills. Include the Family Compliance Report in the retrospective or in `coda_project_planning/sprints/{N}/symmetry_hunter_report.md`.

**Why recommended:** Keeps skill structure consistent and supports autoskill propagation; run at least every few sprints or when many skills change.

## UROS Tier Mapping

| Sprint Phase | UROS Tier | CODEX Lambda | Sovereign Role | 4E Mode |
|-------------|-----------|-------------|---------------|---------|
| Sprint Retrospective | Tier 15 | LAMBDA-170 | Inspector | Extended |
| Techne Code Inspector Report | Tier 10 | LAMBDA-100 | Inspector | Enacted |
| Blackrod Assessment | Tier 14 | LAMBDA-151 | Analyst | Enacted |
| Signal Extraction | Tier 7 | LAMBDA-046 | Analyst | Embodied |
| Web Edit Detection | Tier 11 | LAMBDA-129 | Inspector | Embedded |
| Crystallization Sweep | Tier 15 | LAMBDA-170 | Inspector | Extended |
| Autoskill Latch | Tier 15 | LAMBDA-171 | Inspector | Extended |

### Mandatory Defect Investigation Logging (`RULE_DEFECT_INVESTIGATION_LOGGING_001`)

Whenever this skill encounters any error, build failure, veto, linter defect, anti-pattern breach, proof/contract obstruction, or process violation:
1. Automatically create a formal investigation report under:
   `engine/sentinel_councils/councils/blackrod/investigations/investigation_{YYYYMMDD}_{skill_name}_{defect_id}.md`
2. Include full error trace/context, root cause analysis, affected files, and recommended workflow remediation plan for Blackrod review.

## Related Skills

| Skill | Relationship |
|-------|--------------|
| sprint-planning | Next step: feeds lessons into next plan |
| sprint-execution | Provides outcomes to review |
| sprint-devops-review | Precedes: DevOps audit feeds findings into retrospective |
| sprint-review | Initial approval before execution |
| `techne-code-inspector` | Review test quality metrics for the sprint |
| autoskill | MUST run during retrospective (Step 11). Blocking. Run before /auto-improve-autoskill. |
| auto-symmetry-hunter | Can audit family compliance during retrospective |
| blackrod | Reviews enforcement effectiveness |

**Family:** sprint-workflow (see [family_registry.md](../_shared/family_registry.md))

## Constraints

See: [constraints.md](../_shared/constraints.md)

Required: EVIDENCE_BASED, SELF_REFERENCE

Summary:

- No evidence path = no credit. (EVIDENCE INVARIANT)
- All findings must cite specific sprint evidence (EVIDENCE_BASED)
- Check if retrospective process itself needs improvement (SELF_REFERENCE)
- Lessons learned must be actionable and assigned owners

**Example session:** See [`example-session.md`](references/example-session.md).

## Integration Points

| Direction | Skill | Handoff |
|-----------|-------|---------|
| Inbound | sprint-execution | Retrospective consumes completion.md and sprint metrics produced by execution |
| Inbound | sprint-devops-review | DevOps review findings feed into retrospective analysis |
| Outbound | autoskill | Step 11 invokes /autoskill to extract skill improvements from sprint learnings (BLOCKING) |
| Outbound | auto-improve-autoskill | Step 12 invokes /auto-improve-autoskill after autoskill completes (BLOCKING) |
| Outbound | sprint-planning | Action items feed into the next sprint's planning as cleanup sprint (N-0) stories |
| Bidirectional | blackrod | Blackrod presents quality enforcement summary; retrospective findings may trigger Blackrod escalations |

## Sprint Cycle Complete

After retrospective, the sprint cycle is complete:

``` ext
/sprint-planning → /sprint-review → /sprint-execution → /sprint-retrospective
       ↑                                                                  |
       └──────────────────────────────────────────────────────────────────┘

``` ext

To start the next sprint: `/sprint-planning {N+1}` ext

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
