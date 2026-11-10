-- Vendored for Paper 008 from `lean4/ExactRat/Basic.lean` at commit 52cb5457f6c485ba548cfd292f6012a941ed22cf
-- (git blob 62115b19b2c399b8d480e18a4c7fd31ee47dbf12). Every line after this two-line header is byte-identical to that blob.
/-!
# Exact rationals as numerator/denominator pairs

A fraction is an integer numerator over a positive natural denominator. Two
fractions name the same number exactly when cross-multiplication agrees.
`QN` is the quotient of fractions by that relation, so equality on `QN` is
equality of numbers, and every law below is an equation between numbers.

Core Lean only. The ring normalisation used in the proofs expands products
with distributivity and closes the goal by associativity and commutativity
(`ac_rfl`); linear steps use `omega`. Every reported declaration depends on
at most `propext` and `Quot.sound`.

AuthorityEffect: None
-/

namespace ExactRat

/-- An integer numerator over a positive natural denominator. -/
structure Frac where
  num : Int
  den : Nat
  den_pos : 0 < den

namespace Frac

/-- Cross-multiplication. -/
def Eqv (a b : Frac) : Prop := a.num * (b.den : Int) = b.num * (a.den : Int)

instance (a b : Frac) : Decidable (Eqv a b) := inferInstanceAs (Decidable (_ = _))

theorem den_ne (a : Frac) : (a.den : Int) ≠ 0 := by
  have := a.den_pos
  omega

theorem den_pos' (a : Frac) : (0 : Int) < (a.den : Int) := Int.natCast_pos.mpr a.den_pos

theorem eqv_refl (a : Frac) : Eqv a a := rfl

theorem eqv_symm {a b : Frac} (h : Eqv a b) : Eqv b a := h.symm

theorem eqv_trans {a b c : Frac} (h1 : Eqv a b) (h2 : Eqv b c) : Eqv a c := by
  unfold Eqv at *
  apply (Int.mul_eq_mul_right_iff (den_ne b)).mp
  calc a.num * (c.den : Int) * (b.den : Int)
        = (a.num * (b.den : Int)) * (c.den : Int) := by ac_rfl
    _ = (b.num * (a.den : Int)) * (c.den : Int) := by rw [h1]
    _ = (b.num * (c.den : Int)) * (a.den : Int) := by ac_rfl
    _ = (c.num * (b.den : Int)) * (a.den : Int) := by rw [h2]
    _ = c.num * (a.den : Int) * (b.den : Int) := by ac_rfl

instance setoid : Setoid Frac := ⟨Eqv, ⟨eqv_refl, eqv_symm, eqv_trans⟩⟩

def zero : Frac := ⟨0, 1, Nat.one_pos⟩
def one : Frac := ⟨1, 1, Nat.one_pos⟩

def add (a b : Frac) : Frac :=
  ⟨a.num * b.den + b.num * a.den, a.den * b.den, Nat.mul_pos a.den_pos b.den_pos⟩

def neg (a : Frac) : Frac := ⟨-a.num, a.den, a.den_pos⟩

def mul (a b : Frac) : Frac :=
  ⟨a.num * b.num, a.den * b.den, Nat.mul_pos a.den_pos b.den_pos⟩

/-- The reciprocal of a numerator over a denominator; zero goes to zero. -/
def invPair (n : Int) (d : Nat) : Frac :=
  if h : 0 < n then ⟨d, n.toNat, by omega⟩
  else if h' : n < 0 then ⟨-(d : Int), (-n).toNat, by omega⟩
  else zero

def inv (a : Frac) : Frac := invPair a.num a.den

/-- A positive number: its numerator is positive (its denominator always is). -/
def Pos (a : Frac) : Prop := 0 < a.num

instance (a : Frac) : Decidable (Pos a) := inferInstanceAs (Decidable (_ < _))

theorem add_respects {a a' b b' : Frac} (ha : Eqv a a') (hb : Eqv b b') :
    Eqv (add a b) (add a' b') := by
  simp only [Eqv, add, Int.natCast_mul] at *
  calc (a.num * (b.den : Int) + b.num * (a.den : Int)) * ((a'.den : Int) * (b'.den : Int))
        = (a.num * (a'.den : Int)) * ((b.den : Int) * (b'.den : Int))
          + (b.num * (b'.den : Int)) * ((a.den : Int) * (a'.den : Int)) := by
          simp only [Int.add_mul]; ac_rfl
    _ = (a'.num * (a.den : Int)) * ((b.den : Int) * (b'.den : Int))
          + (b'.num * (b.den : Int)) * ((a.den : Int) * (a'.den : Int)) := by rw [ha, hb]
    _ = (a'.num * (b'.den : Int) + b'.num * (a'.den : Int)) * ((a.den : Int) * (b.den : Int)) := by
          simp only [Int.add_mul]; ac_rfl

theorem neg_respects {a a' : Frac} (ha : Eqv a a') : Eqv (neg a) (neg a') := by
  simp only [Eqv, neg] at *
  rw [Int.neg_mul, Int.neg_mul, ha]

theorem mul_respects {a a' b b' : Frac} (ha : Eqv a a') (hb : Eqv b b') :
    Eqv (mul a b) (mul a' b') := by
  simp only [Eqv, mul, Int.natCast_mul] at *
  calc a.num * b.num * ((a'.den : Int) * (b'.den : Int))
        = (a.num * (a'.den : Int)) * (b.num * (b'.den : Int)) := by ac_rfl
    _ = (a'.num * (a.den : Int)) * (b'.num * (b.den : Int)) := by rw [ha, hb]
    _ = a'.num * b'.num * ((a.den : Int) * (b.den : Int)) := by ac_rfl

theorem num_zero_of_eqv {a a' : Frac} (ha : Eqv a a') (h : a.num = 0) : a'.num = 0 := by
  unfold Eqv at ha
  rw [h, Int.zero_mul] at ha
  have := den_ne a
  rcases Int.mul_eq_zero.mp ha.symm with h' | h'
  · exact h'
  · exact absurd h' this

theorem pos_of_eqv {a a' : Frac} (ha : Eqv a a') (h : Pos a) : Pos a' := by
  unfold Pos Eqv at *
  have h1 : 0 < a.num * (a'.den : Int) := Int.mul_pos h (den_pos' a')
  rw [ha] at h1
  exact Int.pos_of_mul_pos_left h1 (den_pos' a)

theorem pos_respects {a a' : Frac} (ha : Eqv a a') : Pos a ↔ Pos a' :=
  ⟨pos_of_eqv ha, pos_of_eqv (eqv_symm ha)⟩

theorem neg_of_eqv {a a' : Frac} (ha : Eqv a a') (h : a.num < 0) : a'.num < 0 := by
  have hn : Pos (neg a) := by
    show 0 < -a.num
    omega
  have h2 : 0 < -a'.num := pos_of_eqv (neg_respects ha) hn
  omega

theorem inv_respects {a a' : Frac} (ha : Eqv a a') : Eqv (inv a) (inv a') := by
  rcases a with ⟨n, d, hd⟩
  rcases a' with ⟨n', d', hd'⟩
  have hz' : n' = 0 → n = 0 :=
    fun h => num_zero_of_eqv (a := ⟨n', d', hd'⟩) (a' := ⟨n, d, hd⟩) (eqv_symm ha) h
  have hp : 0 < n → 0 < n' := pos_of_eqv (a := ⟨n, d, hd⟩) (a' := ⟨n', d', hd'⟩) ha
  have hp' : 0 < n' → 0 < n := pos_of_eqv (a := ⟨n', d', hd'⟩) (a' := ⟨n, d, hd⟩) (eqv_symm ha)
  have hq : n < 0 → n' < 0 := neg_of_eqv (a := ⟨n, d, hd⟩) (a' := ⟨n', d', hd'⟩) ha
  have hq' : n' < 0 → n < 0 := neg_of_eqv (a := ⟨n', d', hd'⟩) (a' := ⟨n, d, hd⟩) (eqv_symm ha)
  have e : n * (d' : Int) = n' * (d : Int) := ha
  show Eqv (invPair n d) (invPair n' d')
  unfold invPair
  by_cases h1 : 0 < n
  · have h1' := hp h1
    rw [dif_pos h1, dif_pos h1']
    show (d : Int) * ((n'.toNat : Nat) : Int) = (d' : Int) * ((n.toNat : Nat) : Int)
    rw [Int.toNat_of_nonneg (by omega), Int.toNat_of_nonneg (by omega),
      Int.mul_comm (d : Int) n', Int.mul_comm (d' : Int) n]
    exact e.symm
  · by_cases h2 : n < 0
    · have h2' := hq h2
      have h1' : ¬ 0 < n' := by omega
      rw [dif_neg h1, dif_pos h2, dif_neg h1', dif_pos h2']
      show -(d : Int) * (((-n').toNat : Nat) : Int) = -(d' : Int) * (((-n).toNat : Nat) : Int)
      rw [Int.toNat_of_nonneg (by omega), Int.toNat_of_nonneg (by omega),
        Int.neg_mul, Int.neg_mul, Int.mul_neg, Int.mul_neg, Int.neg_neg, Int.neg_neg,
        Int.mul_comm (d : Int) n', Int.mul_comm (d' : Int) n]
      exact e.symm
    · have hn : n = 0 := by omega
      have h1' : ¬ 0 < n' := fun h => h1 (hp' h)
      have h2' : ¬ n' < 0 := fun h => h2 (hq' h)
      rw [dif_neg h1, dif_neg h2, dif_neg h1', dif_neg h2']
      exact eqv_refl zero

end Frac

/-- Exact rationals: fractions up to cross-multiplication. -/
abbrev QN := Quotient Frac.setoid

namespace QN

def mk (a : Frac) : QN := Quotient.mk _ a

/-- The number `n / d`; a zero denominator gives zero. -/
def ofPair (n : Int) (d : Nat) : QN := if h : 0 < d then mk ⟨n, d, h⟩ else mk Frac.zero

def ofInt (n : Int) : QN := mk ⟨n, 1, Nat.one_pos⟩

def add : QN → QN → QN :=
  Quotient.lift₂ (fun a b => mk (Frac.add a b))
    (fun _ _ _ _ ha hb => Quotient.sound (Frac.add_respects ha hb))

def neg : QN → QN :=
  Quotient.lift (fun a => mk (Frac.neg a)) (fun _ _ ha => Quotient.sound (Frac.neg_respects ha))

def mul : QN → QN → QN :=
  Quotient.lift₂ (fun a b => mk (Frac.mul a b))
    (fun _ _ _ _ ha hb => Quotient.sound (Frac.mul_respects ha hb))

def inv : QN → QN :=
  Quotient.lift (fun a => mk (Frac.inv a)) (fun _ _ ha => Quotient.sound (Frac.inv_respects ha))

/-- Positivity, as a Boolean. -/
def pos : QN → Bool :=
  Quotient.lift (fun a => decide (Frac.Pos a))
    (fun _ _ ha => decide_eq_decide.mpr (Frac.pos_respects ha))

instance : OfNat QN n := ⟨ofInt n⟩
instance : Add QN := ⟨add⟩
instance : Neg QN := ⟨neg⟩
instance : Sub QN := ⟨fun x y => add x (neg y)⟩
instance : Mul QN := ⟨mul⟩
instance : Inv QN := ⟨inv⟩
instance : Div QN := ⟨fun x y => mul x (inv y)⟩
instance : LT QN := ⟨fun x y => pos (y - x) = true⟩
instance : LE QN := ⟨fun x y => x = y ∨ x < y⟩

instance : DecidableEq QN := fun x y =>
  Quotient.recOnSubsingleton₂ x y fun a b =>
    decidable_of_iff (Frac.Eqv a b) ⟨fun h => Quotient.sound h, fun h => Quotient.exact h⟩

instance (x y : QN) : Decidable (x < y) := inferInstanceAs (Decidable (_ = _))
instance (x y : QN) : Decidable (x ≤ y) := inferInstanceAs (Decidable (_ ∨ _))

theorem sub_def (x y : QN) : x - y = x + -y := rfl
theorem div_def (x y : QN) : x / y = x * y⁻¹ := rfl
theorem lt_def (x y : QN) : x < y ↔ pos (y - x) = true := Iff.rfl

end QN

end ExactRat
