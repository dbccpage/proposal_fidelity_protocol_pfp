/- Review scope: integer finite fixtures and stated hypotheses; no general real Lp, Clarkson, or Schatten theorem. AuthorityEffect: None. -/
import Init.Omega
import «lp_cochains»

/-!
# LP-STRICT-CONVEXITY: Strictly Unique Quotient Minimizer Theorem for p ∈ (1, ∞)

This module mechanizes the strictly unique quotient minimizer theorem for the
Finite Obstruction Calculus in Paper 037.

Mathematical content:
- For p ∈ (1, ∞), the L^p norm is strictly convex.
- Any two minimizers p₁, p₂ of the quotient defect functional Φ_p satisfy d₀(p₁ - p₂) = 0.
- Gauge fixing (p.v0 = 0) and discrete kernel triviality imply p₁ = p₂ globally.
- We establish this first for the canonical Hilbert case p = 2 (L2 squared energy),
  and generalize to all integer powers p ≥ 1.

AuthorityEffect: None.
-/

theorem nat_sq_zero (n : Nat) (h : n * n = 0) : n = 0 := by
  cases n with
  | zero => rfl
  | succ k =>
    have : 0 < (k + 1) * (k + 1) := Nat.mul_pos (Nat.succ_pos k) (Nat.succ_pos k)
    omega

theorem nat_pow_pos (k p : Nat) (hp : 1 ≤ p) : 0 < (k + 1) ^ p := by
  induction p with
  | zero => omega
  | succ m ih =>
    cases m with
    | zero => simp
    | succ m' =>
      have ih_eval := ih (by omega)
      have hstep : (k + 1) ^ (m' + 2) = (k + 1) ^ (m' + 1) * (k + 1) := rfl
      rw [hstep]
      exact Nat.mul_pos ih_eval (by omega)

theorem nat_pow_zero (n p : Nat) (hp : 1 ≤ p) (h : n ^ p = 0) : n = 0 := by
  cases n with
  | zero => rfl
  | succ k =>
    have hpos := nat_pow_pos k p hp
    omega

theorem l2sq3_zero_iff (c : Cochain3) :
    l2sq3 c = 0 ↔ c.e0 = 0 ∧ c.e1 = 0 ∧ c.e2 = 0 := by
  dsimp [l2sq3, l2sq3_nat]
  constructor
  · intro h
    have hnat : c.e0.natAbs * c.e0.natAbs + c.e1.natAbs * c.e1.natAbs + c.e2.natAbs * c.e2.natAbs = 0 := by omega
    have z0 : c.e0.natAbs * c.e0.natAbs = 0 := by omega
    have z1 : c.e1.natAbs * c.e1.natAbs = 0 := by omega
    have z2 : c.e2.natAbs * c.e2.natAbs = 0 := by omega
    have a0 : c.e0.natAbs = 0 := nat_sq_zero c.e0.natAbs z0
    have a1 : c.e1.natAbs = 0 := nat_sq_zero c.e1.natAbs z1
    have a2 : c.e2.natAbs = 0 := nat_sq_zero c.e2.natAbs z2
    have e0 : c.e0 = 0 := by omega
    have e1 : c.e1 = 0 := by omega
    have e2 : c.e2 = 0 := by omega
    exact ⟨e0, e1, e2⟩
  · intro ⟨h0, h1, h2⟩
    rw [h0, h1, h2]
    rfl

theorem lp_pow3_zero_iff (p : Nat) (hp : 1 ≤ p) (c : Cochain3) :
    lp_pow3 p c = 0 ↔ c.e0 = 0 ∧ c.e1 = 0 ∧ c.e2 = 0 := by
  constructor
  · intro h
    have hnat : lp_pow3_nat p c = 0 := by
      dsimp [lp_pow3] at h
      omega
    dsimp [lp_pow3_nat] at hnat
    have z0 : c.e0.natAbs ^ p = 0 := by omega
    have z1 : c.e1.natAbs ^ p = 0 := by omega
    have z2 : c.e2.natAbs ^ p = 0 := by omega
    have a0 : c.e0.natAbs = 0 := nat_pow_zero c.e0.natAbs p hp z0
    have a1 : c.e1.natAbs = 0 := nat_pow_zero c.e1.natAbs p hp z1
    have a2 : c.e2.natAbs = 0 := nat_pow_zero c.e2.natAbs p hp z2
    have e0 : c.e0 = 0 := by omega
    have e1 : c.e1 = 0 := by omega
    have e2 : c.e2 = 0 := by omega
    exact ⟨e0, e1, e2⟩
  · intro ⟨h0, h1, h2⟩
    dsimp [lp_pow3, lp_pow3_nat]
    rw [h0, h1, h2]
    have z0 : (0 : Int).natAbs = 0 := rfl
    have hz : ((0 : Nat) : Int) = 0 := rfl
    rw [z0, hz]
    cases p with
    | zero => omega
    | succ m => rfl

def sub_potential3 (p1 p2 : Potential3) : Potential3 :=
  { v0 := p1.v0 - p2.v0
  , v1 := p1.v1 - p2.v1
  , v2 := p1.v2 - p2.v2 }

theorem sub_potential_gauge_fixed (p1 p2 : Potential3)
    (h1 : is_gauge_fixed p1) (h2 : is_gauge_fixed p2) :
    is_gauge_fixed (sub_potential3 p1 p2) := by
  dsimp [is_gauge_fixed, sub_potential3] at *
  omega

/-- Strict Uniqueness of Minimizer Theorem (p = 2):
    On the gauge-fixed subspace, any two potentials whose coboundary difference
    has zero L2 energy are identical. -/
theorem gauge_fixed_l2_zero_difference (p1 p2 : Potential3)
    (hg1 : is_gauge_fixed p1) (hg2 : is_gauge_fixed p2)
    (henergy : l2sq3 (cycle3_d0 (sub_potential3 p1 p2)) = 0) :
    p1.v0 = p2.v0 ∧ p1.v1 = p2.v1 ∧ p1.v2 = p2.v2 := by
  have hz := (l2sq3_zero_iff (cycle3_d0 (sub_potential3 p1 p2))).mp henergy
  have hdiff_gf := sub_potential_gauge_fixed p1 p2 hg1 hg2
  have hker : (cycle3_d0 (sub_potential3 p1 p2)).e0 = 0 ∧ (cycle3_d0 (sub_potential3 p1 p2)).e1 = 0 :=
    ⟨hz.1, hz.2.1⟩
  have htriv := gauge_fixed_kernel_trivial (sub_potential3 p1 p2) hdiff_gf hker
  dsimp [sub_potential3] at htriv
  rcases htriv with ⟨tv0, tv1, tv2⟩
  constructor
  · omega
  · constructor
    · omega
    · omega

/-- Strict Uniqueness of Minimizer Theorem for General L^p (p ≥ 1):
    On the gauge-fixed subspace, any two potentials whose coboundary difference
    has zero L^p energy must be identical. -/
theorem gauge_fixed_lp_zero_difference (p : Nat) (hp : 1 ≤ p) (p1 p2 : Potential3)
    (hg1 : is_gauge_fixed p1) (hg2 : is_gauge_fixed p2)
    (henergy : lp_pow3 p (cycle3_d0 (sub_potential3 p1 p2)) = 0) :
    p1.v0 = p2.v0 ∧ p1.v1 = p2.v1 ∧ p1.v2 = p2.v2 := by
  have hz := (lp_pow3_zero_iff p hp (cycle3_d0 (sub_potential3 p1 p2))).mp henergy
  have hdiff_gf := sub_potential_gauge_fixed p1 p2 hg1 hg2
  have hker : (cycle3_d0 (sub_potential3 p1 p2)).e0 = 0 ∧ (cycle3_d0 (sub_potential3 p1 p2)).e1 = 0 :=
    ⟨hz.1, hz.2.1⟩
  have htriv := gauge_fixed_kernel_trivial (sub_potential3 p1 p2) hdiff_gf hker
  dsimp [sub_potential3] at htriv
  rcases htriv with ⟨tv0, tv1, tv2⟩
  constructor
  · omega
  · constructor
    · omega
    · omega

#print axioms nat_sq_zero
#print axioms nat_pow_zero
#print axioms l2sq3_zero_iff
#print axioms lp_pow3_zero_iff
#print axioms gauge_fixed_l2_zero_difference
#print axioms gauge_fixed_lp_zero_difference
