import «l1c_t01_attainment»
import «l1c_t02_quotient_norm»
import «l1c_t03_weak_duality»
import «l1c_t04_complementary_slackness»
import «l1c_t05_cycle_invariant»
import «l1c_t07_bianchi_nilpotency»
import «l1c_general_certificate»
import «l1c_lp_cochains»
import «l1c_lp_duality»
import «l1c_lp_strict_uniqueness»
import «l1c_lp_hodge_decomposition»

/-!
# L1-Native Cohomology — Lean 4 Formal Mechanization Core

This package mechanizes the core theorems of Paper 007:
- `l1c_t01_attainment`: Gauge-fixed kernel triviality and discrete coercivity bound.
- `l1c_t02_quotient_norm`: Subadditivity, positive-definiteness under w > 0, and zero-weight refusal.
- `l1c_t03_weak_duality`: Weak LP duality and capacity-bounded circulation lower bounds.
- `l1c_t04_complementary_slackness`: Exact coordinatewise certificate for zero duality gap.
- `l1c_t05_cycle_invariant`: Gauge invariance of cycle flux and 1-sparse representative attainment.
- `l1c_t07_bianchi_nilpotency`: Triangle, plaquette, and 5-cycle Bianchi/nilpotency witnesses.
- `l1c_general_certificate`: General finite matrix certificate optimality theorem in arbitrary dimension m.

Requirement R4 L^p Generalization Modules:
- `l1c_lp_cochains`: Finite-dimensional L^p cochains, weighted L^p power norms, and quotient defect Φ_p.
- `l1c_lp_duality`: Universal Hölder weak duality ⟨W, h⟩ ≤ ‖W‖_q ‖h - d₀ f‖_p for all circulations d₀* W = 0.
- `l1c_lp_strict_uniqueness`: Strictly unique quotient minimizer theorem for p ∈ (1, ∞) via strict convexity.
- `l1c_lp_hodge_decomposition`: p = 2 Hodge-Helmholtz orthogonal decomposition, d₀* divergence adjoint, orthogonality im(d₀) ⊥ ker(d₀*), and energy conservation.

All theorem modules compile cleanly with proof-placeholder commands absent and
foundational axioms restricted to `{propext, Classical.choice, Quot.sound}`.

AuthorityEffect: None.
-/
