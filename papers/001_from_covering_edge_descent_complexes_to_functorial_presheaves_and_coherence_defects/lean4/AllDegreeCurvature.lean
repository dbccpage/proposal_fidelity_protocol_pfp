import Mathlib.Tactic.NoncommRing

/-!
Universal parity-algebra kernel for PO001-ALL-DEGREE-CURVED and the gauge
zero-obstruction. This assumes, rather than constructs, the incidence DGA laws.
The chain-deletion proof is in manuscript §4.1 and the finite implementations.
Reproduction profile is recorded separately; no pinned-package replay is implied.
-/

namespace Paper001AllDegree

structure ParityDGA (R : Type*) [Ring R] where
  parity : R →+* R
  differential : R →+ R
  involutive : ∀ x, parity (parity x) = x
  square_zero : ∀ x, differential (differential x) = 0
  leibniz : ∀ x y, differential (x * y) =
    differential x * y + parity x * differential y
  anticommute : ∀ x, differential (parity x) = -parity (differential x)

namespace ParityDGA

variable {R : Type*} [Ring R] (E : ParityDGA R)

def curvature (a : R) : R := E.differential a + a * a

def covariant (a x : R) : R :=
  E.differential x + a * x - E.parity x * a

theorem differential_odd_is_even (a : R) (ha : E.parity a = -a) :
    E.parity (E.differential a) = E.differential a := by
  have h := E.anticommute a
  rw [ha, map_neg] at h
  exact (neg_injective h).symm

theorem curvature_even (a : R) (ha : E.parity a = -a) :
    E.parity (E.curvature a) = E.curvature a := by
  simp only [curvature, map_add, map_mul, ha, E.differential_odd_is_even a ha]
  noncomm_ring

theorem covariant_leibniz (a x y : R) :
    E.covariant a (x * y) =
      E.covariant a x * y + E.parity x * E.covariant a y := by
  simp only [covariant, E.leibniz, map_mul]
  noncomm_ring

theorem covariant_square (a x : R) (ha : E.parity a = -a) :
    E.covariant a (E.covariant a x) =
      E.curvature a * x - x * E.curvature a := by
  simp only [covariant, curvature, map_sub, map_add, map_mul,
    E.leibniz, E.square_zero, E.anticommute, E.involutive, ha]
  noncomm_ring

theorem bianchi (a : R) (ha : E.parity a = -a) :
    E.covariant a (E.curvature a) = 0 := by
  unfold covariant
  rw [E.curvature_even a ha]
  simp only [curvature, map_add,
    E.square_zero, E.leibniz, ha]
  noncomm_ring

theorem invertible_endpoints_preserve_zero (g gl h hr x : R)
    (hg : gl * g = 1) (hh : h * hr = 1) :
    g * x * h = 0 ↔ x = 0 := by
  constructor
  · intro hx
    calc
      x = (gl * g) * x * (h * hr) := by rw [hg, hh]; simp
      _ = gl * (g * x * h) * hr := by noncomm_ring
      _ = 0 := by rw [hx]; simp
  · intro hx
    rw [hx]
    simp

#print axioms differential_odd_is_even
#print axioms curvature_even
#print axioms covariant_leibniz
#print axioms covariant_square
#print axioms bianchi
#print axioms invertible_endpoints_preserve_zero

end ParityDGA
end Paper001AllDegree
