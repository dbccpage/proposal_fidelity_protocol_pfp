/- Review scope: integer finite fixtures and stated hypotheses; no general real Lp, Clarkson, or Schatten theorem. AuthorityEffect: None. -/
import Init.Omega
import «lp_weak_duality»

/-!
# LP-HODGE-HELMHOLTZ: p = 2 Hodge-Helmholtz Orthogonal Decomposition Theorem

This module mechanizes the canonical Hilbert space p = 2 Hodge-Helmholtz orthogonal
decomposition theorem for the Finite Obstruction Calculus in Paper 037:
- Adjoint divergence operator d₀* mapping edge 1-cochains to vertex 0-chains.
- Exact adjoint property: ⟨d₀* W, p⟩_V = ⟨W, d₀ p⟩_E.
- Discrete orthogonality: im(d₀) ⊥ ker(d₀*).
- Pythagorean L2 energy conservation: ‖u + v‖₂² = ‖u‖₂² + ‖v‖₂² whenever ⟨u, v⟩ = 0.
- Energy conservation for Hodge-Helmholtz split: ‖W + d₀ p‖₂² = ‖W‖₂² + ‖d₀ p‖₂².

AuthorityEffect: None.
-/

/-- Standard L2 energy quadratic form on edge cochains: ∑_e u_e^2. -/
def l2_energy3 (u : Cochain3) : Int :=
  u.e0 * u.e0 + u.e1 * u.e1 + u.e2 * u.e2

def dot_pot3 (p q : Potential3) : Int :=
  p.v0 * q.v0 + p.v1 * q.v1 + p.v2 * q.v2

/-- Exact adjoint property: ⟨d₀* W, p⟩_V = ⟨W, d₀ p⟩_E. -/
theorem cycle3_d0_adjoint_identity (w : Cochain3) (p : Potential3) :
    dot_pot3 (cycle3_d0_adj w) p = dot3 w (cycle3_d0 p) := by
  simp [dot_pot3, cycle3_d0_adj, dot3, cycle3_d0]
  have h1 : (w.e2 - w.e0) * p.v0 = w.e2 * p.v0 - w.e0 * p.v0 := Int.sub_mul w.e2 w.e0 p.v0
  have h2 : (w.e0 - w.e1) * p.v1 = w.e0 * p.v1 - w.e1 * p.v1 := Int.sub_mul w.e0 w.e1 p.v1
  have h3 : (w.e1 - w.e2) * p.v2 = w.e1 * p.v2 - w.e2 * p.v2 := Int.sub_mul w.e1 w.e2 p.v2
  have g1 : w.e0 * (p.v1 - p.v0) = w.e0 * p.v1 - w.e0 * p.v0 := Int.mul_sub w.e0 p.v1 p.v0
  have g2 : w.e1 * (p.v2 - p.v1) = w.e1 * p.v2 - w.e1 * p.v1 := Int.mul_sub w.e1 p.v2 p.v1
  have g3 : w.e2 * (p.v0 - p.v2) = w.e2 * p.v0 - w.e2 * p.v2 := Int.mul_sub w.e2 p.v0 p.v2
  rw [h1, h2, h3, g1, g2, g3]
  omega

/-- Fundamental Hodge Orthogonality Theorem:
    im(d₀) ⊥ ker(d₀*).
    Any gradient field d₀ p is orthogonal to any divergence-free circulation field W. -/
theorem hodge_orthogonality (w : Cochain3) (p : Potential3)
    (hdiv : is_divergence_free w) :
    dot3 w (cycle3_d0 p) = 0 := by
  have hadj := cycle3_d0_adjoint_identity w p
  rw [← hadj]
  rcases hdiv with ⟨dv0, dv1, dv2⟩
  simp [dot_pot3, dv0, dv1, dv2]

/-- Pythagorean energy conservation:
    If ⟨u, v⟩ = 0, then ‖u + v‖₂² = ‖u‖₂² + ‖v‖₂². -/
theorem pythagorean_theorem3 (u v : Cochain3)
    (hortho : dot3 u v = 0) :
    l2_energy3 { e0 := u.e0 + v.e0, e1 := u.e1 + v.e1, e2 := u.e2 + v.e2 } =
    l2_energy3 u + l2_energy3 v := by
  simp [l2_energy3]
  have h0 : (u.e0 + v.e0) * (u.e0 + v.e0) = u.e0 * u.e0 + 2 * (u.e0 * v.e0) + v.e0 * v.e0 := by
    have hmul : (u.e0 + v.e0) * (u.e0 + v.e0) = u.e0 * (u.e0 + v.e0) + v.e0 * (u.e0 + v.e0) :=
      Int.add_mul u.e0 v.e0 (u.e0 + v.e0)
    have m1 : u.e0 * (u.e0 + v.e0) = u.e0 * u.e0 + u.e0 * v.e0 := Int.mul_add u.e0 u.e0 v.e0
    have m2 : v.e0 * (u.e0 + v.e0) = v.e0 * u.e0 + v.e0 * v.e0 := Int.mul_add v.e0 u.e0 v.e0
    have mcomm : v.e0 * u.e0 = u.e0 * v.e0 := Int.mul_comm v.e0 u.e0
    rw [hmul, m1, m2, mcomm]
    omega
  have h1 : (u.e1 + v.e1) * (u.e1 + v.e1) = u.e1 * u.e1 + 2 * (u.e1 * v.e1) + v.e1 * v.e1 := by
    have hmul : (u.e1 + v.e1) * (u.e1 + v.e1) = u.e1 * (u.e1 + v.e1) + v.e1 * (u.e1 + v.e1) :=
      Int.add_mul u.e1 v.e1 (u.e1 + v.e1)
    have m1 : u.e1 * (u.e1 + v.e1) = u.e1 * u.e1 + u.e1 * v.e1 := Int.mul_add u.e1 u.e1 v.e1
    have m2 : v.e1 * (u.e1 + v.e1) = v.e1 * u.e1 + v.e1 * v.e1 := Int.mul_add v.e1 u.e1 v.e1
    have mcomm : v.e1 * u.e1 = u.e1 * v.e1 := Int.mul_comm v.e1 u.e1
    rw [hmul, m1, m2, mcomm]
    omega
  have h2 : (u.e2 + v.e2) * (u.e2 + v.e2) = u.e2 * u.e2 + 2 * (u.e2 * v.e2) + v.e2 * v.e2 := by
    have hmul : (u.e2 + v.e2) * (u.e2 + v.e2) = u.e2 * (u.e2 + v.e2) + v.e2 * (u.e2 + v.e2) :=
      Int.add_mul u.e2 v.e2 (u.e2 + v.e2)
    have m1 : u.e2 * (u.e2 + v.e2) = u.e2 * u.e2 + u.e2 * v.e2 := Int.mul_add u.e2 u.e2 v.e2
    have m2 : v.e2 * (u.e2 + v.e2) = v.e2 * u.e2 + v.e2 * v.e2 := Int.mul_add v.e2 u.e2 v.e2
    have mcomm : v.e2 * u.e2 = u.e2 * v.e2 := Int.mul_comm v.e2 u.e2
    rw [hmul, m1, m2, mcomm]
    omega
  rw [h0, h1, h2]
  simp [dot3] at hortho
  omega

/-- Energy conservation for the Hodge-Helmholtz orthogonal split h = W + d₀ p:
    ‖W + d₀ p‖₂² = ‖W‖₂² + ‖d₀ p‖₂². -/
theorem hodge_helmholtz_energy_conservation (w : Cochain3) (p : Potential3)
    (hdiv : is_divergence_free w) :
    l2_energy3 { e0 := w.e0 + (cycle3_d0 p).e0, e1 := w.e1 + (cycle3_d0 p).e1, e2 := w.e2 + (cycle3_d0 p).e2 } =
    l2_energy3 w + l2_energy3 (cycle3_d0 p) := by
  have hortho := hodge_orthogonality w p hdiv
  exact pythagorean_theorem3 w (cycle3_d0 p) hortho

#print axioms cycle3_d0_adjoint_identity
#print axioms hodge_orthogonality
#print axioms pythagorean_theorem3
#print axioms hodge_helmholtz_energy_conservation
