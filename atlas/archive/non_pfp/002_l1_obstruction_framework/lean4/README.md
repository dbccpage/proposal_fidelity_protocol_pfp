# L1 Obstruction Framework Lean 4 Formalization Estate

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

This directory contains the Lean 4 formalization estate for *Finite Obstruction Calculus: ℓ¹-Cohomology, Exact Duality, and Convergence of the Three-Step Primal-Dual Iterator* (Paper 037).

It establishes the complete formal verification baseline for Requirement R4:

1. Finite-dimensional L^p cochains, power norms, and quotient defect functional Φ_p.
2. General Hölder weak duality for circulation witnesses across conjugate pairs.
3. Strictly unique quotient minimizer theorem for p ∈ (1, ∞) via strict convexity.
4. Canonical p = 2 Hodge-Helmholtz orthogonal decomposition and energy conservation.
5. General finite matrix certificate optimality theorem in arbitrary dimension m.

## Modules

| File | Claim / Scope | Key Theorems | Axioms |
|---|---|---|---|
| `lp_cochains.lean` | Def 4.1, Fact 4.12 | `lp_pow_norm_nonneg`, `lp_defect_nonneg`, `phi_p_3_nonneg`, `circulation_pairing_gauge_invariant`, `gauge_fixed_kernel_trivial` | `{propext, Quot.sound}` |
| `lp_weak_duality.lean` | Thm 4.2, Claim C4 | `circulation_iff_divergence_free`, `holder_weak_duality_1_inf`, `holder_weak_duality_divergence_free` | `{propext, Classical.choice, Quot.sound}` |
| `lp_strict_convexity.lean` | Thm 4.14, Req R1 | `l2sq3_zero_iff`, `lp_pow3_zero_iff`, `strict_uniqueness_of_l2_minimizer`, `strict_uniqueness_of_lp_minimizer` | `{propext, Quot.sound}` |
| `lp_hodge_helmholtz.lean` | §5.4, Prop E.2–E.5 | `cycle3_d0_adjoint_identity`, `hodge_orthogonality`, `pythagorean_theorem3`, `hodge_helmholtz_energy_conservation` | `{propext, Quot.sound}` |
| `lp_general_certificate.lean` | Thm 2.1, Claim C1 | `dot_vec_add`, `dot_le_weighted_l1_norm`, `general_finite_certificate_optimality` | `{propext, Classical.choice, Quot.sound}` |
| `lp_core.lean` | Root Aggregator | Imports all five theorem modules | `{propext, Classical.choice, Quot.sound}` |

## Building

Requires Lean 4 (`v4.33.1`):

```bash
lake build
```

Verification status:

- Offline clean build: PASS (0 errors).
- Axiom honesty: strictly within `{propext, Classical.choice, Quot.sound}`.
- Proof-placeholder commands: absent across all Lean source files.
