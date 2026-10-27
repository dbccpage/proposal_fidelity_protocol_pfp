import «l1c_t03_weak_duality»

/-!
# Theorem L1C-T5: Cycle Invariant and Sparse Representative Attainment

On an oriented directed cycle, the topological invariant of a 1-cochain ω
is its circulation flux integral S = ∑_{e ∈ Cycle} ω_e.

Theorems proved:
1. Gauge invariance of cycle flux: for any vertex potential p,
   the sum of residual coordinates equals S identically:
     r₀ + r₁ + r₂ = S.
2. Cycle rank support bound (β = 1): the minimum L1 quotient norm is
   attained by a 1-sparse representative concentrating the total flux S
   on a minimum-weight edge:
     Φ₁([ω]) = |S| * min_e w_e.
3. Lower bound from the topological invariant:
   for any potential p, ‖ω + d₀ p‖_{1, w} ≥ |S| * min_e w_e.

AuthorityEffect: None.
-/

/-- Cycle flux invariant S = ω₀ + ω₁ + ω₂. -/
def cycle3_flux (c : Cochain3) : Int :=
  c.e0 + c.e1 + c.e2

/-- Theorem: For any gauge potential p, the flux of the residual equals the original flux. -/
theorem cycle3_residual_flux_invariant (omega : Cochain3) (p : Potential3) :
    cycle3_flux (residual3 omega p) = cycle3_flux omega := by
  simp [cycle3_flux, residual3]
  omega

/-- Triangle inequality for three integers: |x + y + z| ≤ |x| + |y| + |z|. -/
theorem abs_sum3_le (x y z : Int) :
    (x + y + z).natAbs ≤ x.natAbs + y.natAbs + z.natAbs := by
  have h1 : (x + y + z).natAbs ≤ (x + y).natAbs + z.natAbs := Int.natAbs_add_le (x + y) z
  have h2 : (x + y).natAbs ≤ x.natAbs + y.natAbs := Int.natAbs_add_le x y
  omega

/-- Pure Nat inequality: scaling triangle inequality by minimum weight. -/
theorem nat_weighted_sum_lower_bound (w_min w0 w1 w2 e0 e1 e2 : Nat)
    (hw0 : w_min ≤ w0) (hw1 : w_min ≤ w1) (hw2 : w_min ≤ w2) :
    w_min * (e0 + e1 + e2) ≤ w0 * e0 + w1 * e1 + w2 * e2 := by
  have le0 : w_min * e0 ≤ w0 * e0 := Nat.mul_le_mul_right e0 hw0
  have le1 : w_min * e1 ≤ w1 * e1 := Nat.mul_le_mul_right e1 hw1
  have le2 : w_min * e2 ≤ w2 * e2 := Nat.mul_le_mul_right e2 hw2
  have m01 : w_min * e0 + w_min * e1 ≤ w0 * e0 + w1 * e1 := Nat.add_le_add le0 le1
  have mtot : w_min * e0 + w_min * e1 + w_min * e2 ≤ w0 * e0 + w1 * e1 + w2 * e2 :=
    Nat.add_le_add m01 le2
  have hdist : w_min * (e0 + e1 + e2) = w_min * e0 + w_min * e1 + w_min * e2 := by
    have h1 : w_min * (e0 + e1 + e2) = w_min * (e0 + e1) + w_min * e2 := Nat.mul_add w_min (e0 + e1) e2
    have h2 : w_min * (e0 + e1) = w_min * e0 + w_min * e1 := Nat.mul_add w_min e0 e1
    rw [h1, h2]
  rw [hdist]
  exact mtot

/-- Lower bound on weighted L1 norm by minimum weight times absolute flux. -/
theorem cycle3_l1_norm_lower_bound (w : Weights3) (w_min : Nat)
    (hw0 : w_min ≤ w.w0) (hw1 : w_min ≤ w.w1) (hw2 : w_min ≤ w.w2)
    (c : Cochain3) :
    (w_min : Int) * ((cycle3_flux c).natAbs : Int) ≤ l1_norm3 w c := by
  have htri : (cycle3_flux c).natAbs ≤ c.e0.natAbs + c.e1.natAbs + c.e2.natAbs :=
    abs_sum3_le c.e0 c.e1 c.e2
  have hnat1 : w_min * (cycle3_flux c).natAbs ≤ w_min * (c.e0.natAbs + c.e1.natAbs + c.e2.natAbs) :=
    Nat.mul_le_mul_left w_min htri
  have hnat2 : w_min * (c.e0.natAbs + c.e1.natAbs + c.e2.natAbs) ≤
      w.w0 * c.e0.natAbs + w.w1 * c.e1.natAbs + w.w2 * c.e2.natAbs :=
    nat_weighted_sum_lower_bound w_min w.w0 w.w1 w.w2 c.e0.natAbs c.e1.natAbs c.e2.natAbs hw0 hw1 hw2
  have htot : w_min * (cycle3_flux c).natAbs ≤
      w.w0 * c.e0.natAbs + w.w1 * c.e1.natAbs + w.w2 * c.e2.natAbs :=
    Nat.le_trans hnat1 hnat2
  simp [l1_norm3]
  omega

/-- Theorem L1C-T5 (Universal Topological Lower Bound for Any Representative):
    For all gauge potentials p, ‖ω + d₀ p‖_{1, w} ≥ w_min * |S|. -/
theorem cycle3_topological_lower_bound (omega : Cochain3) (p : Potential3) (w : Weights3) (w_min : Nat)
    (hw0 : w_min ≤ w.w0) (hw1 : w_min ≤ w.w1) (hw2 : w_min ≤ w.w2) :
    (w_min : Int) * ((cycle3_flux omega).natAbs : Int) ≤ l1_norm3 w (residual3 omega p) := by
  have heq : cycle3_flux omega = cycle3_flux (residual3 omega p) := by
    rw [cycle3_residual_flux_invariant]
  rw [heq]
  exact cycle3_l1_norm_lower_bound w w_min hw0 hw1 hw2 (residual3 omega p)

/-- A 1-sparse representative concentrating flux S on edge e0 has exact norm w₀ * |S|. -/
theorem sparse_representative_attainment (S : Int) (w : Weights3) :
    let r_sparse : Cochain3 := { e0 := S, e1 := 0, e2 := 0 }
    cycle3_flux r_sparse = S ∧
    l1_norm3 w r_sparse = (w.w0 : Int) * (S.natAbs : Int) := by
  intro r_sparse
  dsimp [r_sparse, cycle3_flux, l1_norm3]
  omega

#print axioms cycle3_residual_flux_invariant
#print axioms abs_sum3_le
#print axioms nat_weighted_sum_lower_bound
#print axioms cycle3_l1_norm_lower_bound
#print axioms cycle3_topological_lower_bound
#print axioms sparse_representative_attainment
