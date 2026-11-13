/- Review scope: integer finite fixtures and stated hypotheses; no general real Lp, Clarkson, or Schatten theorem. AuthorityEffect: None. -/
import Init.Omega
import «l1c_t03_weak_duality»
import «l1c_general_certificate»

/-!
# L1C-LP-COCHAINS: Finite-Dimensional L^p Cochains and Quotient Defect Φ_p

This module mechanizes the finite-dimensional L^p cochain spaces, vector operations,
weighted L^p power norms, L^∞ norms, and the quotient defect functional Φ_p
for the Finite Obstruction Calculus across Paper 007.

Key mathematical structures:
- Arbitrary finite dimension m (inherits `dot` and `vec_add` from `l1c_general_certificate`).
- Vector subtraction `vec_sub`.
- 3-cycle concrete simplicial model (inherits `Cochain3`, `Potential3`, `Weights3`, `cycle3_d0`, `residual3`).
- Norms on Cochain3: `dot3`, `linf3`, `l13`, `l2sq3`, `lp_pow3`.
- L^p power norm: ‖r‖_{p, w}^p = ∑_e w_e |r_e|^p for integer p ≥ 1.
- Quotient defect Φ_p(h, f) = ‖h - d₀ f‖_{p, w}^p.

AuthorityEffect: None.
-/

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

#print axioms lp_pow_norm_eq_cast
#print axioms lp_pow_norm_nonneg
#print axioms lp_defect_nonneg
#print axioms lp_pow_norm3_eq_cast
#print axioms phi_p_3_nonneg
