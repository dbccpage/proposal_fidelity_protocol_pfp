# L1-Native Cohomology Lean 4 Formalization Estate

**Review scope (2026-10-10). Evidence Scope:**

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

This directory contains the Lean 4 formalization estate for *L1-Native Cohomology of Finite Defect Fields* (Paper 002). It includes a general finite list certificate theorem for L1C-TG, finite model/core proofs for the cycle, ambient weighted-norm, complementary-slackness, sparse-representative, and Bianchi witnesses, and scoped integer three-cycle L^p lemmas.

## Modules

| File | Claim / Scope | Key Theorems | Axioms |
|---|---|---|---|
| `l1c_t01_attainment.lean` | L1C-T1, §2 | `gauge_fixed_kernel_trivial`, `potential_v1_le_edge0`, `potential_v2_le_edge_sum`, `l1c_t01_coercivity_bound` | `{propext, Quot.sound}` |
| `l1c_t02_quotient_norm.lean` | L1C-T2, §2 | `cycle3_d0_add`, `residual3_add`, `l1_norm3_nonneg`, `l1_norm3_triangle`, `l1_quotient_subadditive`, `l1_norm3_positive_definite`, `zero_weight_refusal_counterexample` | `{propext, Quot.sound}` |
| `l1c_t03_weak_duality.lean` | L1C-T3, §3 | `int_mul_le_weight_abs`, `circulation_annihilates_coboundary`, `circulation_pairing_gauge_invariant`, `l1c_t03_weak_duality` | `{propext, Quot.sound}` |
| `l1c_t04_complementary_slackness.lean` | L1C-T4, §4 | `pairing_eq_l1_norm_of_cs`, `l1c_t04_zero_duality_gap`, `l1c_t04_primal_optimality` | `{propext, Quot.sound}` |
| `l1c_t05_cycle_invariant.lean` | L1C-T5, §5 | `cycle3_residual_flux_invariant`, `abs_sum3_le`, `nat_weighted_sum_lower_bound`, `cycle3_topological_lower_bound`, `sparse_representative_attainment` | `{propext, Classical.choice, Quot.sound}` |
| `l1c_t07_bianchi_nilpotency.lean` | L1C-T7, §7 | `triangle_bianchi_nilpotency`, `plaquette_bianchi_nilpotency`, `cycle5_loop_nilpotency` | `{propext, Quot.sound}` |
| `l1c_general_certificate.lean` | L1C-TG, §4 | `dot_vec_add`, `dot_le_weighted_l1_norm`, `general_finite_certificate_optimality` | `{propext, Classical.choice, Quot.sound}` |
| `l1c_lp_cochains.lean` | R4.1, L^p Cochains | `lp_pow_norm_nonneg`, `lp_defect_nonneg`, `phi_p_3_nonneg` | `{propext, Quot.sound}` |
| `l1c_lp_duality.lean` | R4.2, Weak Duality | `circulation_iff_divergence_free`, `circulation_pairing_gauge_invariant`, `holder_weak_duality_1_inf`, `holder_weak_duality_divergence_free` | `{propext, Classical.choice, Quot.sound}` |
| `l1c_lp_strict_uniqueness.lean` | R4.3, Gauge-fixed zero-difference implication | `l2sq3_zero_iff`, `lp_pow3_zero_iff`, `gauge_fixed_l2_zero_difference`, `gauge_fixed_lp_zero_difference` | `{propext, Quot.sound}` |
| `l1c_lp_hodge_decomposition.lean` | R4.4, Hodge Decomposition | `cycle3_d0_adjoint_identity`, `hodge_orthogonality`, `pythagorean_theorem3`, `hodge_helmholtz_energy_conservation` | `{propext, Quot.sound}` |
| `l1c_core.lean` | Root Aggregator | Imports all eleven theorem modules | `{propext, Classical.choice, Quot.sound}` |

## Building

Requires Lean 4 (`v4.33.1`):

```bash
lake build
```

Verification status:

- Offline clean build: PASS (0 errors).
- Axiom honesty: strictly within `{propext, Classical.choice, Quot.sound}`.
- Proof-placeholder commands: absent across all Lean source files.

Mathematical proof, originality, and formalization coverage are separate: the general finite-dimensional results have prose proofs and are classical background. L1C-T2 formalizes ambient integer three-edge weighted-norm axioms and residual-addition compatibility, not a minimized quotient norm. L1C-TG is a conditional finite integer-list theorem, without certificate existence or Python correctness. Coherence is exact for rational complex moduli and binary64 otherwise.
