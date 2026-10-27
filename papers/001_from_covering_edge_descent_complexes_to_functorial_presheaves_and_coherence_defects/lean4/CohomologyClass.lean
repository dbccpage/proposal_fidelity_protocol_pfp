import Mathlib.Tactic.Abel
import Mathlib.Tactic.Ring

/-!
 Paper PO-001 Operator Cocycle and Coboundary-Image Kernel.

 The generic H^2 promotion remains open.  For non-flat restriction systems,
 delta_2 after delta_1 need not vanish, so im(delta_1) is not generally a
 subspace of ker(delta_2).

Key formal results:
1. `delta2_operator_curvature_identically_zero`:
   The operator-valued cocycle condition delta_2(K) == 0 holds identically
   and unconditionally for all quadruples a <= b <= c <= d and all section elements sd : A,
   without requiring edge compatibility or lower flatness.
2. `curvature_is_cocycle`:
   Curvature K satisfies the operator cocycle identity.
3. `curvature_coboundary_related_zero_iff_isCoboundary`:
   The declared relation to zero unfolds exactly to image membership.  This is
   definitional and does not construct a cohomology quotient.
-/

namespace Paper001a

universe u

structure QuadRestrictionOp (A : Type u) [AddCommGroup A] where
  rDC : A -> A
  rDB : A -> A
  rDA : A -> A
  rCB : A -> A
  rCA : A -> A
  rBA : A -> A
  rBA_sub : forall x y : A, rBA (x - y) = rBA x - rBA y

namespace QuadRestrictionOp

variable {A : Type u} [AddCommGroup A] (T : QuadRestrictionOp A)

def curvatureDCB (sd : A) : A :=
  T.rCB (T.rDC sd) - T.rDB sd

def curvatureDCA (sd : A) : A :=
  T.rCA (T.rDC sd) - T.rDA sd

def curvatureDBA (sd : A) : A :=
  T.rBA (T.rDB sd) - T.rDA sd

def curvatureCBA (sc : A) : A :=
  T.rBA (T.rCB sc) - T.rCA sc

/-- Operator coboundary delta_2 on 2-cochain components.
    The fourth term evaluates on the restricted section rDC(sd). -/
def delta2 (hDCB hDCA hDBA hCBA_restricted : A) : A :=
  T.rBA hDCB - hDCA + hDBA - hCBA_restricted

/-- Theorem 3.6 — Unconditional Operator Cocycle Identity.
    delta_2(K)(sd) vanishes identically on every quadruple for all sd : A,
    without any hypothesis of edge compatibility or flatness. -/
theorem delta2_operator_curvature_identically_zero (sd : A) :
    T.delta2 (T.curvatureDCB sd) (T.curvatureDCA sd)
        (T.curvatureDBA sd) (T.curvatureCBA (T.rDC sd)) = 0 := by
  simp [delta2, curvatureDCB, curvatureDCA, curvatureDBA, curvatureCBA]
  rw [T.rBA_sub]
  abel

/-- Cocycle predicate for an operator 2-cochain H. -/
def IsCocycle (H_DCB H_DCA H_DBA : A -> A) (H_CBA : A -> A) : Prop :=
  forall sd : A, T.delta2 (H_DCB sd) (H_DCA sd) (H_DBA sd) (H_CBA (T.rDC sd)) = 0

/-- Curvature is an exact cocycle unconditionally. -/
theorem curvature_is_cocycle :
    T.IsCocycle T.curvatureDCB T.curvatureDCA T.curvatureDBA T.curvatureCBA := by
  intro sd
  exact T.delta2_operator_curvature_identically_zero sd

/-- Operator 1-cochains T_{ba}, T_{cb}, T_{dc}, T_{ca}, T_{db}, T_{da}. -/
structure Operator1Cochain where
  tBA : A -> A
  tCB : A -> A
  tDC : A -> A
  tCA : A -> A
  tDB : A -> A
  tDA : A -> A
  tBA_add : forall x y : A, tBA (x + y) = tBA x + tBA y
  rBA_sub : forall x y : A, T.rBA (x - y) = T.rBA x - T.rBA y

/-- Coboundary delta_1 of an operator 1-cochain on triples. -/
def delta1_CBA (t : Operator1Cochain T) (sc : A) : A :=
  T.rBA (t.tCB sc) - t.tCA sc + t.tBA (T.rCB sc)

def delta1_DCB (t : Operator1Cochain T) (sd : A) : A :=
  T.rCB (t.tDC sd) - t.tDB sd + t.tCB (T.rDC sd)

def delta1_DCA (t : Operator1Cochain T) (sd : A) : A :=
  T.rCA (t.tDC sd) - t.tDA sd + t.tCA (T.rDC sd)

def delta1_DBA (t : Operator1Cochain T) (sd : A) : A :=
  T.rBA (t.tDB sd) - t.tDA sd + t.tBA (T.rDB sd)

/-- Coboundary predicate: an operator 2-cochain is a coboundary if it equals delta_1(t). -/
def IsCoboundary (H_DCB H_DCA H_DBA : A -> A) (H_CBA : A -> A) : Prop :=
  exists t : Operator1Cochain T,
    (forall sd, H_DCB sd = T.delta1_DCB t sd) /\
    (forall sd, H_DCA sd = T.delta1_DCA t sd) /\
    (forall sd, H_DBA sd = T.delta1_DBA t sd) /\
    (forall sc, H_CBA sc = T.delta1_CBA t sc)

/-- A declared coboundary relation between two operator 2-cochains.
    No quotient or equivalence-relation theorem is asserted here. -/
def CoboundaryRelated (H1_DCB H1_DCA H1_DBA H1_CBA H2_DCB H2_DCA H2_DBA H2_CBA : A -> A) : Prop :=
  T.IsCoboundary (fun sd => H1_DCB sd - H2_DCB sd)
                 (fun sd => H1_DCA sd - H2_DCA sd)
                 (fun sd => H1_DBA sd - H2_DBA sd)
                 (fun sc => H1_CBA sc - H2_CBA sc)

/-- The curvature tuple is coboundary-related to zero exactly when it is in
    the declared image of delta_1.  This is not an H^2 quotient theorem. -/
theorem curvature_coboundary_related_zero_iff_isCoboundary :
    T.CoboundaryRelated T.curvatureDCB T.curvatureDCA T.curvatureDBA T.curvatureCBA
                      (fun _ => 0) (fun _ => 0) (fun _ => 0) (fun _ => 0) <->
    T.IsCoboundary T.curvatureDCB T.curvatureDCA T.curvatureDBA T.curvatureCBA := by
  constructor
  · intro h
    rcases h with ⟨t, h1, h2, h3, h4⟩
    use t
    refine ⟨?_, ?_, ?_, ?_⟩
    · intro sd; simpa using h1 sd
    · intro sd; simpa using h2 sd
    · intro sd; simpa using h3 sd
    · intro sc; simpa using h4 sc
  · intro h
    rcases h with ⟨t, h1, h2, h3, h4⟩
    use t
    refine ⟨?_, ?_, ?_, ?_⟩
    · intro sd; simpa using h1 sd
    · intro sd; simpa using h2 sd
    · intro sd; simpa using h3 sd
    · intro sc; simpa using h4 sc

end QuadRestrictionOp

end Paper001a
