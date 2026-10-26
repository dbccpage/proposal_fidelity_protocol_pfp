# Epic: Proof and claim assumption matrices for source transfers

**Epic ID:** `EPIC-OE-OERPAPERS-PRIOR-ART-001`
**AuthorityEffect:** None
**Status:** `RESEARCH_HOLD`
**Design readiness:** bounded experiment specified; production contract and source assumptions remain open.
**System:** [omega_engine_research_papers](../../../../omega_engine_research_papers)
**Registry relationship:** `DIRECT_REGISTRY_ASSIGNMENT`; 177 file rows directly assigned to this system.
**Owner:** maintainers of `omega_engine_research_papers`; specialist roles below.
**Date:** 2026-10-10

## Problem and source-derived experiment

Reader editions and model explanations cannot establish that a proposed local theorem follows under its actual assumptions.

Specify a single source lemma with formal statement, local carrier, axiom list, proof artifact and independent reproduction command.

This is a proposed transfer from the linked source material. A relevance score of 5 is discovery metadata. Source titles, abstracts and transcription summaries are not adopted theorem statements or implementation receipts.

## Prior art and existing plan boundary

- [LIB-016814_mathematics_with_large_la.md](../../../research_papers/library/02_formal_verification/LIB-016814_mathematics_with_large_la.md) — `direct`; SHA-256 `c4780b9147c316dd55bb554af4efa590edba3fbb99c21cf84274667ad7ec607b`.
- [LIB-019769_verified_reductions_for_o.md](../../../research_papers/library/05_optimization_and_search/LIB-019769_verified_reductions_for_o.md) — `integration_hypothesis`; SHA-256 `fd1fc6447229e62b0d70c65f99b6039532c9c4e1b3e4a958af21d4efd39855f9`.

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

1. Researcher specifies the finite instance and assumption map; Koroviev records counterexamples and scope objections.
2. DEV_MGR chooses the existing system port and implementation target; Hella checks input shape and Azazello fixes budget and owned paths.
3. QA_MGR and Soviet Inspector run the production-bound negative and positive controls in batches of at most three test files; repair attempts are bounded to three. Native compilation uses `cargo ... -j 1`.
4. Woland adjudicates from bound checker evidence; DOC_MGR checks links/encoding and BUILDER checks the theoretical minimum. Preserve all unresolved objections. Output is a SoftwareQaReceiptV1 only after its production schema and writer are bound.

## Theoretical minimum and proposed TDD acceptance

| Element | Required experiment |
| --- | --- |
| INVARIANT | Candidate, source, assumptions and checker refer to the same finite task; diagnostic evidence grants no authority. |
| BREAK | Substitute a narrower finite replay for the stated general lemma. |
| WITNESS | The claim matrix must record the scope mismatch and retain the unresolved proof obligation. |
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

**Existing public seam:** [compile_proof_obligation / verify_proof_return](../../../../omega_engine_research_papers/use_cases/paper_iteration/proof_obligation_bridge.py). The existing bridge binds proof traffic. Mathematical validity still depends on the selected prover/kernel, assumptions and source-to-formal translation; compilation alone is insufficient.

**Bounded behavior:** Compile one span-bound proof obligation and return evidence for that same source span, assumptions and candidate.

**Independent oracle:** Use a finite checked lemma with an explicit assumption list and compare obligation/candidate/span digests independently.

| Ordered slice | RED observation to require | Minimal GREEN and refactor boundary |
| --- | --- | --- |
| 1: finite positive control | Add one externally observable assertion for the bounded example above. If it already passes, record it as a characterization control; do not claim a new RED. | Reuse the existing seam and its value objects. Add only behavior needed for the first unmet assertion, then refactor with that test green. |
| 2: adversarial control | Return a proof for a different source span, omit an assumption, or report a numeric diagnostic as a theorem; the return must remain refused/unproved. | Enforce the actual missing predicate at the owning seam. Keep the valid control green and preserve the typed refusal. |
| 3: replay and recovery | Recompile changed text as a new obligation and rerun the checker; previous proof bytes remain associated with the previous span. | Restore the original implementation after mutation, rerun the same controls, then refactor without changing the oracle, input bytes or claimed scope. |

**Proposed test file:** `omega_engine_research_papers/tests/test_prior_art_proof_assumptions.py`. It is a future acceptance target, not an existing suite or a recorded pass. Invoke one slice/test at a time before extending this file; keep batches to at most three files/crates and Rust compilation at `-j 1`.

```powershell
py -3.12 -m pytest omega_engine_research_papers/tests/test_prior_art_proof_assumptions.py -q
```

**Decisive mutation target:** the linked existing seam is the integration target; select and record the exact predicate/function at implementation time. The mutation must remove the adversarial check above and make its behavior test fail. Source presence is verified here; execution of that mutation and RED/GREEN recovery is not claimed. A missing semantic layer remains a blocking dependency, not a passing mock substitute.

**Review-loop exit:** this epic can leave planning review only after source assumptions, public inputs/outputs, refusal behavior, oracle and dependency owner are explicit. Broad research residuals above retain RESEARCH_HOLD. QA must bind test command, interpreter/compiler version, candidate SHA and mutation evidence to real receipts before any implementation claim. Re-enter the full epic walk whenever source or acceptance semantics change.

Cross-epic ownership and retained custody follow the [integration decision](../../decisions/adr_20261010_epic_integration_ownership.md).
