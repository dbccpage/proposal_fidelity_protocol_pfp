"""Canonical Lean 4 package terms for live toolchain verification in Woland.

AuthorityEffect: None.
"""

CANONICAL_DISCRETE_4D_BIANCHI_LEAN = """
def Simplicial0Cochain (R : Type) := Fin 5 → R
def Simplicial1Cochain (R : Type) := Fin 5 → Fin 5 → R
def Simplicial2Cochain (R : Type) := Fin 5 → Fin 5 → Fin 5 → R
def Simplicial3Cochain (R : Type) := Fin 5 → Fin 5 → Fin 5 → Fin 5 → R
def Simplicial4Cochain (R : Type) := R

def d0 {R : Type} [Sub R] (α : Simplicial0Cochain R) : Simplicial1Cochain R :=
  fun i j => α j - α i

def d1 (ω : Simplicial1Cochain Int) : Simplicial2Cochain Int :=
  fun i j k => ω j k - ω i k + ω i j

def d2 (F : Simplicial2Cochain Int) : Simplicial3Cochain Int :=
  fun i j k l => F j k l - F i k l + F i j l - F i j k

def d3 (ψ : Simplicial3Cochain Int) : Int :=
  let v0 : Fin 5 := ⟨0, by decide⟩
  let v1 : Fin 5 := ⟨1, by decide⟩
  let v2 : Fin 5 := ⟨2, by decide⟩
  let v3 : Fin 5 := ⟨3, by decide⟩
  let v4 : Fin 5 := ⟨4, by decide⟩
  ψ v1 v2 v3 v4 - ψ v0 v2 v3 v4 + ψ v0 v1 v3 v4 - ψ v0 v1 v2 v4 + ψ v0 v1 v2 v3

theorem d1_comp_d0_zero (α : Simplicial0Cochain Int) (i j k : Fin 5) :
    d1 (d0 α) i j k = 0 := by
  dsimp [d1, d0]
  omega

theorem d2_comp_d1_zero (ω : Simplicial1Cochain Int) (i j k l : Fin 5) :
    d2 (d1 ω) i j k l = 0 := by
  dsimp [d2, d1]
  omega

theorem discrete_4d_bianchi_identity (F : Simplicial2Cochain Int) :
    d3 (d2 F) = 0 := by
  dsimp [d3, d2]
  omega

theorem discrete_4d_bianchi_on_connection (ω : Simplicial1Cochain Int) :
    d3 (d2 (d1 ω)) = 0 := by
  have h := discrete_4d_bianchi_identity (d1 ω)
  exact h

structure ExactFraction where
  num : Nat
  den : Nat
  den_pos : 0 < den
deriving DecidableEq, Repr

def ExactFraction.lt (a b : ExactFraction) : Prop :=
  a.num * b.den < b.num * a.den

instance (a b : ExactFraction) : Decidable (a.lt b) :=
  inferInstanceAs (Decidable (a.num * b.den < b.num * a.den))

def spectral_wall_frac : ExactFraction := ⟨1907, 2000, by decide⟩
def spectral_normalizer_frac : ExactFraction := ⟨6, 5, by decide⟩
def spectral_floor_frac : ExactFraction := ⟨31, 800, by decide⟩

theorem spectral_floor_pos : 0 < spectral_floor_frac.num := by decide
theorem spectral_wall_lt_one : spectral_wall_frac.lt ⟨1, 1, by decide⟩ := by decide

theorem spectral_floor_product_identity :
    spectral_floor_frac.num * spectral_normalizer_frac.num * spectral_wall_frac.den =
      (spectral_wall_frac.den - spectral_wall_frac.num) *
        (spectral_floor_frac.den * spectral_normalizer_frac.den) := by decide

theorem spectral_contraction_floor_bound
    (D_scaled : Int)
    (h_wall : 24000 - (6 * D_scaled) / 5 ≤ 22884) :
    930 ≤ D_scaled := by omega

theorem spectral_contraction_precludes_unbiasedness
    (D_scaled : Int)
    (h_wall : 24000 - (6 * D_scaled) / 5 ≤ 22884)
    (h_zero : D_scaled = 0) :
    False := by
  have h_ge := spectral_contraction_floor_bound D_scaled h_wall
  omega

structure SpectralContractionCertificate where
  dev_sq_scaled : Int
  dev_sq_nonneg : 0 ≤ dev_sq_scaled
  h_wall : 24000 - (6 * dev_sq_scaled) / 5 ≤ 22884

theorem certificate_forces_positive_defect
    (cert : SpectralContractionCertificate) :
    930 ≤ cert.dev_sq_scaled ∧ 0 < cert.dev_sq_scaled := by
  have h_ge := spectral_contraction_floor_bound cert.dev_sq_scaled cert.h_wall
  have h_pos : 0 < cert.dev_sq_scaled := by omega
  exact ⟨h_ge, h_pos⟩

theorem certificate_precludes_zero_defect
    (cert : SpectralContractionCertificate) :
    cert.dev_sq_scaled ≠ 0 := by
  have ⟨_, h_pos⟩ := certificate_forces_positive_defect cert
  omega

def curvature_closure_defect (ω : Simplicial1Cochain Int) (i j k l : Fin 5) : Int :=
  d2 (d1 ω) i j k l

theorem curvature_closure_defect_zero (ω : Simplicial1Cochain Int) (i j k l : Fin 5) :
    curvature_closure_defect ω i j k l = 0 := by
  dsimp [curvature_closure_defect]
  exact d2_comp_d1_zero ω i j k l

def integer_closure_ratio (gamma2 phi1 : Int) : Int :=
  if phi1 == 0 then 0 else gamma2 / phi1

theorem closure_ratio_eq_zero (phi1 : Int) (h_phi : 0 < phi1) :
    integer_closure_ratio 0 phi1 = 0 := by
  dsimp [integer_closure_ratio]
  have h_ne : (phi1 == 0) = false := by
    apply beq_false_of_ne
    omega
  rw [h_ne]
  exact Int.zero_ediv phi1

structure BridgeMub6CoverageContract where
  h_4d_bianchi : ∀ (F : Simplicial2Cochain Int), d3 (d2 F) = 0
  h_gamma2_zero : ∀ (ω : Simplicial1Cochain Int) (i j k l : Fin 5),
    curvature_closure_defect ω i j k l = 0
  h_floor_pos : 0 < spectral_floor_frac.num
  h_rcl_zero : ∀ (phi1 : Int), 0 < phi1 → integer_closure_ratio 0 phi1 = 0

theorem bridge_mub6_coverage_master
    (contract : BridgeMub6CoverageContract) :
    0 < spectral_floor_frac.num ∧
    (∀ (F : Simplicial2Cochain Int), d3 (d2 F) = 0) ∧
    (∀ (ω : Simplicial1Cochain Int) (i j k l : Fin 5),
      curvature_closure_defect ω i j k l = 0) ∧
    (∀ (phi1 : Int), 0 < phi1 → integer_closure_ratio 0 phi1 = 0) := by
  refine ⟨contract.h_floor_pos, contract.h_4d_bianchi,
          contract.h_gamma2_zero, contract.h_rcl_zero⟩
"""
