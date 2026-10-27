# EPIC-OE-OEGOV-004: Blackrod warrants and observed enforcement

**Epic ID:** `EPIC-OE-OEGOV-004`

**Status:** `SPEC_ONLY`

**AuthorityEffect:** None

**Source baseline:** `6c44a0ddd330d827d989eaefad4215d03a88ed9a`

**Owner:** Governance maintains decision and warrant contracts; OEOS maintains execution, cancellation and containment adapters; Adversary consumes observed results.
**Date:** 2026-10-10

Blackrod must turn an evidenced finding into a bounded defensive action whose effect is independently observed. A council resolution, persona statement, action enum or recorded request cannot establish that a task stopped, an artifact was quarantined, or a capability was revoked. The first delivery is an authenticated, scope-bound halt of one owned task, followed by a retained incident record and an explicit human-controlled recovery route.

## Existing behavior and residual gaps

| Inspected production surface | Reuse | Residual this epic owns |
| --- | --- | --- |
| [Rust Blackrod](../../../../engine/crates_rs/core_contracts/src/enforcement/governance/blackrod.rs), `EnforcementAction`, `map_enforcement`, `enforce`, `emergency_halt` | Closed defensive action vocabulary; refuses voting, evidence waiver, self-certification and fake-test acceptance. | `enforce` appends to an in-memory vector; constant trace IDs and `TODO:timestamp` remain. `emergency_halt` returns a value without executing or logging a halt. Bind real incident identity, provenance, execution and readback. |
| [BlackrodActiveInterceptor](../../../../governance/domain/council_deliberation/services/blackrod_active_interceptor.py) | Existing quorum-count, claim-text and previous-veto checks. | `BlackrodAuditResult.prime_rules_checked` names ten rules by default although only three checks execute. Emit per-rule evidence and `NOT_CHECKED` for unexecuted predicates. A hedge anywhere in the decree currently bypasses the whole text check; that heuristic cannot certify proposal/evidence integrity. |
| [CouncilDeliberationWorkflow](../../../../governance/use_cases/council_deliberation/workflows/council_deliberation_workflow.py), `ratify_decree`/`veto_session` | Existing transition and SQLite persistence seam. | OEGOV003 supplies authenticated session/actor/roster evidence and computed voting outcomes. This epic consumes that evidence and supplies orthogonal veto/enforcement; it does not create another meeting engine. |
| [ThanatosBoutUseCase](../../../../adversary/use_cases/thanatos_bout_use_case.py), `execute_bout` | Existing narrative renderer and persisted bout artifacts. | Scripted carrier fields assert dispatched children, PASS security findings and zeroed traces without executing those effects. Current outer status is `BOUNDED_RESIDUAL`/`HOLD`, not authorization. Preserve that ceiling; label simulation and render operational fields only from actual adapter observations. |
| [OEOS TaskService](../../../../operating_system/application/task_service.py), `cancel`/`_run_claimed`; [checkout lease](../../../../operating_system/infrastructure/checkout_lease.py) | Existing task lifecycle, cooperative cancellation, exact checkout identity and lease checks. | Wire Blackrod's scoped action to these public services. Cancellation requested is distinct from executor stopped; unobserved or failed containment remains `UNKNOWN`/refused. |

The [Blackrod skill](../../../../.agents/skills/blackrod/SKILL.md) and [emergency engagement specification](../../../../.agents/skills/blackrod/references/emergency_engagement_rules.md) supply design requirements, not authentication or executable permission. Their theatrical terminology means software containment within owned scopes. This plan authorizes no destructive cleanup, external retaliation, or autonomous global teardown.

## Delivery contract and dependency DAG

The [council runtime epic](epic_oe_oegov_003_council_runtime_and_institutional_memory_plan.md) owns OEGOV003 meeting runtime and institutional memory. Its proposal-only decision record can ship before this epic; operational enforcement depends on both. Dependencies are:

```text
OEGOV003 actor/roster/session evidence ----+
OEGOV PRIOR-ART-001 trust configuration --+--> OEGOV004 warrant check
OEOS task identity/lease/cancellation ----+        |
                                                 v
                                      bounded action + independent readback
                                                 |
                                    incident record --> OEGOV005 feedback
                                                 |
                                    suite qualification in README
```

[Source-to-policy admission](epic_oe_oegov_001_source_to_policy_admission_plan.md) owns admitted checker/principal trust and revocation. [Panel dissent](epic_oe_oegov_002_panel_dissent_and_gate_routes_plan.md) owns preserved objections. [OEEIS admission](../oeeis/epic_oe_eis_003_clonal_affinity_regulatory_anergy_and_human_admission_plan.md) owns immune admission; incident findings enter as candidates only. [OEOS custody](../oeos/epic_oe_oeos_001_immutable_diagnostic_custody_plan.md) owns durable storage/recovery. None of these producers' PASS values substitutes for this consumer's action check.

The proposed warrant is a canonical input record at the governance application boundary: incident ID, request ID/idempotency key, authenticated issuer reference, allowed action, exact task/artifact/repository scope, source/head and evidence digests, policy revision, expiry, revocation version, limits and the human delegation reference. Names/schema version are to be frozen with the existing contract owner before implementation. Bare actor names, YAML roles, copied signatures and the literal `ZD-30` are not credentials.

The result separates `PROPOSED`, `REFUSED`, `REQUESTED`, `OBSERVED_APPLIED`, `OBSERVED_FAILED` and `UNKNOWN` action disposition from council decision and Adversary terminal status. It binds the warrant, before/after observations, actual target, command/executor identity, time, readback evidence and residuals. Only readback from the owning store/process can establish `OBSERVED_APPLIED`; a requested cancellation cannot. An execution failure never erases the incident or enables automatic replay.

Four-lock special operations remain an explicit optional branch: Logos, Nous, Curious and Blackrod attestations bind the same incident, scope, policy and evidence in order. Missing, stale, substituted or out-of-order attestations refuse that branch. Nous records an evidence-limited assessment and uncertainty; software must not claim to prove subjective malice. A predelegated defensive pause and a direct human stop have separate narrow authority paths, so urgent stopping cannot be blocked by an unavailable council. Recovery/release requires the authorized human path and a fresh observation; a council cannot expand Blackrod's scope or reverse that human stop. The exceptional Curious unanimity/secretary mechanism, if enabled, requires its own typed policy and complete roster-bound attestation, never ordinary secretary voting.

## Obstruction review and TDD test plan

For each acceptance slice, first record the independent oracle and demonstrate RED on the named negative control. Implement the smallest production change to reach GREEN, then refactor while rerunning that same public-boundary case and its failure witness. Run the decisive mutation against the owning production method and require RED again; restore the code and record recovery. These are proposed implementation steps, not executions performed by this planning review.

**Execution status:** `PROPOSED_NOT_EXECUTED`. These are future behavior tests and mutations, not test receipts. First run the existing [Blackrod workflow tests](../../../../governance/tests/integration/test_council_deliberation_blackrod_workflow.py) as scoped characterization. Their successful secretary vote is not a valid oracle for OEGOV003's future roster semantics.

| Order and Examiner class | RED witness and minimal GREEN | Independent oracle and decisive mutation |
| --- | --- | --- |
| 1 / Class 1: finite positive | Halt one owned queued OEOS task under an admitted scoped delegation; read its actual terminal state and incident binding. An already-valid characterization control is not invented RED. | Open the real temporary SQLite store separately and compare task/incident/digest values; another task remains unchanged. Mutation: bypass `TaskService.cancel`'s queued-task transition in `task_service.py`; the public halt/readback test must fail. |
| 2 / Class 2: malformed or incomplete authority | Reject absent principal/delegation, empty scope, malformed digest, expired/revoked warrant, unknown action and boolean-as-integer limits before any execution. Add only the missing validator at the owned boundary. | Read unchanged store and zero action dispatch count. The future warrant-verifier rejection branch is a proposed target, not an existing implementation. Record its exact function/line after the minimum implementation, then bypass it and require RED. |
| 3 / Class 3: transplant and replay | Transplant a valid warrant to a different task/head/artifact; refuse. Repeating an identical request observes its previous result without repeating the effect; changed bytes under the same key refuse. | Independently hash inputs and inspect two task histories. Remove the future scope/idempotency binding and require RED, including a readback from the wrong target. |
| 4 / Class 4: concrete counterexamples | Keep an active task ignoring cooperative cancellation; report `REQUESTED`/`UNKNOWN` until a real stop is observed. Replace evidence with a narrative PASS, inject a disconnected containment adapter, remove a four-lock attestation, or append a hedge to an unsupported decree; none becomes observed clearance. | Actual executor handle/store observation and literal required-rule table. Mutation: suppress the current prior-veto guard in `BlackrodActiveInterceptor.audit_session_for_ratification`; terminal-veto controls must fail. Add an unexecuted rule to `prime_rules_checked`; the new audit-custody control must fail. |
| 5 / Class 5: production mutation and recovery | Human stop during execution wins over a later favorable council vote; no new action starts after revocation/stop. Crash between request and readback preserves unknown status and reconciles without duplicate effects. Recovery uses a fresh authorized request. | Real local child process with bounded timeout, actual store reopen and independent effect log; no paid model. Mutation: bypass `_run_claimed`'s post-execution `cancellation_requested` guard, or its `lease.assert_held` check, and require the matching public-boundary control to fail; restore and recover GREEN. |

The first running-task exercise uses a harmless isolated child process. Quarantine, license revocation, done-credit removal and rollback follow as separate action adapters with their own target-store readback, preimage/version check and bounded recovery tests. Rollback cannot overwrite a newer/foreign state. None may inherit completion from the halt test. No action is enabled in deployment until its own positive, malformed, transplant, counterexample and mutation controls pass.

**Theoretical Minimum:** INVARIANT: exact authorized scope and observed effect remain bound to independent evidence. BREAK: swap a target, erase veto/stop, bypass a lease, or turn a requested effect into an observed one. WITNESS: the public workflow refuses or retains unknown status, preserves original evidence and leaves the unrelated task intact. MUTATION: execute one named production change above in an isolated test worktree, record failing test/output, restore exact source bytes and rerun GREEN; new verifier branches remain prospective until authored.

Candidate test files below are **proposed**, except the first existing characterization file. Execute individual tests with `-k` while implementing, then that file only; no whole-estate sweep. Use a writable external `--basetemp` on Windows if required.

```powershell
py -3.12 -m pytest governance/tests/integration/test_council_deliberation_blackrod_workflow.py -q
py -3.12 -m pytest governance/tests/integration/test_blackrod_warrant_execution.py -q
py -3.12 -m pytest governance/tests/integration/test_blackrod_stop_recovery.py -q
cargo test --manifest-path engine/crates_rs/Cargo.toml -p core_contracts -j 1 blackrod
```

Rust enum tests characterize type behavior only; they cannot establish OS containment. DOC_MGR pins source/contract bytes, UTF-8/LF and links; DEV_MGR with Bare Metal Anchor/Techne and Scope Guard binds the existing execution seam and narrow scope; QA_MGR with Defect Hunter/Inspector owns independent effects and vetoes mock-only safety; BUILDER checks INVARIANT/BREAK/WITNESS/MUTATION. The four stages are intake, implementation, adversarial QA, receipt review with Punchlist/Adversary. Run one to three files/crates per batch, use `cargo -j 1`, and stop after at most three repair attempts with retained dissent and obstruction. Record real `SoftwareQaReceiptV1` only through its bound schema/writer, including base/head, runtime versions, commands, exit statuses, mutation diff and recovery bytes outside this epic folder.

## Remaining decisions and completion evidence

Before implementation, owners must bind the admitted human/principal authentication source, canonical warrant schema, clock/expiry policy, adapter-specific capability revocation, running-process isolation support on the target host, and the authority for release after halt. Missing authentication or containment support is a deployment blocker, not permission to use a string flag or simulated adapter. Local deterministic tests remain available while those deployments are held.

Completion requires each enabled action's real readback and adversarial receipts, the human-stop integration exercise, per-rule audit honesty, persisted reconciliation, and Adversary rendering of those same observed bytes. Offline fixture success alone cannot bring Blackrod online; qualification must name which host, policy, adapters and actions actually ran.

## Claim envelope

- **Supports:** source-inspected specification for bounded Blackrod enforcement, reuse boundaries, independent effect oracles and implementation falsifiers.
- **Does not support:** executed mutation/tests, authenticated runtime deployment, universal containment, proof of hostile intent, or any authority grant.
- **Narrowest claim:** current Blackrod values and workflow checks can anchor the proposed integration, but operational warrants and effect verification still require implementation and receipts.
- **Next evidence:** implement the first scoped halt through the existing OEOS task service and record real RED/minimal GREEN/mutation/restoration results before expanding the enabled action set.
