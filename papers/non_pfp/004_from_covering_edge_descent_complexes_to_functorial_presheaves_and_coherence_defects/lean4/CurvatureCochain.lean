import Mathlib.Tactic.Abel
import Mathlib.Tactic.Ring

/-!
Paper PO-001 curvature-cochain kernel.

This is the algebraic core of Path B. In a single additive fiber, with the
restriction from the middle node to the bottom preserving subtraction, the
typed coboundary calculation `d1 (d0 s) = K(s c)` is Lean-checked.
-/

namespace Paper001a

universe u

structure TripleRestriction (A : Type u) [AddCommGroup A] where
  rCB : A -> A
  rBA : A -> A
  rCA : A -> A
  rBA_sub : forall x y : A, rBA (x - y) = rBA x - rBA y

namespace TripleRestriction

variable {A : Type u} [AddCommGroup A] (T : TripleRestriction A)

def d0CB (sc sb : A) : A :=
  T.rCB sc - sb

def d0BA (sb sa : A) : A :=
  T.rBA sb - sa

def d0CA (sc sa : A) : A :=
  T.rCA sc - sa

def d1 (gCB gCA gBA : A) : A :=
  T.rBA gCB - gCA + gBA

def curvature (sc : A) : A :=
  T.rBA (T.rCB sc) - T.rCA sc

def Flat (T : TripleRestriction A) : Prop :=
  forall sc : A, T.curvature sc = 0

def ChainComposable (T : TripleRestriction A) : Prop :=
  forall sc : A, T.rBA (T.rCB sc) = T.rCA sc

theorem d1_d0_eq_curvature (sc sb sa : A) :
    T.d1 (T.d0CB sc sb) (T.d0CA sc sa) (T.d0BA sb sa) =
      T.curvature sc := by
  simp [d1, d0CB, d0CA, d0BA, curvature]
  rw [T.rBA_sub]
  abel

theorem flat_iff_chainComposable :
    T.Flat <-> T.ChainComposable := by
  constructor
  · intro h sc
    exact sub_eq_zero.mp (h sc)
  · intro h sc
    exact sub_eq_zero.mpr (h sc)

theorem d1_d0_zero_iff_flat [Inhabited A] :
    (forall sc sb sa : A,
        T.d1 (T.d0CB sc sb) (T.d0CA sc sa) (T.d0BA sb sa) = 0)
      <-> T.Flat := by
  constructor
  · intro h sc
    simpa [d1_d0_eq_curvature T sc default default] using
      h sc default default
  · intro h sc sb sa
    rw [d1_d0_eq_curvature T sc sb sa]
    exact h sc

theorem flat_iff_d1_d0_zero [Inhabited A] :
    T.Flat <->
      (forall sc sb sa : A,
        T.d1 (T.d0CB sc sb) (T.d0CA sc sa) (T.d0BA sb sa) = 0) :=
  (d1_d0_zero_iff_flat T).symm

theorem nonzero_curvature_not_chainComposable
    {sc : A} (hcurv : T.curvature sc ≠ 0) :
    Not T.ChainComposable := by
  intro hchain
  exact hcurv (sub_eq_zero.mpr (hchain sc))

theorem chainComposable_iff_curvature_zero :
    T.ChainComposable <-> T.Flat :=
  (flat_iff_chainComposable T).symm

end TripleRestriction

theorem scalar_diamond_curvature
    (alpha beta mu v : Int) :
    beta * (alpha * v) - mu * v = (beta * alpha - mu) * v := by
  ring

structure QuadRestriction (A : Type u) [AddCommGroup A] where
  rDC : A -> A
  rDB : A -> A
  rDA : A -> A
  rCB : A -> A
  rCA : A -> A
  rBA : A -> A
  rBA_sub : forall x y : A, rBA (x - y) = rBA x - rBA y

namespace QuadRestriction

variable {A : Type u} [AddCommGroup A] (T : QuadRestriction A)

def d0DC (sd sc : A) : A :=
  T.rDC sd - sc

def curvatureDCB (sd : A) : A :=
  T.rCB (T.rDC sd) - T.rDB sd

def curvatureDCA (sd : A) : A :=
  T.rCA (T.rDC sd) - T.rDA sd

def curvatureDBA (sd : A) : A :=
  T.rBA (T.rDB sd) - T.rDA sd

def curvatureCBA (sc : A) : A :=
  T.rBA (T.rCB sc) - T.rCA sc

def d2 (hDCB hDCA hDBA hCBA : A) : A :=
  T.rBA hDCB - hDCA + hDBA - hCBA

theorem d2_curvature_eq_lower_curvature_difference
    (sd sc : A) :
    T.d2 (T.curvatureDCB sd) (T.curvatureDCA sd)
        (T.curvatureDBA sd) (T.curvatureCBA sc) =
      T.curvatureCBA (T.rDC sd) - T.curvatureCBA sc := by
  simp [d2, curvatureDCB, curvatureDCA, curvatureDBA, curvatureCBA]
  rw [T.rBA_sub]
  abel

theorem d2_curvature_zero_of_lower_flat
    (sd sc : A) (hflat : forall x : A, T.curvatureCBA x = 0) :
    T.d2 (T.curvatureDCB sd) (T.curvatureDCA sd)
        (T.curvatureDBA sd) (T.curvatureCBA sc) = 0 := by
  rw [d2_curvature_eq_lower_curvature_difference T sd sc]
  rw [hflat (T.rDC sd), hflat sc]
  abel

theorem d2_curvature_zero_of_edge_compatible
    (sd sc : A) (hedge : T.rDC sd = sc) :
    T.d2 (T.curvatureDCB sd) (T.curvatureDCA sd)
        (T.curvatureDBA sd) (T.curvatureCBA sc) = 0 := by
  rw [d2_curvature_eq_lower_curvature_difference T sd sc]
  rw [hedge]
  abel

end QuadRestriction

end Paper001a
