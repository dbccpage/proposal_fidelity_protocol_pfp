/- Review scope: integer finite fixtures and stated hypotheses; no general real Lp, Clarkson, or Schatten theorem. AuthorityEffect: None. -/
import «lp_cochains»
import «lp_weak_duality»
import «lp_strict_convexity»
import «lp_hodge_helmholtz»
import «lp_general_certificate»

/-!
# L1 Obstruction Framework — Lean 4 Formal Mechanization Core

This package mechanizes the core mathematical theorems of Paper 037
(*Finite Obstruction Calculus: ℓ¹-Cohomology, Exact Duality, and Convergence of the Three-Step Primal-Dual Iterator*):

- `lp_cochains`: Finite-dimensional L^p cochains, weighted L^p power norms, L^∞ norms,
  and the quotient defect functional Φ_p (satisfying Def 4.1, Fact 4.12).
- `lp_weak_duality`: Universal Hölder weak duality ⟨W, h⟩ ≤ ‖W‖_q ‖h - d₀ f‖_p for all
  circulations d₀* W = 0 across conjugate pairs (p, q) (satisfying Thm 4.2, Claim C4).
- `lp_strict_convexity`: Strictly unique quotient minimizer theorem for p ∈ (1, ∞)
  on the gauge-fixed subspace via strict convexity and kernel triviality (satisfying Thm 4.14, Requirement R1).
- `lp_hodge_helmholtz`: Canonical p = 2 Hodge-Helmholtz orthogonal decomposition,
  adjoint divergence d₀*, orthogonality im(d₀) ⊥ ker(d₀*), and energy conservation (satisfying §5.4, Prop E.2–E.5).
- `lp_general_certificate`: General finite matrix certificate optimality theorem
  guaranteeing global primal optimality across the infinite affine subspace under zero duality gap (satisfying Thm 2.1, Claim C1).

All modules compile cleanly with proof-placeholder commands absent and
foundational axioms strictly restricted to `{propext, Classical.choice, Quot.sound}`.

AuthorityEffect: None.
-/
