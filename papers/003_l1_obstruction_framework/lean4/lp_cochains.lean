/- Review scope: integer finite fixtures and stated hypotheses; no general real Lp, Clarkson, or Schatten theorem. AuthorityEffect: None. -/
import Init.Omega

/-!
# LP-COCHAINS: Finite-Dimensional L^p Cochains, Norms, and Quotient Defect Φ_p

This module provides the formal mathematical definitions and foundational theorems
for the L^p cochain spaces across Paper 037 (Finite Obstruction Calculus).

Key notions formalized:
- Arbitrary finite-dimensional coordinate vectors (`List Int`, `List Nat`).
- Coordinatewise addition, subtraction, dot product.
- Weighted L^p power norms ‖r‖_{p, w}^p = ∑_e w_e |r_e|^p for p ≥ 1.
- Pure Nat norms and cast-equality lemmas ensuring non-negativity.
- Quotient defect functional Φ_p(h, d₀ f) = ‖h - d₀ f‖_{p, w}^p.
- Concrete 3-cycle simplicial complex model: `Cochain3`, `Potential3`, `Weights3`.

AuthorityEffect: None.
-/

/-- Discrete dot product of coordinate vectors. -/
def dot : List Int → List Int → Int
  | [], _ => 0
  | _, [] => 0
  | x :: xs, y :: ys => x * y + dot xs ys

/-- Vector addition of cochains. -/
def vec_add : List Int → List Int → List Int
  | [], _ => []
  | _, [] => []
  | x :: xs, y :: ys => (x + y) :: vec_add xs ys

/-- Vector subtraction of cochains. -/
def vec_sub : List Int → List Int → List Int
  | [], _ => []
  | _, [] => []
  | x :: xs, y :: ys => (x - y) :: vec_sub xs ys

/-- Pure Nat weighted L1 norm. -/
def l1_norm_nat : List Nat → List Int → Nat
  | [], _ => 0
  | _, [] => 0
  | w :: ws, r :: rs => w * r.natAbs + l1_norm_nat ws rs

/-- Weighted L1 norm: ‖r‖_{1, w} = ∑_e w_e |r_e|. -/
def l1_norm : List Nat → List Int → Int
  | [], _ => 0
  | _, [] => 0
  | w :: ws, r :: rs => (w : Int) * (r.natAbs : Int) + l1_norm ws rs

/-- Pure Nat weighted L2 squared norm: ∑_e w_e r_e^2. -/
def l2_sq_norm_nat : List Nat → List Int → Nat
  | [], _ => 0
  | _, [] => 0
  | w :: ws, r :: rs => w * (r.natAbs * r.natAbs) + l2_sq_norm_nat ws rs

/-- Weighted L2 squared norm: ‖r‖_{2, w}^2 = ∑_e w_e r_e^2. -/
def l2_sq_norm : List Nat → List Int → Int
  | [], _ => 0
  | _, [] => 0
  | w :: ws, r :: rs => (w : Int) * (r * r) + l2_sq_norm ws rs

/-- L-infinity norm: ‖r‖_∞ = max_e |r_e|. -/
def linf_norm : List Int → Nat
  | [] => 0
  | x :: xs => Nat.max x.natAbs (linf_norm xs)

/-- Pure Nat general Lp power norm: ∑_e w_e |r_e|^p. -/
def lp_pow_norm_nat (p : Nat) : List Nat → List Int → Nat
  | [], _ => 0
  | _, [] => 0
  | w :: ws, r :: rs => w * (r.natAbs ^ p) + lp_pow_norm_nat p ws rs

/-- General Lp power norm for integer p ≥ 1: ‖r‖_{p, w}^p = ∑_e w_e |r_e|^p. -/
def lp_pow_norm (p : Nat) : List Nat → List Int → Int
  | [], _ => 0
  | _, [] => 0
  | w :: ws, r :: rs => (w : Int) * ((r.natAbs ^ p : Nat) : Int) + lp_pow_norm p ws rs

/-- Lemma: Lp power norm in Int coincides with cast of pure Nat norm. -/
theorem lp_pow_norm_eq_cast (p : Nat) (w : List Nat) (r : List Int) :
    lp_pow_norm p w r = (lp_pow_norm_nat p w r : Int) := by
  induction w generalizing r with
  | nil =>
    cases r <;> rfl
  | cons w_hd w_tl ih =>
    cases r with
    | nil => rfl
    | cons r_hd r_tl =>
      dsimp [lp_pow_norm, lp_pow_norm_nat]
      rw [ih r_tl]

/-- Residual cochain r = h - d₀ f in general dimension. -/
def lp_residual (h : List Int) (d0f : List Int) : List Int :=
  vec_sub h d0f

/-- L^p quotient defect functional Φ_p(h, d₀ f) = ‖h - d₀ f‖_{p, w}^p. -/
def lp_defect (p : Nat) (w : List Nat) (h : List Int) (d0f : List Int) : Int :=
  lp_pow_norm p w (vec_sub h d0f)

/-- Non-negativity of general weighted L^p power norm. -/
theorem lp_pow_norm_nonneg (p : Nat) (w : List Nat) (r : List Int) :
    0 ≤ lp_pow_norm p w r := by
  rw [lp_pow_norm_eq_cast]
  omega

/-- Non-negativity of quotient defect functional Φ_p. -/
theorem lp_defect_nonneg (p : Nat) (w : List Nat) (h : List Int) (d0f : List Int) :
    0 ≤ lp_defect p w h d0f := by
  dsimp [lp_defect]
  exact lp_pow_norm_nonneg p w (vec_sub h d0f)

/-!
### 3-Cycle Concrete Geometric Model
-/

structure Cochain3 where
  e0 : Int
  e1 : Int
  e2 : Int

structure Potential3 where
  v0 : Int
  v1 : Int
  v2 : Int

structure Weights3 where
  w0 : Nat
  w1 : Nat
  w2 : Nat

def cycle3_d0 (p : Potential3) : Cochain3 :=
  { e0 := p.v1 - p.v0
  , e1 := p.v2 - p.v1
  , e2 := p.v0 - p.v2 }

def residual3 (h : Cochain3) (p : Potential3) : Cochain3 :=
  { e0 := h.e0 - (p.v1 - p.v0)
  , e1 := h.e1 - (p.v2 - p.v1)
  , e2 := h.e2 - (p.v0 - p.v2) }

def dot3 (u v : Cochain3) : Int :=
  u.e0 * v.e0 + u.e1 * v.e1 + u.e2 * v.e2

def linf3 (u : Cochain3) : Nat :=
  Nat.max u.e0.natAbs (Nat.max u.e1.natAbs u.e2.natAbs)

def l13 (u : Cochain3) : Int :=
  (u.e0.natAbs : Int) + (u.e1.natAbs : Int) + (u.e2.natAbs : Int)

def l2sq3_nat (c : Cochain3) : Nat :=
  c.e0.natAbs * c.e0.natAbs + c.e1.natAbs * c.e1.natAbs + c.e2.natAbs * c.e2.natAbs

def l2sq3 (u : Cochain3) : Int :=
  (l2sq3_nat u : Int)

def lp_pow3_nat (p : Nat) (c : Cochain3) : Nat :=
  c.e0.natAbs ^ p + c.e1.natAbs ^ p + c.e2.natAbs ^ p

def lp_pow3 (p : Nat) (c : Cochain3) : Int :=
  (lp_pow3_nat p c : Int)

def lp_pow_norm3_nat (p : Nat) (w : Weights3) (c : Cochain3) : Nat :=
  w.w0 * (c.e0.natAbs ^ p) + w.w1 * (c.e1.natAbs ^ p) + w.w2 * (c.e2.natAbs ^ p)

def lp_pow_norm3 (p : Nat) (w : Weights3) (c : Cochain3) : Int :=
  (w.w0 : Int) * ((c.e0.natAbs ^ p : Nat) : Int)
  + (w.w1 : Int) * ((c.e1.natAbs ^ p : Nat) : Int)
  + (w.w2 : Int) * ((c.e2.natAbs ^ p : Nat) : Int)

theorem lp_pow_norm3_eq_cast (p : Nat) (w : Weights3) (c : Cochain3) :
    lp_pow_norm3 p w c = (lp_pow_norm3_nat p w c : Int) := by
  dsimp [lp_pow_norm3, lp_pow_norm3_nat]

def phi_p_3 (p : Nat) (w : Weights3) (h : Cochain3) (f : Potential3) : Int :=
  lp_pow_norm3 p w (residual3 h f)

theorem phi_p_3_nonneg (p : Nat) (w : Weights3) (h : Cochain3) (f : Potential3) :
    0 ≤ phi_p_3 p w h f := by
  dsimp [phi_p_3]
  rw [lp_pow_norm3_eq_cast]
  omega

def is_cycle3_circulation (z : Cochain3) : Prop :=
  z.e0 = z.e1 ∧ z.e1 = z.e2

theorem cycle3_potential_sum_zero (z : Int) (p : Potential3) :
    z * (p.v1 - p.v0) + z * (p.v2 - p.v1) + z * (p.v0 - p.v2) = 0 := by
  have hzero : (p.v1 - p.v0) + (p.v2 - p.v1) + (p.v0 - p.v2) = 0 := by omega
  have hdistrib : z * (p.v1 - p.v0) + z * (p.v2 - p.v1) + z * (p.v0 - p.v2)
                = z * ((p.v1 - p.v0) + (p.v2 - p.v1) + (p.v0 - p.v2)) := by
    simp [Int.mul_add]
  rw [hdistrib, hzero, Int.mul_zero]

theorem circulation_pairing_gauge_invariant (z : Cochain3) (h : Cochain3) (p : Potential3)
    (hz : is_cycle3_circulation z) :
    dot3 z h = dot3 z (residual3 h p) := by
  rcases hz with ⟨h01, h12⟩
  simp [dot3, residual3]
  rw [h01, h12]
  have h1 : z.e2 * (h.e0 - (p.v1 - p.v0)) = z.e2 * h.e0 - z.e2 * (p.v1 - p.v0) := Int.mul_sub z.e2 h.e0 (p.v1 - p.v0)
  have h2 : z.e2 * (h.e1 - (p.v2 - p.v1)) = z.e2 * h.e1 - z.e2 * (p.v2 - p.v1) := Int.mul_sub z.e2 h.e1 (p.v2 - p.v1)
  have h3 : z.e2 * (h.e2 - (p.v0 - p.v2)) = z.e2 * h.e2 - z.e2 * (p.v0 - p.v2) := Int.mul_sub z.e2 h.e2 (p.v0 - p.v2)
  have hnull : z.e2 * (p.v1 - p.v0) + z.e2 * (p.v2 - p.v1) + z.e2 * (p.v0 - p.v2) = 0 :=
    cycle3_potential_sum_zero z.e2 p
  rw [h1, h2, h3]
  omega

def is_gauge_fixed (p : Potential3) : Prop :=
  p.v0 = 0

theorem gauge_fixed_kernel_trivial (p : Potential3)
    (hgauge : is_gauge_fixed p)
    (hker : (cycle3_d0 p).e0 = 0 ∧ (cycle3_d0 p).e1 = 0) :
    p.v0 = 0 ∧ p.v1 = 0 ∧ p.v2 = 0 := by
  simp [cycle3_d0] at hker
  rcases hker with ⟨h0, h1⟩
  dsimp [is_gauge_fixed] at hgauge
  have hv1 : p.v1 = 0 := by omega
  have hv2 : p.v2 = 0 := by omega
  exact ⟨hgauge, hv1, hv2⟩

#print axioms lp_pow_norm_eq_cast
#print axioms lp_pow_norm_nonneg
#print axioms lp_defect_nonneg
#print axioms lp_pow_norm3_eq_cast
#print axioms phi_p_3_nonneg
#print axioms cycle3_potential_sum_zero
#print axioms circulation_pairing_gauge_invariant
#print axioms gauge_fixed_kernel_trivial
