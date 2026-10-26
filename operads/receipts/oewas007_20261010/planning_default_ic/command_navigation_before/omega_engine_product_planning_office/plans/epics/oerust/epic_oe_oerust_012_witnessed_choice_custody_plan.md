# Epic: Witnessed-choice source custody and current owner resolution

**Epic ID:** `EPIC-OE-OERUST-PRIOR-ART-012`
**AuthorityEffect:** None
**Status:** `RESEARCH_HOLD`
**Design readiness:** bounded experiment specified; production contract and source assumptions remain open.
**System:** [omega_engine/crates_rs/omega_wdp](../../../../omega_engine/crates_rs/omega_wdp)
**Registry relationship:** `DIRECT_REGISTRY_ASSIGNMENT`; 4 file rows directly assigned to this system.
**Owner:** maintainers of `omega_engine/crates_rs/omega_wdp`; specialist roles below.
**Date:** 2026-10-10

## Problem and source-derived experiment

The registry retains a WDP path while architecture notes describe decomposition; ownership must be resolved before new implementation.

Locate the current owner of one finite witnessed-choice example; pin its symmetry group, witness format and nonselection assumptions.

This is a proposed transfer from the linked source material. A relevance score of 5 is discovery metadata. Source titles, abstracts and transcription summaries are not adopted theorem statements or implementation receipts.

## Prior art and existing plan boundary

- [LIB-016574_witnessed_symmetric_choice_stronger_cpt.md](../../../../omega_engine_library/coda_library/markdown/LIB-016574_witnessed_symmetric_choice_stronger_cpt.md) — `direct`; SHA-256 `09a92f0bfc324c71b03053054165f52994eedd0931fde234219572bd2ab442f0`.

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
| BREAK | Let a lexicographic identifier silently select an orbit representative. |
| WITNESS | A permutation audit must expose the undeclared selection rule; source claims stay unadopted. |
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

**Existing public seam:** [propose_transport / verify_transport](../../../../omega_engine/crates_rs/omega_wdp/src/guarded_chain_transport.rs). Witnessed finite transport does not discharge an unrestricted choice principle. Observer completeness and source predicate adequacy remain separately stated assumptions.

**Bounded behavior:** Construct and independently verify one bounded chain transport while retaining its witness and observation basis.

**Independent oracle:** Use a minimal pairs/capacity instance and independently enumerate the event/task cells and boundary identities.

| Ordered slice | RED observation to require | Minimal GREEN and refactor boundary |
| --- | --- | --- |
| 1: finite positive control | Add one externally observable assertion for the bounded example above. If it already passes, record it as a characterization control; do not claim a new RED. | Reuse the existing seam and its value objects. Add only behavior needed for the first unmet assertion, then refactor with that test green. |
| 2: adversarial control | Change one witness matrix coefficient or source-cell identifier; verify_transport must reject the mismatched transport. | Enforce the actual missing predicate at the owning seam. Keep the valid control green and preserve the typed refusal. |
| 3: replay and recovery | Restore the proposal and verify again with the same parameters; failed proposals remain recorded. | Restore the original implementation after mutation, rerun the same controls, then refactor without changing the oracle, input bytes or claimed scope. |

**Proposed test file:** `omega_engine/crates_rs/omega_wdp/tests/prior_art_witnessed_choice.rs`. It is a future acceptance target, not an existing suite or a recorded pass. Invoke one slice/test at a time before extending this file; keep batches to at most three files/crates and Rust compilation at `-j 1`.

```powershell
cargo test --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_wdp --test prior_art_witnessed_choice -j 1
```

**Decisive mutation target:** the linked existing seam is the integration target; select and record the exact predicate/function at implementation time. The mutation must remove the adversarial check above and make its behavior test fail. Source presence is verified here; execution of that mutation and RED/GREEN recovery is not claimed. A missing semantic layer remains a blocking dependency, not a passing mock substitute.

**Review-loop exit:** this epic can leave planning review only after source assumptions, public inputs/outputs, refusal behavior, oracle and dependency owner are explicit. Broad research residuals above retain RESEARCH_HOLD. QA must bind test command, interpreter/compiler version, candidate SHA and mutation evidence to real receipts before any implementation claim. Re-enter the full epic walk whenever source or acceptance semantics change.

Cross-epic ownership and retained custody follow the [integration decision](../../decisions/adr_20261010_epic_integration_ownership.md).
