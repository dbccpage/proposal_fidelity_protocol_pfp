# Withdrawn Pre-Review Text (Retained for Provenance)

**Historical Archive (2026-09-30).** This file preserves withdrawn pre-review text from earlier working drafts for historical and provenance tracking. It does not represent current release claims and is superseded by the release-facing documentation.

---

The general real Lp/Schatten discussion is prose mathematics, not a completed Lean formalization. New Lean modules use integer three-cycle cochains, natural exponents and explicit hypotheses. Zero energy of a difference implies gauge-fixed equality; this does not establish strict convexity or general minimizer uniqueness. The finite list certificate uses capacity, circulation and saturation hypotheses. It is not a general Fenchel-Rockafellar duality proof.

Python p=2 and p=infinity solvers use rational arithmetic. Interior-p iterations and matrix singular values use float64. `numerical_checks_passed` reports tolerance checks; `is_certified` is always false for the interior-p iterations. The weighted p=infinity convention is max(w*abs(x)), not the limit of the finite-p convention for nonuniform weights. Potential uniqueness needs a gauge on each component. Normalized dual formulas require nonzero residual; at zero, zero is a dual maximizer and uniqueness is not asserted.

# An L1 Obstruction Framework for Coboundary Defects: Lp Solvers, Schatten Presheaves, and Primal-Dual Iterators

**Paper Key:** `001_finite_obstruction_calculus/003_l1_obstruction_framework`  
**Series:** `001_finite_obstruction_calculus`  
**Author:** Jeremy H. Carroll  
**Version:** 5.5.0 (2026-09-30)  

## 1. Overview

This package synthesizes the finite $\ell^1$ obstruction framework for coboundary defects and establishes its extension across the $L^p$ and Schatten-$p$ families ($p \in [1, \infty]$):

- **Functorial Defect Aggregation (§2):** Establishes monotonicity of coboundary norms under contractive pushforwards $\pi_*$ (Theorem 2.1).
- **Operator-Valued Presheaves and Schatten-$p$ Duality (§3):** Generalizes stalks to Schatten-$p$ spaces $\mathcal{S}_p(\mathcal{H})$ ($p \in [1, \infty]$), establishing non-commutative Hölder duality $|\operatorname{Tr}(X^* Y)| \le \|X\|_{S_q} \|Y\|_{S_p}$ (Theorem 3.0), polar witness alignment, and Kadison-isometry unitary gauge invariance (Proposition 3.1, Theorem 3.1).
- **Primal--Dual Iterators and Graph $p$-Laplacian Optimality (§4):** Characterizes KKT fixed points across $L^p$ and Schatten-$p$ (Theorem 4.2). For $p \in (1, \infty)$, quotient minimizers satisfy the discrete graph $p$-Laplacian Euler--Lagrange equation:
  $$d_0^* \Big( |\omega - d_0 s^*|^{p-1} \operatorname{sgn}(\omega - d_0 s^*) \Big) = 0$$
  certified by divergence-free dual circulation witnesses $d_0^* \phi^* = 0$.
- **Operator Distinguishability Bounds (§5):** Bounded telescoping path defects satisfy $T_p(\rho_a, R_{b,a}(\rho_b)) \le \frac{1}{2} I_p(s)$ across the Schatten-$p$ family (Theorem 5.1).

## 2. Lean 4 Formalization (`lean4/`)

| Module | Contents & Verified Claims | Axioms |
| :--- | :--- | :---: |
| `lp_cochains.lean` | Cochain spaces, vector operations, $L^p$ power norms, non-negativity of $\Phi_p$ | `[propext, Quot.sound]` |
| `lp_weak_duality.lean` | General Hölder weak duality, divergence-free circulation pairing | `[propext, Classical.choice, Quot.sound]` |
| `lp_strict_convexity.lean` | Strict uniqueness of $L^2$ and $L^p$ minimizers for $p \in (1, \infty)$ | `[propext, Quot.sound]` |
| `lp_general_certificate.lean` | Finite certificate duality and optimality certificate | `[propext, Classical.choice, Quot.sound]` |
| `lp_hodge_helmholtz.lean` | $p=2$ Hodge--Helmholtz orthogonal split, Pythagorean energy conservation | `[propext, Quot.sound]` |
| `lp_core.lean` | Consolidated umbrella module importing all theorems | `[propext, Classical.choice, Quot.sound]` |

## 3. Python Verification Suite (`code/` and `tests/`)

1. **Zero-Float Exact Rational Solvers:**
   - $p = 1$: Two-phase Simplex LP solver (`ExactTwoPhaseSimplexSolver`).
   - $p = 2$: Moore--Penrose pseudoinverse graph Laplacian solver (`ExactRationalL2LaplacianSolver`).
   - $p = \infty$: Chebyshev LP solver (`ExactRationalLinfChebyshevSolver`).
2. **High-Precision Continuous $L^p$ Solvers:**
   - IRLS and Proximal Bregman gradient descent with Armijo backtracking (`HighPrecisionLpConvexSolver`).
3. **Operator-Valued Schatten-$p$ Module:**
   - Matrix coboundaries, Schatten-$p$ norm evaluation, non-commutative Hölder duality, Kadison unitary invariance (`OperatorSchattenPModule`).
4. **Primal-Dual Fixed-Point Iteration:**
   - Local primal-dual iterator verification and functorial aggregation (`LocalPrimalDualIterator`, `FunctorialAggregation`).
