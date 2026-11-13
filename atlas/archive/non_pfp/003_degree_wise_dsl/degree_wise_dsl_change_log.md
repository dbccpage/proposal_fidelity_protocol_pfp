# Change Log — Degree-Wise Obstruction Calculus and Symbolic DSL

---
title: Degree-Wise DSL Change Log
file_name: degree_wise_dsl_change_log.md
status: Canonical
canonical_paper_id: FOC-006
legacy_paper_id: Paper 012
date: 2026-09-30
version: 2.1.0
---

This document assigns no authorization and changes no jurisdiction. It carries no operational authority or institutional standing.

2026-10-09 — Package elaboration of the context-obstruction theorem
-------------------------------------------------------------------

* This is not a new Zenodo deposit and does not change the published version.
* `PaperFOC006.c3_degree_separation_instance` verifies the integer $C_3$ degree-separation instance. The $\ell^1$ distance from $(1,0,0)$ to the image of $d_0$ is $1$, that distance ignores the 2-cell flag, and the $\Gamma_2$ readout is absent or $1$ according to that flag. General $k$ and real-valued minimization stay outside this deposit.
* `PaperFOC006.PrimitiveDifference.localGreenGlobalRed_context_obstruction_of_witness` is elaborated in `lean4/DegreeSeparation.lean`. The older `OmegaCore.PrimitiveDifference` citation is not a module of this package.
* Claim C11 stays proved for context replacement only. `QM.PaperFOC006DegreeBridge`, Q admission, and `QHeld` are not theorems of this package.
* `context_obstruction_witness` in `code/mod_009_degree_wise_dsl_core.py` evaluates the manuscript pair. The gates are `(None, False)` and `(1, True)`.

v2.1.0 (2026-09-30) — Swarm Review & Packaging Harmonization
------------------------------------------------------------

* Executed `/omega-paper-review-swarm` SPOE harmonization pipeline across Stages 0–6 and Stage Ω.
* Harmonized Zero-Line Header Block, Compliance 5b `## Mechanism inventory` table with 14 bound slots, and academic nonclaims.
* Established self-contained Lean 4 package with verified axiom census `{Classical.choice, Quot.sound, propext}`.
* Implemented package-scoped test suite (`code/tests/test_004_degree_wise_dsl.py`), dynamic figure generation (`code/generate_figures.py`), and headless Jupyter companion notebook replay (`jupyter_notebooks/000_degree_wise_dsl.ipynb`).
* Rebuilt deterministic release ZIP and two-way manifest bijection (`SHA256SUMS`, `MANIFEST.sha256`).

v2.0.9 (2026-09-09) — OEARS Pipeline Audit
-------------------------------------------

* Executed `/rip-papers` perfect-one-pass pipeline pass.
* Emitted Stage 0 adversarial dialogue and 1:1 binding update packet.
* Emitted `docs/lean_claim_map.md` validating the exact boundary between `[MECHANIZED-PARTIAL]` (integer-shadow `PaperFOC006`), fully mechanized contracts, and prose claims.
* Registered open craft residual `OO-009-COV-001` (coverage N/A for self-contained DSL specification monograph).
* Completed Stage 2 Adversary evaluation receipt and Stage 4 release preflight.

v2.0.8 (2026-07-25) — FOC Closing-Arc Identity Normalization & Spec Refactoring
-------------------------------------------------------------------------------

* Standardized primary paper identity as `FOC-006 — Degree-Wise DSL` (legacy identity: `Paper 012`).
* Retyped paper front-matter to explicitly state role as DSL specification paper (`Gamma2` degree separation and local/global non-factorization as primary theorems).
* Corrected boxed statement for $\pi_Z$: degree-preserving $C^1 \to C^1$ projection requiring certified idempotence and exact-killing invariants.
* Added typed `Gamma2Readout` enum semantics (`NoComplex2 | MalformedComplex2 | Gamma2(value)`).
* Extracted transient crate implementation pointers (`apply_d1`, `apply_d0`, `solve_l1_hodge`, `cycle_space_projector.rs`) to `_support/006_implementation_registry.md`.
* Consolidated in-body changelog history into this companion change log file.

v2.0.7 (2026-07-16)
-------------------

* Added `OmegaCore.PrimitiveDifference.localGreenGlobalRed_context_obstruction_of_witness`, the reusable context-fingerprint LGGR theorem in `OmegaCosmology.Primitives.PrimitiveDifference`.
* Refactored the PaperFOC006 context theorem so `PaperFOC006.contextual_local_green_not_global_gate` is a direct specialization of the general PrimitiveDifference context theorem.
* Added encyclopedia binding `ENC-1170` for the PrimitiveDifference context-fingerprint theorem and linked PaperFOC006 `ENC-1169` to it.

v2.0.6 (2026-07-16)
-------------------

* Added `PaperFOC006.ContextualDegreeDSLState`, context replacement lemmas, and `PaperFOC006.contextual_local_green_not_global_gate`: arbitrary external context does not repair the local-fingerprint/global-gate LGGR obstruction.
* Generalized the QM wrapper from `Unit` metadata to arbitrary operator/density metadata via `QM.PaperFOC006DegreeBridge.proposal_local_green_not_global_gate`.
* Added encyclopedia binding `ENC-1169` for the context-extension LGGR non-repair theorem.

v2.0.5 (2026-07-16)
-------------------

* Added the composite Lean theorem `PaperFOC006.degreeDsl_local_green_not_global_gate`: a PrimitiveDifference quotient preserving the local fingerprint `(C1, diagnosticConstructible)` cannot also factor the global gated readout `(Gamma2, acceptanceAuthorized)`.
* Extended `QM.PaperFOC006DegreeBridge` with local/global fingerprint definitions, metadata-invariance lemmas, a concrete graph-only/2-cell witness, and `QM.PaperFOC006DegreeBridge.unitProposal_local_green_not_global_gate`.
* Added encyclopedia binding `ENC-1168` for the composite PaperFOC006 degree/DSL LGGR boundary.

v2.0.4 (2026-07-16)
-------------------

* Strengthened the Rust PL-012-1 conformance suite in `omega_engine/crates/omega_functional/tests/conformance_pl012_descent_dsl.rs` from 9 to 14 tests.
* Added `omega_functional::gamma2::Complex2InputQ` and `ExactGamma2Error::MissingComplex2` so absent `Complex2` is an explicit rejected input.
* Added evaluator-boundary tests proving the guarded `Phi1 > Gamma2 > Xi` order refuses scalar-score laundering.

v2.0.3 (2026-07-16)
-------------------

* Added `PaperFOC006.HasGamma2Readout` and theorems naming the missing-2-cell gate.
* Added QM-facing Lean bridge `QM.PaperFOC006DegreeBridge`.
* Added encyclopedia binding `ENC-1167` for the QM PaperFOC006 degree-diagnostic firewall.

v2.0.2 (2026-06-15)
-------------------

* Added Lean support in `omega_engine/lean4/PaperFOC006`: finite $C_3$ coboundary cancellation, declared-projection rewrite contract lemmas, `gamma2` undefined/visible replay, PrimitiveDifference LGGR theorem.

v2.0.1 (2026-06-09)
-------------------

* Improver hygiene pass (Stage 1).
* Claim-typed Degree Separation Theorem at honest strength.
* Created sibling claim ledger `006_degree_wise_dsl_claim_ledger.md`.

v1.0 (April 2026)
-----------------

* Initial formulation of degree-wise calculus DSL.
