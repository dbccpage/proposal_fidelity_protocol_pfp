# Epic: Paired replay campaign for gate diagnostics

**Epic ID:** `EPIC-OE-OEOPS-PRIOR-ART-001`
**AuthorityEffect:** None
**Status:** `RESEARCH_HOLD`
**Design readiness:** bounded experiment specified; production contract and source assumptions remain open.
**System:** [omega_engine_operations](../../../../omega_engine_operations)
**Registry relationship:** `INTEGRATION_HYPOTHESIS`; 0 file rows directly assigned to this system.
**Owner:** maintainers of `omega_engine_operations`; specialist roles below.
**Date:** 2026-10-10

## Problem and source-derived experiment

A collection of passing examples cannot measure the effect of a gate or decoding intervention.

Specify paired frozen candidate sets with gate/ungated arms, identical budgets and explicit malformed-input and false-positive counts.

This is a proposed transfer from the linked source material. A relevance score of 5 is discovery metadata. Source titles, abstracts and transcription summaries are not adopted theorem statements or implementation receipts.

## Prior art and existing plan boundary

- [07_learning_to_give_checkable_answers_with_prover-ver.md](../../../research_papers/library/03_multi_agent_debate/07_learning_to_give_checkable_answers_with_prover-ver.md) — `integration_hypothesis`; SHA-256 `57a9522f54e1eac6de325c972af9ab3e248f69d0a36cd4263dc0418e2d045af8`.
- [02_grammar_aligned_decoding.md](../../../research_papers/library/01_generation_control/02_grammar_aligned_decoding.md) — `integration_hypothesis`; SHA-256 `5e89e7bf7549599333dfb65d6b8a5cbbbd2722d3f16fd1ab759a521883c553ca`.

Use the [estate epic index](../README.md) to resolve adjacent owners and the [design-review reconciliation](../../../receipts/epic_design_review_20261010.md) for current OEWAS/Woland limits. This epic adds the experiment above; existing suite plans continue to own their broader architecture, migrations and release work.

## Contract to settle before implementation

- Input: frozen source revision and byte digest, finite task instance, explicit assumptions, observation basis, checker identity and budget.
- Output: typed result with candidate and evidence digests, separate diagnostic and authorization status, residual obligations and next action.
- Refusal: malformed input, missing oracle, mismatched source/candidate bytes, or undeclared authority produces an explicit refusal or open residual.
- Recovery: retain the failed candidate and dissent; re-evaluate changed bytes under the same run budget. Never reinterpret an earlier receipt as checking new bytes.
- Open design decisions: choose the existing owning production port, freeze its value-object schema and error codes, define checker trust and the source-to-local assumption map. Resolve these before declaring implementation readiness.

## Dependencies and bounded delivery

- Specify source assumptions and checker trust configuration before implementation readiness.
- Bind prospective acceptance tests to an existing production port; record a real mutation failure before GREEN.
- Coordinate the diagnostic/production boundary with the Woland transition epic and native host owners.

1. Researcher specifies the finite instance and assumption map; Koroviev records counterexamples and scope objections.
2. DEV_MGR chooses the existing system port and implementation target; Hella checks input shape and Azazello fixes budget and owned paths.
3. QA_MGR and Soviet Inspector run the production-bound negative and positive controls in batches of at most three test files; repair attempts are bounded to three. Native compilation uses `cargo ... -j 1`.
4. Woland adjudicates from bound checker evidence; DOC_MGR checks links/encoding and BUILDER checks the theoretical minimum. Preserve all unresolved objections. Output is a SoftwareQaReceiptV1 only after its production schema and writer are bound.

## Theoretical minimum and proposed TDD acceptance

| Element | Required experiment |
| --- | --- |
| INVARIANT | Candidate, source, assumptions and checker refer to the same finite task; diagnostic evidence grants no authority. |
| BREAK | Give one arm extra retries or remove refused trials from its denominator. |
| WITNESS | The campaign audit must expose the budget or denominator mismatch. |
| MUTATION | Apply the BREAK to the selected production path after its owner is resolved; require the negative control to turn RED, restore the implementation, then rerun GREEN. No production mutation is claimed executed by this draft. |

Landau Class 1: positive finite example. Class 2: malformed input. Class 3: changed-source/candidate transplant. Class 4: the counterexample above. Class 5: production-bound replay and mutation. All five are **proposed acceptance tests** until recorded against the chosen implementation; mock-only Class 0 evidence is insufficient.

The implemented planning check is `py -3.12 -m omega_engine_product_planning_office.use_cases.prior_art_epic_audit`. It checks source and navigation custody, not the experiment's correctness. The experiment's production test command remains a required design decision owned by this system.

## Claim discipline

- What it supports: a linked, bounded experiment and explicit readiness blockers for this system.
- What it does not support: implementation completion, source-theorem adoption, general mathematical correctness, publication, or an authority grant.
- Narrowest defensible claim: the experiment has a concrete input/output boundary and a falsifier; its production binding remains open.
- Next test needed: run the planning audit above, then settle the production port and author the Class 1–5 acceptance tests before implementation.

## Obstruction review and TDD test plan

**Plan status:** proposed behavior tests; no implementation completion is implied. The [requested TDD skill](../../../../.agents/skills/ext-mattpocock-tdd/SKILL.md) currently contains an operadic signature and authority fence only. The concrete RED/GREEN sequence below is this plan's specification, not an invented additional skill instruction.

**Existing public seam:** [check_evidence](../../../../omega_engine_operations/use_cases/verification/evidence_freshness.py). Freshness checking is implemented. The paired campaign protocol and statistical claim are new bounded experiment work, requiring a declared comparison rule before sampling.

**Bounded behavior:** Run a paired replay campaign with frozen candidate, model, seed, denominator and revision metadata.

**Independent oracle:** Compare two fixture runs with identical declared inputs and independently counted attempts; both success and failure remain in the denominator.

| Ordered slice | RED observation to require | Minimal GREEN and refactor boundary |
| --- | --- | --- |
| 1: finite positive control | Add one externally observable assertion for the bounded example above. If it already passes, record it as a characterization control; do not claim a new RED. | Reuse the existing seam and its value objects. Add only behavior needed for the first unmet assertion, then refactor with that test green. |
| 2: adversarial control | Drop failed attempts, change the candidate SHA, or relabel an old receipt as current; campaign acceptance must refuse the discrepancy. | Enforce the actual missing predicate at the owning seam. Keep the valid control green and preserve the typed refusal. |
| 3: replay and recovery | Rerun only the stale pair with a fresh receipt linked to the old failure; do not erase failed trials or change denominator rules. | Restore the original implementation after mutation, rerun the same controls, then refactor without changing the oracle, input bytes or claimed scope. |

**Proposed test file:** `omega_engine_operations/tests/test_prior_art_paired_replay.py`. It is a future acceptance target, not an existing suite or a recorded pass. Invoke one slice/test at a time before extending this file; keep batches to at most three files/crates and Rust compilation at `-j 1`.

```powershell
py -3.12 -m pytest omega_engine_operations/tests/test_prior_art_paired_replay.py -q
```

**Decisive mutation target:** the linked existing seam is the integration target; select and record the exact predicate/function at implementation time. The mutation must remove the adversarial check above and make its behavior test fail. Source presence is verified here; execution of that mutation and RED/GREEN recovery is not claimed. A missing semantic layer remains a blocking dependency, not a passing mock substitute.

**Review-loop exit:** this epic can leave planning review only after source assumptions, public inputs/outputs, refusal behavior, oracle and dependency owner are explicit. Broad research residuals above retain RESEARCH_HOLD. QA must bind test command, interpreter/compiler version, candidate SHA and mutation evidence to real receipts before any implementation claim. Re-enter the full epic walk whenever source or acceptance semantics change.

Cross-epic ownership and retained custody follow the [integration decision](../../decisions/adr_20261010_epic_integration_ownership.md).
