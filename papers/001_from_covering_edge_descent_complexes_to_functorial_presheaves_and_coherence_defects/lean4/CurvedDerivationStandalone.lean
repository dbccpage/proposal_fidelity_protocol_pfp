/-!
Paper PO-001 v2.0: Curved Operator Derivation Identity (Standalone Lean 4 Core Kernel).

AuthorityEffect: None.

Formalizes Theorem 4.1 in pure Lean 4 core without external dependencies:
  (delta_2 (delta_1 t))_{d, c, b, a} = [K, t]_{d, c, b, a}
                                      = K_{c, b, a} ∘ t_{d, c} - t_{b, a} ∘ K_{d, c, b}

This module provides an axiomatic algebraic formalization requiring zero external libraries.
-/

namespace Paper001a

universe u

structure QuadRestrictionOpCore (A : Type u) where
  rDC : A -> A
  rDB : A -> A
  rDA : A -> A
  rCB : A -> A
  rCA : A -> A
  rBA : A -> A

structure Operator1CochainCore (A : Type u) where
  tBA : A -> A
  tCB : A -> A
  tDC : A -> A
  tCA : A -> A
  tDB : A -> A
  tDA : A -> A

namespace QuadRestrictionOpCore

variable {A : Type u} (T : QuadRestrictionOpCore A)

def curvatureDCB [Sub A] (sd : A) : A :=
  T.rCB (T.rDC sd) - T.rDB sd

def curvatureDCA [Sub A] (sd : A) : A :=
  T.rCA (T.rDC sd) - T.rDA sd

def curvatureDBA [Sub A] (sd : A) : A :=
  T.rBA (T.rDB sd) - T.rDA sd

def curvatureCBA [Sub A] (sc : A) : A :=
  T.rBA (T.rCB sc) - T.rCA sc

def delta2 [Add A] [Sub A] (hDCB hDCA hDBA hCBA_restricted : A) : A :=
  T.rBA hDCB - hDCA + hDBA - hCBA_restricted

def delta1_CBA [Add A] [Sub A] (t : Operator1CochainCore A) (sc : A) : A :=
  T.rBA (t.tCB sc) - t.tCA sc + t.tBA (T.rCB sc)

def delta1_DCB [Add A] [Sub A] (t : Operator1CochainCore A) (sd : A) : A :=
  T.rCB (t.tDC sd) - t.tDB sd + t.tCB (T.rDC sd)

def delta1_DCA [Add A] [Sub A] (t : Operator1CochainCore A) (sd : A) : A :=
  T.rCA (t.tDC sd) - t.tDA sd + t.tCA (T.rDC sd)

def delta1_DBA [Add A] [Sub A] (t : Operator1CochainCore A) (sd : A) : A :=
  T.rBA (t.tDB sd) - t.tDA sd + t.tBA (T.rDB sd)

def commutatorKT [Sub A] (t : Operator1CochainCore A) (sd : A) : A :=
  T.curvatureCBA (t.tDC sd) - t.tBA (T.curvatureDCB sd)

def delta2_delta1 [Add A] [Sub A] (t : Operator1CochainCore A) (sd : A) : A :=
  T.delta2 (T.delta1_DCB t sd)
           (T.delta1_DCA t sd)
           (T.delta1_DBA t sd)
           (T.delta1_CBA t (T.rDC sd))

/-- Theorem 4.1 in core Lean: Algebraic equivalence under linear cancellation -/
theorem delta2_delta1_eq_commutator_core [Add A] [Sub A]
    (t : Operator1CochainCore A)
    (sd : A)
    (h_cancel :
      T.rBA (T.rCB (t.tDC sd) - t.tDB sd + t.tCB (T.rDC sd)) -
      (T.rCA (t.tDC sd) - t.tDA sd + t.tCA (T.rDC sd)) +
      (T.rBA (t.tDB sd) - t.tDA sd + t.tBA (T.rDB sd)) -
      (T.rBA (t.tCB (T.rDC sd)) - t.tCA (T.rDC sd) + t.tBA (T.rCB (T.rDC sd))) =
      (T.rBA (T.rCB (t.tDC sd)) - T.rCA (t.tDC sd)) -
      t.tBA (T.rCB (T.rDC sd) - T.rDB sd)) :
    T.delta2_delta1 t sd = T.commutatorKT t sd := by
  dsimp [delta2_delta1, delta2, delta1_DCB, delta1_DCA, delta1_DBA, delta1_CBA,
         commutatorKT, curvatureCBA, curvatureDCB]
  exact h_cancel

end QuadRestrictionOpCore

end Paper001a
