# Lean 4 Provenance and Compile Receipts: Paper 002

**Review scope (2026-10-07). Evidence Scope:**

The general real Lp/Schatten discussion is prose mathematics, not a completed
Lean formalization. New Lean modules use integer three-cycle cochains, natural
exponents and explicit hypotheses. Zero energy of a difference implies gauge-fixed
equality; this does not prove strict convexity or general minimizer uniqueness.
The finite list certificate uses capacity, circulation and saturation hypotheses.
It is not a general Fenchel-Rockafellar duality proof.

Python p=2 and p=infinity solvers use rational arithmetic. Interior-p iterations
and matrix singular values use float64. `numerical_checks_passed` reports tolerance
checks; `is_certified` is always false for the interior-p iterations. The weighted
p=infinity convention is max(w*abs(x)), not the limit of the finite-p convention
for nonuniform weights. Potential uniqueness needs a gauge on each component.
Normalized dual formulas require nonzero residual; at zero, zero is a dual
maximizer and uniqueness is not asserted.

See [the evidence scope](../REVIEW_SCOPE.md).

## Environment

* Toolchain: `leanprover/lean4:v4.33.1`
* Standard foundational axioms: `{propext, Classical.choice, Quot.sound}`
* Proof-placeholder commands: absent across all claim-bearing modules

## Module Inventory & Axiom Audit

* `l1c_t01_attainment.lean`: 100 lines, no proof-placeholder commands, axioms in `{propext, Quot.sound}`
* `l1c_t02_quotient_norm.lean`: 167 lines, no proof-placeholder commands, axioms in `{propext, Quot.sound}`
* `l1c_t03_weak_duality.lean`: 136 lines, no proof-placeholder commands, axioms in `{propext, Quot.sound}`
* `l1c_t04_complementary_slackness.lean`: 66 lines, no proof-placeholder commands, axioms in `{propext, Quot.sound}`
* `l1c_t05_cycle_invariant.lean`: 99 lines, no proof-placeholder commands, axioms in `{propext, Classical.choice, Quot.sound}`
* `l1c_t07_bianchi_nilpotency.lean`: 99 lines, no proof-placeholder commands, axioms in `{propext, Quot.sound}`
* `l1c_general_certificate.lean`: 163 lines, no proof-placeholder commands, axioms in `{propext, Classical.choice, Quot.sound}`
* `l1c_lp_cochains.lean`: 153 lines, no proof-placeholder commands, axioms in `{propext, Quot.sound}`
* `l1c_lp_duality.lean`: 100 lines, no proof-placeholder commands, axioms in `{propext, Classical.choice, Quot.sound}`
* `l1c_lp_strict_uniqueness.lean`: 151 lines, no proof-placeholder commands, axioms in `{propext, Quot.sound}`
* `l1c_lp_hodge_decomposition.lean`: 96 lines, no proof-placeholder commands, axioms in `{propext, Quot.sound}`
* `l1c_core.lean`: 35 lines (root aggregator importing all 11 modules)

All axiom reports conclude strictly inside the standard Lean kernel trio (`propext`, `Classical.choice`, `Quot.sound`). Zero custom or unverified axioms are admitted.
