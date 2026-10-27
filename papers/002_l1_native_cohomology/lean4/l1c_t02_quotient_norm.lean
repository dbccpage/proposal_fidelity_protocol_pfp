import «l1c_t03_weak_duality»

/-!
# Theorem L1C-T2: Quotient Norm Axioms and Strict Positivity Boundary

In L1-native cohomology, the functional Φ₁([ω]) satisfies:
1. Non-negativity: ‖c‖_{1, w} ≥ 0 for all cochains c.
2. Subadditivity (Triangle Inequality): ‖c₁ + c₂‖_{1, w} ≤ ‖c₁‖_{1, w} + ‖c₂‖_{1, w}.
3. Quotient subadditivity: for any representatives ω₁ + d₀ p₁ and ω₂ + d₀ p₂,
   their sum is represented by (ω₁ + ω₂) + d₀ (p₁ + p₂), satisfying:
     ‖(ω₁ + ω₂) + d₀ (p₁ + p₂)‖_{1, w} ≤ ‖ω₁ + d₀ p₁‖_{1, w} + ‖ω₂ + d₀ p₂‖_{1, w}.
4. Positive Definiteness: if every weight w_e > 0, then ‖c‖_{1, w} = 0 implies c = 0.
5. Strict Positivity Necessity (Zero-Weight Refusal):
   if a zero weight w_e = 0 is permitted, positive definiteness fails;
   a nonzero cochain can have zero weighted L1 norm.

AuthorityEffect: None.
-/

/-- Addition of cochains. -/
def add_cochain3 (c1 c2 : Cochain3) : Cochain3 :=
  { e0 := c1.e0 + c2.e0
  , e1 := c1.e1 + c2.e1
  , e2 := c1.e2 + c2.e2 }

/-- Addition of potentials. -/
def add_potential3 (p1 p2 : Potential3) : Potential3 :=
  { v0 := p1.v0 + p2.v0
  , v1 := p1.v1 + p2.v1
  , v2 := p1.v2 + p2.v2 }

/-- Lemma: Structural equality for Cochain3. -/
theorem cochain3_ext (a b : Cochain3) (h0 : a.e0 = b.e0) (h1 : a.e1 = b.e1) (h2 : a.e2 = b.e2) : a = b := by
  cases a
  cases b
  simp only at h0 h1 h2
  rw [h0, h1, h2]

/-- Coboundary is additive: d₀ (p₁ + p₂) = d₀ p₁ + d₀ p₂. -/
theorem cycle3_d0_add (p1 p2 : Potential3) :
    cycle3_d0 (add_potential3 p1 p2) = add_cochain3 (cycle3_d0 p1) (cycle3_d0 p2) := by
  apply cochain3_ext
  · simp [cycle3_d0, add_potential3, add_cochain3]; omega
  · simp [cycle3_d0, add_potential3, add_cochain3]; omega
  · simp [cycle3_d0, add_potential3, add_cochain3]; omega

/-- Residual is additive: (ω₁ + ω₂) + d₀ (p₁ + p₂) = (ω₁ + d₀ p₁) + (ω₂ + d₀ p₂). -/
theorem residual3_add (omega1 omega2 : Cochain3) (p1 p2 : Potential3) :
    residual3 (add_cochain3 omega1 omega2) (add_potential3 p1 p2) =
    add_cochain3 (residual3 omega1 p1) (residual3 omega2 p2) := by
  apply cochain3_ext
  · simp [residual3, add_cochain3, add_potential3]; omega
  · simp [residual3, add_cochain3, add_potential3]; omega
  · simp [residual3, add_cochain3, add_potential3]; omega

/-- Pure Nat weighted L1 norm. -/
def l1_norm3_nat (w : Weights3) (c : Cochain3) : Nat :=
  w.w0 * c.e0.natAbs + w.w1 * c.e1.natAbs + w.w2 * c.e2.natAbs

/-- Lemma: Nat norm casts to Int norm. -/
theorem l1_norm3_eq_cast (w : Weights3) (c : Cochain3) :
    l1_norm3 w c = (l1_norm3_nat w c : Int) := by
  dsimp [l1_norm3, l1_norm3_nat]

/-- Non-negativity: ‖c‖_{1, w} ≥ 0. -/
theorem l1_norm3_nonneg (w : Weights3) (c : Cochain3) :
    0 ≤ l1_norm3 w c := by
  rw [l1_norm3_eq_cast]
  omega

/-- Triangle inequality in pure Nat. -/
theorem l1_norm3_nat_triangle (w : Weights3) (c1 c2 : Cochain3) :
    l1_norm3_nat w (add_cochain3 c1 c2) ≤ l1_norm3_nat w c1 + l1_norm3_nat w c2 := by
  dsimp [l1_norm3_nat, add_cochain3]
  have h0 : (c1.e0 + c2.e0).natAbs ≤ c1.e0.natAbs + c2.e0.natAbs := Int.natAbs_add_le c1.e0 c2.e0
  have h1 : (c1.e1 + c2.e1).natAbs ≤ c1.e1.natAbs + c2.e1.natAbs := Int.natAbs_add_le c1.e1 c2.e1
  have h2 : (c1.e2 + c2.e2).natAbs ≤ c1.e2.natAbs + c2.e2.natAbs := Int.natAbs_add_le c1.e2 c2.e2
  have m0 : w.w0 * (c1.e0 + c2.e0).natAbs ≤ w.w0 * c1.e0.natAbs + w.w0 * c2.e0.natAbs := by
    have := Nat.mul_le_mul_left w.w0 h0
    rw [Nat.mul_add] at this
    exact this
  have m1 : w.w1 * (c1.e1 + c2.e1).natAbs ≤ w.w1 * c1.e1.natAbs + w.w1 * c2.e1.natAbs := by
    have := Nat.mul_le_mul_left w.w1 h1
    rw [Nat.mul_add] at this
    exact this
  have m2 : w.w2 * (c1.e2 + c2.e2).natAbs ≤ w.w2 * c1.e2.natAbs + w.w2 * c2.e2.natAbs := by
    have := Nat.mul_le_mul_left w.w2 h2
    rw [Nat.mul_add] at this
    exact this
  omega

/-- Triangle inequality for weighted L1 norm. -/
theorem l1_norm3_triangle (w : Weights3) (c1 c2 : Cochain3) :
    l1_norm3 w (add_cochain3 c1 c2) ≤ l1_norm3 w c1 + l1_norm3 w c2 := by
  rw [l1_norm3_eq_cast, l1_norm3_eq_cast, l1_norm3_eq_cast]
  have hnat := l1_norm3_nat_triangle w c1 c2
  omega

/-- Quotient subadditivity theorem. -/
theorem l1_quotient_subadditive (w : Weights3) (omega1 omega2 : Cochain3) (p1 p2 : Potential3) :
    l1_norm3 w (residual3 (add_cochain3 omega1 omega2) (add_potential3 p1 p2)) ≤
    l1_norm3 w (residual3 omega1 p1) + l1_norm3 w (residual3 omega2 p2) := by
  rw [residual3_add]
  exact l1_norm3_triangle w (residual3 omega1 p1) (residual3 omega2 p2)

/-- Positive definiteness: strictly positive weights force zero cochain if norm is zero. -/
theorem l1_norm3_positive_definite (w : Weights3) (c : Cochain3)
    (hw0 : 0 < w.w0) (hw1 : 0 < w.w1) (hw2 : 0 < w.w2)
    (hnorm : l1_norm3 w c = 0) :
    c.e0 = 0 ∧ c.e1 = 0 ∧ c.e2 = 0 := by
  have hcast : l1_norm3_nat w c = 0 := by
    rw [l1_norm3_eq_cast] at hnorm
    omega
  dsimp [l1_norm3_nat] at hcast
  have hz0 : w.w0 * c.e0.natAbs = 0 := by omega
  have hz1 : w.w1 * c.e1.natAbs = 0 := by omega
  have hz2 : w.w2 * c.e2.natAbs = 0 := by omega
  have a0 : c.e0.natAbs = 0 := by
    cases hc : c.e0.natAbs
    · rfl
    · rename_i n
      rw [hc] at hz0
      have hpos : 0 < w.w0 * (n + 1) := Nat.mul_pos hw0 (Nat.succ_pos n)
      have hne : w.w0 * (n + 1) ≠ 0 := Nat.ne_of_gt hpos
      exact False.elim (hne hz0)
  have a1 : c.e1.natAbs = 0 := by
    cases hc : c.e1.natAbs
    · rfl
    · rename_i n
      rw [hc] at hz1
      have hpos : 0 < w.w1 * (n + 1) := Nat.mul_pos hw1 (Nat.succ_pos n)
      have hne : w.w1 * (n + 1) ≠ 0 := Nat.ne_of_gt hpos
      exact False.elim (hne hz1)
  have a2 : c.e2.natAbs = 0 := by
    cases hc : c.e2.natAbs
    · rfl
    · rename_i n
      rw [hc] at hz2
      have hpos : 0 < w.w2 * (n + 1) := Nat.mul_pos hw2 (Nat.succ_pos n)
      have hne : w.w2 * (n + 1) ≠ 0 := Nat.ne_of_gt hpos
      exact False.elim (hne hz2)
  have e0 : c.e0 = 0 := by omega
  have e1 : c.e1 = 0 := by omega
  have e2 : c.e2 = 0 := by omega
  exact ⟨e0, e1, e2⟩

/-- Zero-Weight Refusal Counterexample:
    Permitting a zero weight w₀ = 0 allows a nonzero cochain to have norm zero,
    violating positive definiteness. -/
theorem zero_weight_refusal_counterexample :
    let w_bad : Weights3 := { w0 := 0, w1 := 1, w2 := 1 }
    let c_nonzero : Cochain3 := { e0 := 10, e1 := 0, e2 := 0 }
    (c_nonzero.e0 ≠ 0) ∧ (l1_norm3 w_bad c_nonzero = 0) := by
  intro w_bad c_nonzero
  constructor
  · decide
  · rfl

#print axioms cochain3_ext
#print axioms cycle3_d0_add
#print axioms residual3_add
#print axioms l1_norm3_nonneg
#print axioms l1_norm3_nat_triangle
#print axioms l1_norm3_triangle
#print axioms l1_quotient_subadditive
#print axioms l1_norm3_positive_definite
#print axioms zero_weight_refusal_counterexample
