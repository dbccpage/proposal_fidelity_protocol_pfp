import ExactRat.Basic
import ExactRat.Laws

/-!
# Polynomials over `QN`, and claims that hold for every natural from a start

A polynomial is its list of coefficients, lowest power first, evaluated by
Horner's rule. The forward difference `diff p` evaluates to
`p (x + 1) - p x` for every `x` (`eval_diff`), proved by induction on the
coefficient list.

`nonneg_from` is the claim-for-all-cases theorem, proved by induction: when
the value of `p` and of each of its forward differences up to the `d`-th is
nonnegative at the natural `n0`, and the `d`-th difference is constant, then
`p` is nonnegative at every natural `n ≥ n0`. `pos_from` is its strict form.
The hypotheses are Booleans a level's certificate module decides by
`decide` on its own data, so one generic induction covers every fixture.

`eval_reverse` substitutes a reciprocal: reading the coefficients in
reverse at `x ≠ 0` is `x ^ (length - 1)` times the value at `x⁻¹`. With it,
`halving_bound` proves a bound at every `1 / 2 ^ k` from one at the naturals.

Only `propext` and `Quot.sound` are used; no Mathlib, no `Classical.choice`.

AuthorityEffect: None
-/

namespace ExactRat
namespace QN

instance : Std.Associative (α := QN) (· + ·) := ⟨add_assoc⟩
instance : Std.Commutative (α := QN) (· + ·) := ⟨add_comm⟩
instance : Std.Associative (α := QN) (· * ·) := ⟨mul_assoc⟩
instance : Std.Commutative (α := QN) (· * ·) := ⟨mul_comm⟩

/-! ## Two more ring facts -/

theorem eq_neg_of_add_eq_zero {a b : QN} (h : a + b = 0) : a = -b := by
  calc a = a + (b + -b) := by rw [add_neg_cancel, add_zero]
    _ = (a + b) + -b := by rw [add_assoc]
    _ = -b := by rw [h, zero_add]

theorem mul_neg (x y : QN) : x * -y = -(x * y) := by
  apply eq_neg_of_add_eq_zero
  rw [← mul_add, neg_add_cancel, mul_zero]

theorem add_sub_cancel_left (a b : QN) : a + (b - a) = b := by
  rw [sub_def, add_comm b, ← add_assoc, add_neg_cancel, zero_add]

/-! ## The order facts the inductions use -/

theorem zero_lt_iff (a : QN) : 0 < a ↔ Pos a := by
  rw [lt_iff_pos_sub, sub_zero]

theorem nonneg_add {a b : QN} (ha : 0 ≤ a) (hb : 0 ≤ b) : 0 ≤ a + b := by
  rcases ha with ha | ha
  · rw [← ha, zero_add]
    exact hb
  rcases hb with hb | hb
  · rw [← hb, add_zero]
    exact Or.inr ha
  · exact Or.inr ((zero_lt_iff _).mpr (pos_add ((zero_lt_iff _).mp ha) ((zero_lt_iff _).mp hb)))

theorem pos_add_nonneg {a b : QN} (ha : 0 < a) (hb : 0 ≤ b) : 0 < a + b := by
  rcases hb with hb | hb
  · rw [← hb, add_zero]
    exact ha
  · exact (zero_lt_iff _).mpr (pos_add ((zero_lt_iff _).mp ha) ((zero_lt_iff _).mp hb))

theorem zero_lt_one : (0 : QN) < 1 := by decide

theorem nonneg_of_mul_pos_left {a y : QN} (ha : 0 < a) (h : 0 ≤ a * y) : 0 ≤ y := by
  rcases trichotomy y with hy | hy | hy
  · exact Or.inr ((zero_lt_iff _).mpr hy)
  · exact Or.inl hy.symm
  · exfalso
    have hn : Pos (-(a * y)) := by
      rw [← mul_neg]
      exact pos_mul ((zero_lt_iff _).mp ha) hy
    rcases h with h | h
    · rw [← h, neg_zero] at hn
      exact not_pos_zero hn
    · exact not_pos_and_pos_neg _ ⟨(zero_lt_iff _).mp h, hn⟩

/-! ## Naturals and powers -/

/-- The natural `n` as a number, by counting. -/
def natQ : Nat → QN
  | 0 => 0
  | n + 1 => natQ n + 1

theorem natQ_nonneg : ∀ n : Nat, 0 ≤ natQ n
  | 0 => Or.inl rfl
  | n + 1 => Or.inr (by
      show 0 < natQ n + 1
      rw [add_comm]
      exact pos_add_nonneg zero_lt_one (natQ_nonneg n))

theorem natQ_pos : ∀ n : Nat, 0 < n → 0 < natQ n
  | 0, h => absurd h (Nat.lt_irrefl 0)
  | n + 1, _ => by
      show 0 < natQ n + 1
      rw [add_comm]
      exact pos_add_nonneg zero_lt_one (natQ_nonneg n)

/-- `x` to the power `n`. -/
def qpow (x : QN) : Nat → QN
  | 0 => 1
  | n + 1 => qpow x n * x

theorem qpow_pos {x : QN} (hx : 0 < x) : ∀ n : Nat, 0 < qpow x n
  | 0 => zero_lt_one
  | n + 1 => by
      show 0 < qpow x n * x
      exact mul_pos (qpow_pos hx n) hx

/-! ## Polynomials -/

/-- Coefficients, lowest power first. -/
abbrev Poly := List QN

/-- Horner's rule. -/
def eval : Poly → QN → QN
  | [], _ => 0
  | c :: p, x => c + x * eval p x

def padd : Poly → Poly → Poly
  | [], q => q
  | a :: p, [] => a :: p
  | a :: p, b :: q => (a + b) :: padd p q

def pneg (p : Poly) : Poly := p.map (fun c => -c)

def scale (a : QN) (p : Poly) : Poly := p.map (fun c => a * c)

/-- `(x + 1)` times a polynomial. -/
def mulX1 (p : Poly) : Poly := padd (0 :: p) p

/-- The polynomial `x ↦ p (x + 1)`. -/
def shift : Poly → Poly
  | [] => []
  | c :: p => padd [c] (mulX1 (shift p))

/-- The forward difference. -/
def diff (p : Poly) : Poly := padd (shift p) (pneg p)

theorem eval_padd : ∀ (p q : Poly) (x : QN), eval (padd p q) x = eval p x + eval q x
  | [], q, x => by
      show eval q x = 0 + eval q x
      rw [zero_add]
  | a :: p, [], x => by
      show eval (a :: p) x = eval (a :: p) x + 0
      rw [add_zero]
  | a :: p, b :: q, x => by
      show (a + b) + x * eval (padd p q) x = (a + x * eval p x) + (b + x * eval q x)
      rw [eval_padd p q x, mul_add]
      ac_rfl

theorem eval_pneg : ∀ (p : Poly) (x : QN), eval (pneg p) x = -(eval p x)
  | [], _ => neg_zero.symm
  | c :: p, x => by
      show -c + x * eval (pneg p) x = -(c + x * eval p x)
      rw [eval_pneg p x, mul_neg, neg_add]

theorem eval_scale (a : QN) : ∀ (p : Poly) (x : QN), eval (scale a p) x = a * eval p x
  | [], _ => (mul_zero a).symm
  | c :: p, x => by
      show a * c + x * eval (scale a p) x = a * (c + x * eval p x)
      rw [eval_scale a p x, mul_add]
      ac_rfl

theorem eval_cons_zero (p : Poly) (x : QN) : eval (0 :: p) x = x * eval p x := zero_add _

theorem eval_mulX1 (p : Poly) (x : QN) : eval (mulX1 p) x = (x + 1) * eval p x := by
  show eval (padd (0 :: p) p) x = _
  rw [eval_padd, eval_cons_zero, add_mul, one_mul]

theorem eval_single (c x : QN) : eval [c] x = c := by
  show c + x * 0 = c
  rw [mul_zero, add_zero]

theorem eval_shift : ∀ (p : Poly) (x : QN), eval (shift p) x = eval p (x + 1)
  | [], _ => rfl
  | c :: p, x => by
      show eval (padd [c] (mulX1 (shift p))) x = c + (x + 1) * eval p (x + 1)
      rw [eval_padd, eval_mulX1, eval_shift p x, eval_single]

theorem eval_diff (p : Poly) (x : QN) : eval (diff p) x = eval p (x + 1) - eval p x := by
  show eval (padd (shift p) (pneg p)) x = _
  rw [eval_padd, eval_shift, eval_pneg]
  rfl

/-! ## Constant polynomials -/

def tailZero : Poly → Bool
  | [] => true
  | c :: p => decide (c = 0) && tailZero p

theorem eval_tailZero : ∀ (p : Poly) (x : QN), tailZero p = true → eval p x = 0
  | [], _, _ => rfl
  | c :: p, x, h => by
      simp only [tailZero, Bool.and_eq_true, decide_eq_true_eq] at h
      show c + x * eval p x = 0
      rw [h.1, eval_tailZero p x h.2, mul_zero, add_zero]

/-- Every coefficient past the first is zero. -/
def isConst : Poly → Bool
  | [] => true
  | _ :: p => tailZero p

theorem eval_const : ∀ (p : Poly) (x y : QN), isConst p = true → eval p x = eval p y
  | [], _, _, _ => rfl
  | c :: p, x, y, h => by
      show c + x * eval p x = c + y * eval p y
      rw [eval_tailZero p x h, eval_tailZero p y h, mul_zero, mul_zero]

/-! ## Claims for every natural from a start, by induction -/

/-- A sequence that starts nonnegative and never steps down stays nonnegative. -/
theorem nonneg_step {f : Nat → QN} {n0 : Nat} (h0 : 0 ≤ f n0)
    (hs : ∀ n, n0 ≤ n → 0 ≤ f (n + 1) - f n) : ∀ n, n0 ≤ n → 0 ≤ f n := by
  intro n hn
  induction n with
  | zero =>
      have e : n0 = 0 := by omega
      rw [← e]
      exact h0
  | succ n ih =>
      rcases Nat.lt_or_ge n n0 with h | h
      · have e : n0 = n + 1 := by omega
        rw [← e]
        exact h0
      · have := nonneg_add (ih h) (hs n h)
        rw [add_sub_cancel_left] at this
        exact this

/-- A sequence that starts positive and never steps down stays positive. -/
theorem pos_step {f : Nat → QN} {n0 : Nat} (h0 : 0 < f n0)
    (hs : ∀ n, n0 ≤ n → 0 ≤ f (n + 1) - f n) : ∀ n, n0 ≤ n → 0 < f n := by
  intro n hn
  induction n with
  | zero =>
      have e : n0 = 0 := by omega
      rw [← e]
      exact h0
  | succ n ih =>
      rcases Nat.lt_or_ge n n0 with h | h
      · have e : n0 = n + 1 := by omega
        rw [← e]
        exact h0
      · have := pos_add_nonneg (ih h) (hs n h)
        rw [add_sub_cancel_left] at this
        exact this

/-- The value of `p` at `n0` and of its first `d` forward differences are
all nonnegative. -/
def startsNonneg (n0 : Nat) : Nat → Poly → Bool
  | 0, p => decide (0 ≤ eval p (natQ n0))
  | d + 1, p => decide (0 ≤ eval p (natQ n0)) && startsNonneg n0 d (diff p)

/-- The `d`-th forward difference of `p` is constant. -/
def constAfter : Nat → Poly → Bool
  | 0, p => isConst p
  | d + 1, p => constAfter d (diff p)

/-- **The claim for every natural from `n0` on**, by induction on the
difference order and on `n`. -/
theorem nonneg_from (n0 : Nat) : ∀ (d : Nat) (p : Poly), constAfter d p = true →
    startsNonneg n0 d p = true → ∀ n, n0 ≤ n → 0 ≤ eval p (natQ n)
  | 0, p, hc, hs, n, _ => by
      have h0 : 0 ≤ eval p (natQ n0) := of_decide_eq_true hs
      rw [eval_const p (natQ n) (natQ n0) hc]
      exact h0
  | d + 1, p, hc, hs, n, hn => by
      simp only [startsNonneg, Bool.and_eq_true] at hs
      have h0 : 0 ≤ eval p (natQ n0) := of_decide_eq_true hs.1
      have ih := nonneg_from n0 d (diff p) hc hs.2
      refine nonneg_step (f := fun m => eval p (natQ m)) h0 (fun m hm => ?_) n hn
      have := ih m hm
      rw [eval_diff] at this
      exact this

/-- The strict form: positive at `n0`, differences nonnegative there. -/
def startsPositive (n0 d : Nat) (p : Poly) : Bool :=
  decide (0 < eval p (natQ n0)) && startsNonneg n0 d (diff p)

theorem pos_from (n0 d : Nat) (p : Poly) (hc : constAfter d (diff p) = true)
    (hs : startsPositive n0 d p = true) : ∀ n, n0 ≤ n → 0 < eval p (natQ n) := by
  simp only [startsPositive, Bool.and_eq_true] at hs
  have h0 : 0 < eval p (natQ n0) := of_decide_eq_true hs.1
  have ih := nonneg_from n0 d (diff p) hc hs.2
  refine pos_step (f := fun m => eval p (natQ m)) h0 (fun m hm => ?_)
  have := ih m hm
  rw [eval_diff] at this
  exact this

/-! ## Reciprocal substitution -/

theorem eval_append : ∀ (a b : Poly) (x : QN), eval (a ++ b) x = eval a x + qpow x a.length * eval b x
  | [], b, x => by
      show eval b x = 0 + 1 * eval b x
      rw [zero_add, one_mul]
  | c :: a, b, x => by
      show c + x * eval (a ++ b) x = (c + x * eval a x) + qpow x a.length * x * eval b x
      rw [eval_append a b x, mul_add]
      ac_rfl

theorem pow_mul_inv {x : QN} (hx : x ≠ 0) (n : Nat) : qpow x (n + 1) * x⁻¹ = qpow x n := by
  show qpow x n * x * x⁻¹ = qpow x n
  rw [mul_assoc, mul_inv_cancel x hx, mul_one]

/-- Reading the coefficients in reverse at `x ≠ 0` is `x ^ (length - 1)`
times the value at `x⁻¹`. -/
theorem eval_reverse {x : QN} (hx : x ≠ 0) :
    ∀ p : Poly, eval p.reverse x = qpow x (p.length - 1) * eval p x⁻¹
  | [] => (mul_zero _).symm
  | [c] => by
      show eval [c] x = 1 * eval [c] x⁻¹
      rw [one_mul, eval_single, eval_single]
  | c :: d :: q => by
      rw [List.reverse_cons, eval_append, eval_reverse hx (d :: q), eval_single, List.length_reverse]
      show qpow x q.length * eval (d :: q) x⁻¹ + qpow x (q.length + 1) * c
          = qpow x (q.length + 1) * (c + x⁻¹ * eval (d :: q) x⁻¹)
      rw [mul_add, ← mul_assoc, pow_mul_inv hx, add_comm]

/-- `C - p` and `C + p` as polynomials. -/
def belowBy (c : QN) : Poly → Poly
  | [] => [c]
  | a :: p => (c - a) :: pneg p

def aboveBy (c : QN) : Poly → Poly
  | [] => [c]
  | a :: p => (c + a) :: p

theorem eval_belowBy (c x : QN) : ∀ p : Poly, eval (belowBy c p) x = c - eval p x
  | [] => by
      show c + x * 0 = c + -0
      rw [mul_zero, neg_zero]
  | a :: p => by
      show (c + -a) + x * eval (pneg p) x = c + -(a + x * eval p x)
      rw [eval_pneg, mul_neg, neg_add]
      ac_rfl

theorem eval_aboveBy (c x : QN) : ∀ p : Poly, eval (aboveBy c p) x = c + eval p x
  | [] => by
      show c + x * 0 = c + 0
      rw [mul_zero]
  | a :: p => by
      show (c + a) + x * eval p x = c + (a + x * eval p x)
      rw [add_assoc]

/-- A bound at every `1 / 2 ^ k` for `k ≥ k0`: `C - g` and `C + g` are
nonnegative there when their reversed coefficient lists are nonnegative at
every natural from `2 ^ k0` on (certified by `nonneg_from`). -/
theorem halving_bound (g : Poly) (c : QN) (k0 d : Nat)
    (h1 : constAfter d (belowBy c g).reverse = true)
    (h2 : startsNonneg (2 ^ k0) d (belowBy c g).reverse = true)
    (h3 : constAfter d (aboveBy c g).reverse = true)
    (h4 : startsNonneg (2 ^ k0) d (aboveBy c g).reverse = true) :
    ∀ k, k0 ≤ k → 0 ≤ c - eval g (natQ (2 ^ k))⁻¹ ∧ 0 ≤ c + eval g (natQ (2 ^ k))⁻¹ := by
  intro k hk
  have hle : 2 ^ k0 ≤ 2 ^ k := Nat.pow_le_pow_right (by decide) hk
  have hxpos : 0 < natQ (2 ^ k) := natQ_pos _ (Nat.two_pow_pos k)
  have hx : natQ (2 ^ k) ≠ 0 := fun h => by
    rw [h] at hxpos
    exact lt_irrefl 0 hxpos
  have a1 := nonneg_from (2 ^ k0) d _ h1 h2 (2 ^ k) hle
  have a2 := nonneg_from (2 ^ k0) d _ h3 h4 (2 ^ k) hle
  rw [eval_reverse hx, eval_belowBy] at a1
  rw [eval_reverse hx, eval_aboveBy] at a2
  exact ⟨nonneg_of_mul_pos_left (qpow_pos hxpos _) a1, nonneg_of_mul_pos_left (qpow_pos hxpos _) a2⟩

end QN
end ExactRat
