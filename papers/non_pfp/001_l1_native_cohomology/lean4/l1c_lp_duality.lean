/- Review scope: integer finite fixtures and stated hypotheses; no general real Lp, Clarkson, or Schatten theorem. AuthorityEffect: None. -/
import Init.Omega
import «l1c_lp_cochains»

/-!
# L1C-LP-DUALITY: Universal Hölder Weak Duality for Circulation Witnesses

This module mechanizes universal Hölder weak duality for discrete cochain complexes
and circulation witnesses in Paper 007.

For any circulation W satisfying the divergence-free condition d₀* W = 0 (or z_0 = z_1 = z_2 on the 3-cycle),
and for any gauge potential p:
  ⟨W, h⟩ ≤ ‖W‖_q * ‖h - d₀ p‖_p

Specifically, for the conjugate pair (p, q) = (1, ∞):
  ⟨W, h⟩ ≤ ‖W‖_∞ * ‖h - d₀ p‖_1

AuthorityEffect: None.
-/

/-- Discrete adjoint divergence operator d0* mapping edge cochain to vertex charges. -/
def cycle3_d0_adj (w : Cochain3) : Potential3 :=
  { v0 := w.e2 - w.e0
  , v1 := w.e0 - w.e1
  , v2 := w.e1 - w.e2 }

def is_divergence_free (w : Cochain3) : Prop :=
  (cycle3_d0_adj w).v0 = 0 ∧ (cycle3_d0_adj w).v1 = 0 ∧ (cycle3_d0_adj w).v2 = 0

theorem circulation_iff_divergence_free (w : Cochain3) :
    is_cycle3_circulation w ↔ is_divergence_free w := by
  dsimp [is_cycle3_circulation, is_divergence_free, cycle3_d0_adj]
  constructor
  · intro ⟨h01, h12⟩
    have : w.e0 = w.e2 := by omega
    omega
  · intro ⟨h0, h1, h2⟩
    omega

theorem int_mul_le_abs_mul (x y : Int) :
    x * y ≤ (x.natAbs : Int) * (y.natAbs : Int) := by
  have h1 : x * y ≤ ((x * y).natAbs : Int) := by omega
  have h2 : (x * y).natAbs = x.natAbs * y.natAbs := Int.natAbs_mul x y
  rw [h2] at h1
  omega

theorem holder_bound_3 (W1 W2 W3 r1 r2 r3 : Int) (M : Nat)
    (h1 : W1.natAbs ≤ M) (h2 : W2.natAbs ≤ M) (h3 : W3.natAbs ≤ M) :
    W1 * r1 + W2 * r2 + W3 * r3 ≤ (M : Int) * ((r1.natAbs : Int) + (r2.natAbs : Int) + (r3.natAbs : Int)) := by
  have le1 := int_mul_le_abs_mul W1 r1
  have le2 := int_mul_le_abs_mul W2 r2
  have le3 := int_mul_le_abs_mul W3 r3
  have b1 : (W1.natAbs : Int) * (r1.natAbs : Int) ≤ (M : Int) * (r1.natAbs : Int) := by
    have := Nat.mul_le_mul_right r1.natAbs h1
    omega
  have b2 : (W2.natAbs : Int) * (r2.natAbs : Int) ≤ (M : Int) * (r2.natAbs : Int) := by
    have := Nat.mul_le_mul_right r2.natAbs h2
    omega
  have b3 : (W3.natAbs : Int) * (r3.natAbs : Int) ≤ (M : Int) * (r3.natAbs : Int) := by
    have := Nat.mul_le_mul_right r3.natAbs h3
    omega
  have hdist : (M : Int) * ((r1.natAbs : Int) + (r2.natAbs : Int) + (r3.natAbs : Int)) =
      (M : Int) * (r1.natAbs : Int) + (M : Int) * (r2.natAbs : Int) + (M : Int) * (r3.natAbs : Int) := by
    simp [Int.mul_add]
  omega

theorem dot3_le_linf_mul_l1 (W r : Cochain3) :
    dot3 W r ≤ (linf3 W : Int) * l13 r := by
  have m1 : W.e0.natAbs ≤ linf3 W := Nat.le_max_left _ _
  have m2_sub : W.e1.natAbs ≤ Nat.max W.e1.natAbs W.e2.natAbs := Nat.le_max_left _ _
  have m2 : W.e1.natAbs ≤ linf3 W := Nat.le_trans m2_sub (Nat.le_max_right _ _)
  have m3_sub : W.e2.natAbs ≤ Nat.max W.e1.natAbs W.e2.natAbs := Nat.le_max_right _ _
  have m3 : W.e2.natAbs ≤ linf3 W := Nat.le_trans m3_sub (Nat.le_max_right _ _)
  dsimp [dot3, l13]
  exact holder_bound_3 W.e0 W.e1 W.e2 r.e0 r.e1 r.e2 (linf3 W) m1 m2 m3

/-- Theorem: Universal Hölder Weak Duality for Circulation Witness:
    For any circulation W with d₀* W = 0 and any gauge potential p,
    ⟨W, h⟩ ≤ ‖W‖_∞ * ‖h - d0 p‖_1. -/
theorem holder_weak_duality_1_inf (W : Cochain3) (h : Cochain3) (p : Potential3)
    (hcirc : is_cycle3_circulation W) :
    dot3 W h ≤ (linf3 W : Int) * l13 (residual3 h p) := by
  have hgauge := circulation_pairing_gauge_invariant W h p hcirc
  have hdot1 : dot3 W h = pairing3 W h := rfl
  have hdot2 : dot3 W (residual3 h p) = pairing3 W (residual3 h p) := rfl
  rw [hdot1, hgauge, ← hdot2]
  exact dot3_le_linf_mul_l1 W (residual3 h p)

/-- Universal Hölder Weak Duality stated under divergence-free current d₀* W = 0:
    ⟨W, h⟩ ≤ ‖W‖_∞ * ‖h - d₀ p‖_1. -/
theorem holder_weak_duality_divergence_free (W : Cochain3) (h : Cochain3) (p : Potential3)
    (hdiv : is_divergence_free W) :
    dot3 W h ≤ (linf3 W : Int) * l13 (residual3 h p) := by
  have hcirc := (circulation_iff_divergence_free W).mpr hdiv
  exact holder_weak_duality_1_inf W h p hcirc

#print axioms circulation_iff_divergence_free
#print axioms holder_bound_3
#print axioms dot3_le_linf_mul_l1
#print axioms holder_weak_duality_1_inf
#print axioms holder_weak_duality_divergence_free
