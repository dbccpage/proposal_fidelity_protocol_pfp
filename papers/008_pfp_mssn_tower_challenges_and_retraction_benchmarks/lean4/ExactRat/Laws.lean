-- Vendored for Paper 008 from `lean4/ExactRat/Laws.lean` at commit 52cb5457f6c485ba548cfd292f6012a941ed22cf
-- (git blob ff18d1a07b12901c9f79c2364e6ea984747e0061). Every line after this two-line header is byte-identical to that blob.
import ExactRat.Basic

/-!
# Field and order laws for `QN`

Every law is an equation (or an order fact) between numbers, proved by
passing to representatives and checking cross-multiplication.

Order is given by a positive cone: sums and products of positives are
positive, and every number is positive, zero, or has a positive negation,
never two of these at once. These are the ordered-field axioms.

AuthorityEffect: None
-/

namespace ExactRat
namespace QN

open Frac

/-- Two numbers are equal when their representatives cross-multiply equal. -/
theorem sound {a b : Frac} (h : Frac.Eqv a b) : mk a = mk b := Quotient.sound h

theorem exact {a b : Frac} (h : mk a = mk b) : Frac.Eqv a b := Quotient.exact h

theorem mk_eq_iff (a b : Frac) : mk a = mk b ↔ Frac.Eqv a b := ⟨exact, sound⟩

theorem zero_def : (0 : QN) = mk Frac.zero := rfl
theorem one_def : (1 : QN) = mk Frac.one := rfl

/-! ## The commutative ring laws -/

theorem add_comm (x y : QN) : x + y = y + x := by
  induction x using Quotient.ind
  induction y using Quotient.ind
  apply sound
  simp only [Frac.Eqv, Frac.add, Int.natCast_mul, Int.add_mul]
  ac_rfl

theorem add_assoc (x y z : QN) : x + y + z = x + (y + z) := by
  induction x using Quotient.ind
  induction y using Quotient.ind
  induction z using Quotient.ind
  apply sound
  simp only [Frac.Eqv, Frac.add, Int.natCast_mul, Int.add_mul]
  ac_rfl

theorem zero_add (x : QN) : 0 + x = x := by
  induction x using Quotient.ind
  apply sound
  simp only [Frac.Eqv, Frac.add, Int.natCast_mul, Int.natCast_zero, Int.natCast_one, Int.zero_mul,
    Int.zero_add, Int.mul_one, Int.one_mul]

theorem add_zero (x : QN) : x + 0 = x := by
  rw [add_comm]
  exact zero_add x

theorem neg_add_cancel (x : QN) : -x + x = 0 := by
  induction x using Quotient.ind
  apply sound
  simp only [Frac.Eqv, Frac.add, Frac.neg, Frac.zero, Int.natCast_mul, Int.neg_mul,
    Int.natCast_zero, Int.natCast_one, Int.mul_one, Int.zero_mul]
  omega

theorem add_neg_cancel (x : QN) : x + -x = 0 := by
  rw [add_comm]
  exact neg_add_cancel x

theorem sub_self (x : QN) : x - x = 0 := add_neg_cancel x

theorem neg_add (x y : QN) : -(x + y) = -x + -y := by
  induction x using Quotient.ind
  induction y using Quotient.ind
  apply sound
  simp only [Frac.Eqv, Frac.add, Frac.neg, Int.natCast_mul, Int.neg_add, Int.neg_mul, Int.add_mul]

theorem neg_zero : -(0 : QN) = 0 := by
  apply sound
  decide

theorem sub_zero (x : QN) : x - 0 = x := by
  rw [sub_def, neg_zero, add_zero]

theorem mul_comm (x y : QN) : x * y = y * x := by
  induction x using Quotient.ind
  induction y using Quotient.ind
  apply sound
  simp only [Frac.Eqv, Frac.mul, Int.natCast_mul]
  ac_rfl

theorem mul_assoc (x y z : QN) : x * y * z = x * (y * z) := by
  induction x using Quotient.ind
  induction y using Quotient.ind
  induction z using Quotient.ind
  apply sound
  simp only [Frac.Eqv, Frac.mul, Int.natCast_mul]
  ac_rfl

theorem one_mul (x : QN) : 1 * x = x := by
  induction x using Quotient.ind
  apply sound
  simp only [Frac.Eqv, Frac.mul, Frac.one, Int.natCast_mul, Int.natCast_zero, Int.natCast_one, Int.one_mul]

theorem mul_one (x : QN) : x * 1 = x := by
  rw [mul_comm]
  exact one_mul x

theorem zero_mul (x : QN) : 0 * x = 0 := by
  induction x using Quotient.ind
  apply sound
  simp only [Frac.Eqv, Frac.mul, Int.natCast_mul, Int.natCast_zero, Int.zero_mul]

theorem mul_zero (x : QN) : x * 0 = 0 := by
  rw [mul_comm]
  exact zero_mul x

theorem mul_add (x y z : QN) : x * (y + z) = x * y + x * z := by
  induction x using Quotient.ind
  induction y using Quotient.ind
  induction z using Quotient.ind
  apply sound
  simp only [Frac.Eqv, Frac.mul, Frac.add, Int.natCast_mul, Int.add_mul, Int.mul_add]
  ac_rfl

theorem add_mul (x y z : QN) : (x + y) * z = x * z + y * z := by
  rw [mul_comm, mul_add, mul_comm z x, mul_comm z y]

theorem zero_ne_one : (0 : QN) ≠ 1 := by
  intro h
  have := exact h
  simp only [Frac.Eqv, Frac.zero, Frac.one] at this
  omega

/-! ## The field law -/

theorem inv_zero : (0 : QN)⁻¹ = 0 := by
  apply sound
  exact Frac.eqv_refl _

theorem mul_inv_cancel (x : QN) (hx : x ≠ 0) : x * x⁻¹ = 1 := by
  induction x using Quotient.ind
  rename_i a
  rcases a with ⟨n, d, hd⟩
  apply sound
  show Frac.Eqv (Frac.mul ⟨n, d, hd⟩ (Frac.invPair n d)) Frac.one
  unfold Frac.invPair
  by_cases h1 : 0 < n
  · rw [dif_pos h1]
    simp only [Frac.Eqv, Frac.mul, Frac.one, Int.natCast_mul, Int.natCast_zero, Int.natCast_one, Int.mul_one,
      Int.one_mul, Int.toNat_of_nonneg (Int.le_of_lt h1)]
    exact Int.mul_comm _ _
  · by_cases h2 : n < 0
    · rw [dif_neg h1, dif_pos h2]
      simp only [Frac.Eqv, Frac.mul, Frac.one, Int.natCast_mul, Int.natCast_zero, Int.natCast_one, Int.mul_one,
        Int.one_mul, Int.toNat_of_nonneg (show 0 ≤ -n by omega), Int.mul_neg, Int.neg_mul,
        Int.neg_neg]
      rw [Int.mul_comm]
    · exfalso
      apply hx
      apply sound
      simp only [Frac.Eqv, Frac.zero, Int.zero_mul, Int.natCast_zero, Int.natCast_one, Int.mul_one]
      omega

theorem inv_mul_cancel (x : QN) (hx : x ≠ 0) : x⁻¹ * x = 1 := by
  rw [mul_comm]
  exact mul_inv_cancel x hx

theorem div_self (x : QN) (hx : x ≠ 0) : x / x = 1 := mul_inv_cancel x hx

/-! ## The order: a positive cone -/

/-- `x` is positive. -/
def Pos (x : QN) : Prop := pos x = true

instance (x : QN) : Decidable (Pos x) := inferInstanceAs (Decidable (_ = _))

theorem pos_mk (a : Frac) : Pos (mk a) ↔ 0 < a.num := by
  show decide (Frac.Pos a) = true ↔ _
  simp only [decide_eq_true_eq]
  rfl

theorem pos_add {x y : QN} (hx : Pos x) (hy : Pos y) : Pos (x + y) := by
  induction x using Quotient.ind
  induction y using Quotient.ind
  rename_i a b
  have ha := (pos_mk a).mp hx
  have hb := (pos_mk b).mp hy
  show Pos (mk (Frac.add a b))
  apply (pos_mk _).mpr
  show 0 < a.num * (b.den : Int) + b.num * (a.den : Int)
  have h1 := Int.mul_pos ha (Frac.den_pos' b)
  have h2 := Int.mul_pos hb (Frac.den_pos' a)
  omega

theorem pos_mul {x y : QN} (hx : Pos x) (hy : Pos y) : Pos (x * y) := by
  induction x using Quotient.ind
  induction y using Quotient.ind
  rename_i a b
  have ha := (pos_mk a).mp hx
  have hb := (pos_mk b).mp hy
  show Pos (mk (Frac.mul a b))
  exact (pos_mk _).mpr (Int.mul_pos ha hb)

theorem trichotomy (x : QN) : Pos x ∨ x = 0 ∨ Pos (-x) := by
  induction x using Quotient.ind
  rename_i a
  rcases Int.lt_trichotomy 0 a.num with h | h | h
  · exact Or.inl ((pos_mk a).mpr h)
  · refine Or.inr (Or.inl (sound ?_))
    simp only [Frac.Eqv, Frac.zero, Int.zero_mul, Int.natCast_zero, Int.natCast_one, Int.mul_one]
    omega
  · refine Or.inr (Or.inr ?_)
    show Pos (mk (Frac.neg a))
    apply (pos_mk _).mpr
    show 0 < -a.num
    omega

theorem not_pos_and_pos_neg (x : QN) : ¬ (Pos x ∧ Pos (-x)) := by
  induction x using Quotient.ind
  rename_i a
  intro ⟨h1, h2⟩
  have p1 := (pos_mk a).mp h1
  have p2 : 0 < -a.num := (pos_mk (Frac.neg a)).mp h2
  omega

theorem not_pos_zero : ¬ Pos (0 : QN) := by
  intro h
  have := (pos_mk Frac.zero).mp h
  simp only [Frac.zero] at this
  omega

theorem lt_iff_pos_sub (x y : QN) : x < y ↔ Pos (y - x) := Iff.rfl

theorem lt_irrefl (x : QN) : ¬ x < x := by
  rw [lt_iff_pos_sub, sub_self]
  exact not_pos_zero

theorem lt_trans {x y z : QN} (h1 : x < y) (h2 : y < z) : x < z := by
  rw [lt_iff_pos_sub] at *
  have := pos_add h2 h1
  have e : z - y + (y - x) = z - x := by
    simp only [sub_def]
    rw [add_assoc, ← add_assoc (-y) y (-x), neg_add_cancel, zero_add]
  rw [e] at this
  exact this

theorem lt_trichotomy (x y : QN) : x < y ∨ x = y ∨ y < x := by
  rcases trichotomy (y - x) with h | h | h
  · exact Or.inl h
  · refine Or.inr (Or.inl ?_)
    have e : y = y - x + x := by
      simp only [sub_def]
      rw [add_assoc, neg_add_cancel, add_zero]
    rw [e, h, zero_add]
  · refine Or.inr (Or.inr ?_)
    rw [lt_iff_pos_sub]
    have e : -(y - x) = x - y := by
      have h0 : -(y - x) + (y - x) = 0 := neg_add_cancel _
      calc -(y - x) = -(y - x) + ((y - x) + (x - y)) := by
            rw [show (y - x) + (x - y) = 0 by
              simp only [sub_def]
              rw [add_assoc, ← add_assoc (-x) x (-y), neg_add_cancel, zero_add, add_neg_cancel],
              add_zero]
        _ = (-(y - x) + (y - x)) + (x - y) := by rw [add_assoc]
        _ = x - y := by rw [h0, zero_add]
    rw [← e]
    exact h

theorem add_lt_add_right {x y : QN} (h : x < y) (z : QN) : x + z < y + z := by
  rw [lt_iff_pos_sub] at *
  have e : y + z - (x + z) = y - x := by
    rw [sub_def, sub_def, neg_add, add_assoc]
    congr 1
    rw [add_comm (-x) (-z), ← add_assoc, add_neg_cancel, zero_add]
  rw [e]
  exact h

theorem mul_pos {x y : QN} (hx : 0 < x) (hy : 0 < y) : 0 < x * y := by
  rw [lt_iff_pos_sub, sub_zero] at *
  exact pos_mul hx hy

end QN
end ExactRat
