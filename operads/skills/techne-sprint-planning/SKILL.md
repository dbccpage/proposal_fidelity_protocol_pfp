---
name: techne-sprint-planning
description: "Guides sprint backlog grooming, capacity planning, ticket dependencies, and definition of done alignment."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# techne-sprint-planning

**Required documents and pre-execution gate:** See [sprint_gates.md](../_shared/sprint_gates.md).
**Source:** Sprint 060 Retrospective - goal/scope mismatch lesson

## Verification Checklist

**Good alignment:**
**Bad alignment:**

## Example

## Rule

**CRITICAL:** The sprint goal MUST be achievable by completing all planned stories.

## Sprint Goal/Scope Alignment (MANDATORY)

**Source:** Sprint 114 incident -- Sprint 115 was planned/reviewed but never executed; work was done on a shared branch with Sprint 114. Sprint 118 retrospective -- code committed under wrong sprint label due to shared branch accumulation.
**Detection:** The Orphaned Sprint Audit (pre-flight checklist) catches phantom sprints by looking for sprints with `review.md` but no `retrospective.md`.
**Anti-pattern (Sprint 118):** The `sprint-113` branch accumulated work from sprints 116, 117, and 118, causing commit attribution confusion (Sprint 118 code committed under `feat(sprint-116):` label) and phantom sprint detection failures.
**Prevention:**
**Consequences:**

## Phantom Sprint Anti-Pattern

**Source:** Sprint 105-0 - established pattern for consolidating tech debt from Sprints 104 and 105
**Cleanup sprint triggers:**

## Cleanup Sprint Nomenclature

## Sprint Capacity Rules

## Workflow Overview

**Shared gates** (cleanup sprint, IAK-007, already-committed check, required documents, + Current-System Gates: contracts · governance-strict · test-tier · obstruction/clippy · worktree-isolation · devops-review): See [sprint_gates.md](../_shared/sprint_gates.md). All gates in that file apply to this skill.

## When to Activate

## description: Kickoff the sprint_planning workflow with Blackrod as orchestrator. Use when starting a new sprint, planning sprint scope, or when ooutwire says "start sprint X". Triggers on "/sprint-planning", "start sprint", "plan sprint"

**Reference material** (moved out of this file to keep it under the 300-line ceiling):

- Pre-flight checklist — [`preflight-checklist.md`](references/preflight-checklist.md)
- Planning instructions — [`instructions.md`](references/instructions.md)
- Async work tracking protocol — [`async-work-tracking.md`](references/async-work-tracking.md)
- Sprint pivot process — [`sprint-pivot-process.md`](references/sprint-pivot-process.md)

## Story Point Scale

| Points | Description | Duration |
|--------|-------------|----------|
| 1 | Trivial | < 1 hour |
| 2 | Small | 1-4 hours |
| 3 | Medium | 1 day |
| 5 | Large | 2-3 days |
| 8 | Very large | ~1 week |
| 13 | Epic | Split it |

**Estimation note:** Test count estimates in story verification sections should use "minimum N" rather than exact counts. Delivery routinely exceeds planned test counts as edge cases are discovered during implementation.

## Performance Considerations

When planning stories that involve auto-telemetry or automatic instrumentation:

- **Database traffic impact**: Evaluate if automatic tracking creates excessive writes
  - As a planning heuristic, avoid features that are expected to add more than ~50 additional writes per minute per active user. This is an illustrative default only and should be recalibrated based on the actual write capacity, SLOs, and headroom of the target database.
  - Also avoid designs that would increase overall database write volume by more than ~10% during current peak traffic periods without a capacity plan. Treat this as a starting threshold and adjust it in collaboration with the owning infrastructure/DBA team using current capacity planning and observability data.
- **invoke_skill with auto-BLOB**: Defer if it would trigger writes on every skill invocation
  - Prefer sampling (e.g., record 1 in N calls) or summarised metrics instead of storing a full BLOB on every invocation.
- **Batch vs real-time**: Prefer batched approaches for high-frequency operations
  - As a rule of thumb, target batches of at most ~1,000 additional writes and space them at least 5 minutes apart for non-critical telemetry. This batching guidance is a generic heuristic and should be tuned to the system's throughput limits and latency requirements.

If ooutwire rejects a story for "too much traffic", mark it as deferred and:

- Document the estimated additional writes per minute and batching strategy in the story's **Technical Notes**.
- Capture the specific performance concern and any proposed mitigations in the sprint retrospective.

## Test Checklist

**MANDATORY:** Every story that adds or modifies code MUST include test requirements.

### Story Test Requirements

| Story Type | Required Tests |
|------------|----------------|
| New React component | At least 1 render test in `.test.tsx` |
| Component modification | Update existing tests, no regression |
| New API endpoint | pytest for happy path + error cases |
| Backend modification | Update existing tests, no regression |
| New utility/service | Unit tests for public methods |

### Pre-Merge Test Checklist

Before marking any story as DONE, verify:

- [ ] New code has corresponding test file
- [ ] All tests pass locally (`npm run test:react:run`, `pytest tests/`)
- [ ] Coverage not regressed (`pytest --cov=backend`)
- [ ] No components without tests

### Test File Naming Convention

| Code File | Test File |
|-----------|-----------|
| `MyComponent.tsx` | `MyComponent.test.tsx` |
| `my_service.py` | `test_my_service.py` |
| `utils.ts` | `utils.test.ts` |

## Expansive Story Format (MANDATORY)

Every story in `sprint_0NN_plan.md` MUST follow this expanded format to ensure machine-readable contracts.

```markdown

## [STORY-{SPRINT}-{NUM}] Title

**As a** <user type>
**I want** <goal>
**So that** <benefit>

### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

### Test Requirements
- [ ] Test type: (unit/integration/e2e)
- [ ] Test file: path/to/test_file
- [ ] Coverage target: X%
- [ ] **Assertion quality criteria:**
  - [ ] Exact counts tested (no `>= 1` when specific count known)
  - [ ] All claimed behaviors have corresponding assertions
  - [ ] Downgrade tested (if migration story)
  - [ ] No tautological assertions (`assert True`, etc.)

### Technical Notes
- Implementation approach
- Dependencies

### Estimate
- Points: X
- Complexity: Low/Medium/High

``` ext

**Test count phrasing:** When specifying test counts in the Test Requirements or Verification sections, use "minimum N tests" rather than exact counts. Implementation often discovers additional edge cases that warrant more tests than originally estimated.

**Source:** Sprint 114 -- planned 29 tests, delivered 47; exact counts create false expectations

## Graphiti Integration Notes (Sprint 047 Learnings)

When working with graphiti-core v0.26+:

- Use `build_indices_and_constraints()` not `build_indices()` ext
- Use `EpisodeType.text` enum, not string for `source` parameter
- cross_encoder defaults to OpenAI; use NoOpCrossEncoder class to bypass
- Anthropic+VoyageAI is viable alternative to OpenAI (VoyageAI key starts with `pa-`)
- VoyageAI free tier has 3 RPM limit; add payment method for production use

**Source**: Sprint 047 E2E validation (STORY-047-001)

## UROS Tier Mapping

| Sprint Phase | UROS Tier | CODEX Lambda | Sovereign Role | 4E Mode |
|-------------|-----------|-------------|---------------|---------|
| Sprint Planning | Tier 15 | LAMBDA-161 | Analyst | Embedded |
| Story Definition | Tier 11 | LAMBDA-129 | Inspector | Enacted |
| Quality Gates | Tier 14 | LAMBDA-151 | Analyst | Extended |
| Code Audit | Tier 7 | LAMBDA-046 | Analyst | Embodied |

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `sprint-planning-review` | Next step: validates this plan before execution |
| `sprint-execution` | Consumes this plan to guide development |
| `sprint-retrospective` | Reviews outcomes of plans created here |
| `blackrod` | Enforces quality gates defined in this plan |
| `techne-code-soviet-inspector` | Design-time test quality criteria |
| `commit` | Used for committing planning documents |

**Family:** sprint-workflow (see [family_registry.md](../_shared/family_registry.md))

## Constraints

See: [constraints.md](../_shared/constraints.md)

Required: APPROVAL_REQUIRED, EVIDENCE_BASED

Summary:

- All plans require approval before execution (APPROVAL_REQUIRED)
- Story estimates must be justified with evidence (EVIDENCE_BASED)
- Quality gates must be measurable and enforceable

**Example session:** See [`example-session.md`](references/example-session.md).

## Next Workflow

After `/sprint-planning` completes, run `/sprint-planning-review` to initiate the sprint_planning_review workflow.

## Integration Points

| Direction | Skill | Handoff |
|-----------|-------|---------|
| Inbound | sprint-retrospective | Action items from retro feed into planning as cleanup sprint (N-0) stories |
| Inbound | architecture-governance | Architecture decisions constraint planning |
| Outbound | `sprint-planning-review` | Produced plan is input for review |
| Outbound | sprint-execution | Plan guides execution |
| Outbound | blackrod | Quality gates defined in plan are enforced by Blackrod |
| Bidirectional | `techne-code-soviet-inspector` | Test requirements defined here, enforced by inspector later |

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
