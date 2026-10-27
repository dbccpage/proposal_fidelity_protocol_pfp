import Init.Omega

/-!
# Theorem L1C-T3: Weak LP Duality and Circulation Certificate Lower Bound

In L1-native cohomology, for any edge cochain ω, any gauge potential f,
and any dual circulation z satisfying the capacity bounds |z_e| ≤ w_e:
  ⟨z, ω⟩ ≤ ‖ω + d₀ f‖_{1, w}.

Physical interpretation:
- z is a capacity-bounded divergence-free current / circulation.
- ⟨z, ω⟩ measures the conserved circulation flux pairing with the defect cochain.
- The theorem establishes that every feasible circulation z provides a rigorous,
  checkable lower bound on the L1 quotient norm Φ₁([ω]).

AuthorityEffect: None.
-/

/-- Helper lemma: Integer product bounded by weight times absolute value. -/
theorem int_mul_le_weight_abs (z r : Int) (w : Nat) (hz : z.natAbs ≤ w) :
    z * r ≤ (w : Int) * (r.natAbs : Int) := by
  have h1 : z * r ≤ ((z * r).natAbs : Int) := by omega
  have h2 : (z * r).natAbs = z.natAbs * r.natAbs := Int.natAbs_mul z r
  have h3 : z.natAbs * r.natAbs ≤ w * r.natAbs := Nat.mul_le_mul_right r.natAbs hz
  have h4 : ((z.natAbs * r.natAbs : Nat) : Int) ≤ ((w * r.natAbs : Nat) : Int) := by omega
  rw [h2] at h1
  omega

/-- 3-edge directed graph cochains. -/
structure Cochain3 where
  e0 : Int
  e1 : Int
  e2 : Int

/-- 3-vertex potential. -/
structure Potential3 where
  v0 : Int
  v1 : Int
  v2 : Int

/-- Strictly positive integer edge weights. -/
structure Weights3 where
  w0 : Nat
  w1 : Nat
  w2 : Nat

/-- Weighted L1 norm of a 3-edge cochain. -/
def l1_norm3 (w : Weights3) (c : Cochain3) : Int :=
  (w.w0 : Int) * (c.e0.natAbs : Int)
    + (w.w1 : Int) * (c.e1.natAbs : Int)
    + (w.w2 : Int) * (c.e2.natAbs : Int)

/-- Incidence coboundary on a 3-cycle:
    e0: v0 -> v1, e1: v1 -> v2, e2: v2 -> v0. -/
def cycle3_d0 (p : Potential3) : Cochain3 :=
  { e0 := p.v1 - p.v0
  , e1 := p.v2 - p.v1
  , e2 := p.v0 - p.v2 }

/-- Residual cochain r = ω + d₀ p. -/
def residual3 (omega : Cochain3) (p : Potential3) : Cochain3 :=
  { e0 := omega.e0 + (p.v1 - p.v0)
  , e1 := omega.e1 + (p.v2 - p.v1)
  , e2 := omega.e2 + (p.v0 - p.v2) }

/-- Inner product / pairing ⟨z, c⟩ = z₀ c₀ + z₁ c₁ + z₂ c₂. -/
def pairing3 (z : Cochain3) (c : Cochain3) : Int :=
  z.e0 * c.e0 + z.e1 * c.e1 + z.e2 * c.e2

/-- A circulation on the 3-cycle satisfies constant flux z₀ = z₁ = z₂. -/
def is_cycle3_circulation (z : Cochain3) : Prop :=
  z.e0 = z.e1 ∧ z.e1 = z.e2

/-- Helper: Ring distribution for circulation potential cancellation. -/
theorem cycle3_potential_sum_zero (z : Int) (p : Potential3) :
    z * (p.v1 - p.v0) + z * (p.v2 - p.v1) + z * (p.v0 - p.v2) = 0 := by
  have hzero : (p.v1 - p.v0) + (p.v2 - p.v1) + (p.v0 - p.v2) = 0 := by omega
  have hdistrib : z * (p.v1 - p.v0) + z * (p.v2 - p.v1) + z * (p.v0 - p.v2)
                = z * ((p.v1 - p.v0) + (p.v2 - p.v1) + (p.v0 - p.v2)) := by
    simp [Int.mul_add]
  rw [hdistrib, hzero, Int.mul_zero]

/-- Circulation annihilates any coboundary: ⟨z, d₀ p⟩ = 0. -/
theorem circulation_annihilates_coboundary (z : Cochain3) (p : Potential3)
    (hz : is_cycle3_circulation z) :
    pairing3 z (cycle3_d0 p) = 0 := by
  rcases hz with ⟨h01, h12⟩
  simp [pairing3, cycle3_d0]
  rw [h01, h12]
  exact cycle3_potential_sum_zero z.e2 p

/-- Gauge invariance of circulation pairing: ⟨z, ω⟩ = ⟨z, ω + d₀ p⟩. -/
theorem circulation_pairing_gauge_invariant (z : Cochain3) (omega : Cochain3) (p : Potential3)
    (hz : is_cycle3_circulation z) :
    pairing3 z omega = pairing3 z (residual3 omega p) := by
  rcases hz with ⟨h01, h12⟩
  simp [pairing3, residual3]
  rw [h01, h12]
  have h1 : z.e2 * (omega.e0 + (p.v1 - p.v0)) = z.e2 * omega.e0 + z.e2 * (p.v1 - p.v0) :=
    Int.mul_add z.e2 omega.e0 (p.v1 - p.v0)
  have h2 : z.e2 * (omega.e1 + (p.v2 - p.v1)) = z.e2 * omega.e1 + z.e2 * (p.v2 - p.v1) :=
    Int.mul_add z.e2 omega.e1 (p.v2 - p.v1)
  have h3 : z.e2 * (omega.e2 + (p.v0 - p.v2)) = z.e2 * omega.e2 + z.e2 * (p.v0 - p.v2) :=
    Int.mul_add z.e2 omega.e2 (p.v0 - p.v2)
  have hnull : z.e2 * (p.v1 - p.v0) + z.e2 * (p.v2 - p.v1) + z.e2 * (p.v0 - p.v2) = 0 :=
    cycle3_potential_sum_zero z.e2 p
  rw [h1, h2, h3]
  omega

/-- Capacity bound: |z_e| ≤ w_e for all edges. -/
def satisfies_capacity_bound (z : Cochain3) (w : Weights3) : Prop :=
  z.e0.natAbs ≤ w.w0 ∧ z.e1.natAbs ≤ w.w1 ∧ z.e2.natAbs ≤ w.w2

/-- Theorem L1C-T3 (Weak LP Duality for L1-Native Cohomology):
    For any cochain ω, potential p, and circulation z satisfying capacity bounds w,
    the circulation pairing is a lower bound for the weighted L1 residual:
      ⟨z, ω⟩ ≤ ‖ω + d₀ p‖_{1, w}. -/
theorem l1c_t03_weak_duality (omega : Cochain3) (p : Potential3) (z : Cochain3) (w : Weights3)
    (hcirc : is_cycle3_circulation z)
    (hcap : satisfies_capacity_bound z w) :
    pairing3 z omega ≤ l1_norm3 w (residual3 omega p) := by
  have hgauge : pairing3 z omega = pairing3 z (residual3 omega p) :=
    circulation_pairing_gauge_invariant z omega p hcirc
  rw [hgauge]
  simp [pairing3, l1_norm3, residual3]
  rcases hcap with ⟨hc0, hc1, hc2⟩
  have le0 := int_mul_le_weight_abs z.e0 (omega.e0 + (p.v1 - p.v0)) w.w0 hc0
  have le1 := int_mul_le_weight_abs z.e1 (omega.e1 + (p.v2 - p.v1)) w.w1 hc1
  have le2 := int_mul_le_weight_abs z.e2 (omega.e2 + (p.v0 - p.v2)) w.w2 hc2
  omega

#print axioms int_mul_le_weight_abs
#print axioms cycle3_potential_sum_zero
#print axioms circulation_annihilates_coboundary
#print axioms circulation_pairing_gauge_invariant
#print axioms l1c_t03_weak_duality
