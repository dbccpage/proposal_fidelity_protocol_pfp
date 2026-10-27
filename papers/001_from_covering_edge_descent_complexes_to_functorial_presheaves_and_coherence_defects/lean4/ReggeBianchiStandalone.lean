/-!
Paper PO-001 v2.0: Simplicial Face Posets and Regge-Bianchi Identity (Standalone Lean 4 Core Kernel).

AuthorityEffect: None.

Formalizes Theorem 4.8 of PO-001 v2.0:
1. Simplicial face poset chains:
   A saturated quadruple sigma_0 -< sigma_1 -< sigma_2 -< sigma_3 represents a sequence of
   simplices ordered by codimension-1 face inclusion:
     dim(sigma_{k+1}) = dim(sigma_k) + 1.
2. Regge connection and parallel transport:
   Each comparable pair has a restriction map r_{j, i} : Hom(F(j), F(i)).
3. Discrete hinge curvature:
   K_{c, b, a}(x) = r_{b, a}(r_{c, b}(x)) - r_{c, a}(x).
4. Discrete Regge-Bianchi Identity:
   The operator coboundary delta_2(K) vanishes identically on every quadruple:
     delta_2(K)(sigma_3, sigma_2, sigma_1, sigma_0) = 0.
   In Regge calculus, dualizing around vertices yields the discrete Bianchi identity:
     vec_prod_{h in boundary(v^*)} R(h) = I.
-/

namespace Paper001a

namespace ReggeBianchiCore

/-- The discrete curvature 2-cochain operator on a comparable triple (a, b, c):
    K(a, b, c)(x) = r_{b, a}(r_{c, b}(x)) - r_{c, a}(x) -/
def curvature (r_ba r_cb r_ca : Int -> Int) (x : Int) : Int :=
  r_ba (r_cb x) - r_ca x

/-- The operator coboundary delta_2(K) on a quadruple (0, 1, 2, 3):
    delta_2(K) = r_{1, 0}(K(1, 2, 3)) - K(0, 2, 3) + K(0, 1, 3) - K(0, 1, 2)(r_{3, 2}(x)) -/
def reggeOperatorCoboundary
    (r10 r21 r32 r31 r20 r30 : Int -> Int) (x : Int) : Int :=
  let k123 := curvature r21 r32 r31 x
  let k023 := curvature r20 r32 r30 x
  let k013 := curvature r10 r31 r30 x
  let k012 := curvature r10 r21 r20 (r32 x)
  r10 k123 - k023 + k013 - k012

/-- Theorem 4.8: The discrete Regge-Bianchi identity holds identically in any linear representation.
    All terms in delta_2(K) cancel pairwise with zero curvature hypothesis required. -/
theorem regge_bianchi_identity_unconditional
    (r10 r21 r32 r31 r20 r30 : Int -> Int)
    (h_linear : forall u v, r10 (u - v) = r10 u - r10 v)
    (x : Int) :
    reggeOperatorCoboundary r10 r21 r32 r31 r20 r30 x = 0 := by
  dsimp [reggeOperatorCoboundary, curvature]
  rw [h_linear]
  omega

/-- Corollary: On a flat Regge system (all K == 0), delta_2(K) is trivially zero -/
theorem regge_bianchi_flat_system
    (r10 r21 r32 r31 r20 r30 : Int -> Int)
    (h_linear : forall u v, r10 (u - v) = r10 u - r10 v)
    (x : Int)
    (_h123 : r21 (r32 x) = r31 x)
    (_h023 : r20 (r32 x) = r30 x)
    (_h013 : r10 (r31 x) = r30 x)
    (_h012 : r10 (r21 (r32 x)) = r20 (r32 x)) :
    reggeOperatorCoboundary r10 r21 r32 r31 r20 r30 x = 0 := by
  exact regge_bianchi_identity_unconditional r10 r21 r32 r31 r20 r30 h_linear x

end ReggeBianchiCore

end Paper001a
