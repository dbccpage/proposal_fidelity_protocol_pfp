# Lean 4 Provenance and Compile Receipts: Paper 037

**Review scope (2026-09-22). AuthorityEffect: None.**

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

* `lp_cochains.lean`: 229 lines, no proof-placeholder commands, axioms in `{propext, Quot.sound}`
* `lp_weak_duality.lean`: 98 lines, no proof-placeholder commands, axioms in `{propext, Classical.choice, Quot.sound}`
* `lp_strict_convexity.lean`: 150 lines, no proof-placeholder commands, axioms in `{propext, Quot.sound}`
* `lp_hodge_helmholtz.lean`: 96 lines, no proof-placeholder commands, axioms in `{propext, Quot.sound}`
* `lp_general_certificate.lean`: 143 lines, no proof-placeholder commands, axioms in `{propext, Classical.choice, Quot.sound}`
* `lp_core.lean`: 28 lines (root aggregator importing all 5 formal modules)

All axiom reports conclude strictly inside the standard Lean kernel trio (`propext`, `Classical.choice`, `Quot.sound`). Zero custom or unverified axioms are admitted.
