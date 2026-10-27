# Epic: Transport assumptions and identity witnesses

**Epic ID:** `EPIC-OE-OERUST-PRIOR-ART-005`
**AuthorityEffect:** None
**Status:** `RESEARCH_HOLD`
**Design readiness:** bounded experiment specified; production contract and source assumptions remain open.
**System:** [engine/crates_rs/core_homotopy_type_theory](../../../../engine/crates_rs/core_homotopy_type_theory)
**Registry relationship:** `INTEGRATION_HYPOTHESIS`; 0 file rows directly assigned to this system.
**Owner:** maintainers of `engine/crates_rs/core_homotopy_type_theory`; specialist roles below.
**Date:** 2026-10-10

## Problem and source-derived experiment

Informal higher-structure analogies omit the identity and transport assumptions needed by a kernel.

Specify one finite identity-transport example and list every equality principle and axiom used by its checker.

This is a proposed transfer from the linked source material. A relevance score of 5 is discovery metadata. Source titles, abstracts and transcription summaries are not adopted theorem statements or implementation receipts.

## Prior art and existing plan boundary

- [LIB-000044_multitensor_lifting_.md](../../../../library/coda_library/markdown/LIB-000044_multitensor_lifting_.md) — `integration_hypothesis`; SHA-256 `b21e4cbb92ed54ee52394b29f1dcc26305d3b412a54ce008f4821470e77ab273`.
- [LIB-000023_on_homotopy_invarian.md](../../../../library/coda_library/markdown/LIB-000023_on_homotopy_invarian.md) — `integration_hypothesis`; SHA-256 `21945a07136f08d63939e0b1b2ea9f75932cd3b60b42417884eb32da2e63e942`.

Use the [estate epic index](../README.md) to resolve adjacent owners and the [design-review reconciliation](../../../receipts/epic_design_review_20261010.md) for current OEWAS/Adversary limits. This epic adds the experiment above; existing suite plans continue to own their broader architecture, migrations and release work.

## Contract to settle before implementation

- Input: frozen source revision and byte digest, finite task instance, explicit assumptions, observation basis, checker identity and budget.
- Output: typed result with candidate and evidence digests, separate diagnostic and authorization status, residual obligations and next action.
- Refusal: malformed input, missing oracle, mismatched source/candidate bytes, or undeclared authority produces an explicit refusal or open residual.
- Recovery: retain the failed candidate and dissent; re-evaluate changed bytes under the same run budget. Never reinterpret an earlier receipt as checking new bytes.
- Open design decisions: choose the existing owning production port, freeze its value-object schema and error codes, define checker trust and the source-to-local assumption map. Resolve these before declaring implementation readiness.

## Dependencies and bounded delivery

- Specify source assumptions and checker trust configuration before implementation readiness.
- Bind prospective acceptance tests to an existing production port; record a real mutation failure before GREEN.

1. Researcher specifies the finite instance and assumption map; Defect Hunter records counterexamples and scope objections.
2. DEV_MGR chooses the existing system port and implementation target; Syntax Prefilter checks input shape and Scope Guard fixes budget and owned paths.
3. QA_MGR and Inspector run the production-bound negative and positive controls in batches of at most three test files; repair attempts are bounded to three. Native compilation uses `cargo ... -j 1`.
4. Adversary adjudicates from bound checker evidence; DOC_MGR checks links/encoding and BUILDER checks the theoretical minimum. Preserve all unresolved objections. Output is a SoftwareQaReceiptV1 only after its production schema and writer are bound.

## Theoretical minimum and proposed TDD acceptance

| Element | Required experiment |
| --- | --- |
| INVARIANT | Candidate, source, assumptions and checker refer to the same finite task; diagnostic evidence grants no authority. |
| BREAK | Replace a witnessed equality with a textual assertion. |
| WITNESS | A missing witness must remain an open obligation. |
| MUTATION | Apply the BREAK to the selected production path after its owner is resolved; require the negative control to turn RED, restore the implementation, then rerun GREEN. No production mutation is claimed executed by this draft. |

Examiner Class 1: positive finite example. Class 2: malformed input. Class 3: changed-source/candidate transplant. Class 4: the counterexample above. Class 5: production-bound replay and mutation. All five are **proposed acceptance tests** until recorded against the chosen implementation; mock-only Class 0 evidence is insufficient.

The implemented planning check is `py -3.12 -m product_planning_office.use_cases.prior_art_epic_audit`. It checks source and navigation custody, not the experiment's correctness. The experiment's production test command remains a required design decision owned by this system.

## Claim discipline

- What it supports: a linked, bounded experiment and explicit readiness blockers for this system.
- What it does not support: implementation completion, source-theorem adoption, general mathematical correctness, publication, or an authority grant.
- Narrowest defensible claim: the experiment has a concrete input/output boundary and a falsifier; its production binding remains open.
- Next test needed: run the planning audit above, then settle the production port and author the Class 1–5 acceptance tests before implementation.

## Obstruction review and TDD test plan

**Plan status:** proposed behavior tests; no implementation completion is implied. The [requested TDD skill](../../../../.agents/skills/ext-mattpocock-tdd/SKILL.md) currently contains an operadic signature and authority fence only. The concrete RED/GREEN sequence below is this plan's specification, not an invented additional skill instruction.

**Existing public seam:** [IdentityEliminator.validate / PathTransport](../../../../engine/crates_rs/core_homotopy_type_theory/src/path_transport.rs). The module explicitly implements shape checks, not J-elimination or univalence. A trusted semantic checker is a separate blocking dependency.

**Bounded behavior:** Retain every transport reference and classify a nonempty record as shape-valid only.

**Independent oracle:** Hand-enumerate one fixture with all four nonempty references and four fixtures omitting one field each. Assign shape-valid/shape-invalid expected results before invoking validate; this table supplies no semantic identity proof.

| Ordered slice | RED observation to require | Minimal GREEN and refactor boundary |
| --- | --- | --- |
| 1: finite positive control | Add one externally observable assertion for the bounded example above. If it already passes, record it as a characterization control; do not claim a new RED. | Reuse the existing seam and its value objects. Add only behavior needed for the first unmet assertion, then refactor with that test green. |
| 2: adversarial control | Give a well-shaped record an unrelated result reference; the planned semantic layer must not label it a proved identity merely because validate succeeds. | Enforce the actual missing predicate at the owning seam. Keep the valid control green and preserve the typed refusal. |
| 3: replay and recovery | Keep the shape-valid record available as an unresolved semantic obligation; no synthetic proof is added during recovery. | Restore the original implementation after mutation, rerun the same controls, then refactor without changing the oracle, input bytes or claimed scope. |

**Proposed test file:** `engine/crates_rs/core_homotopy_type_theory/tests/prior_art_transport_assumptions.rs`. It is a future acceptance target, not an existing suite or a recorded pass. Invoke one slice/test at a time before extending this file; keep batches to at most three files/crates and Rust compilation at `-j 1`.

```powershell
cargo test --manifest-path engine/crates_rs/Cargo.toml -p core_homotopy_type_theory --test prior_art_transport_assumptions -j 1
```

**Decisive mutation target:** the linked existing seam is the integration target; select and record the exact predicate/function at implementation time. The mutation must remove the adversarial check above and make its behavior test fail. Source presence is verified here; execution of that mutation and RED/GREEN recovery is not claimed. A missing semantic layer remains a blocking dependency, not a passing mock substitute.

**Review-loop exit:** this epic can leave planning review only after source assumptions, public inputs/outputs, refusal behavior, oracle and dependency owner are explicit. Broad research residuals above retain RESEARCH_HOLD. QA must bind test command, interpreter/compiler version, candidate SHA and mutation evidence to real receipts before any implementation claim. Re-enter the full epic walk whenever source or acceptance semantics change.

Cross-epic ownership and retained custody follow the [integration decision](../../decisions/adr_20261010_epic_integration_ownership.md).
