import Mathlib.Tactic.Abel
import Mathlib.Tactic.Ring
import CohomologyClass

/-!
Paper PO-001 v2.0: Curved Operator Derivation Identity.

Formalizes Theorem 4.1:
  (delta_2 (delta_1 t))_{d, c, b, a} = [K, t]_{d, c, b, a}
                                      = K_{c, b, a} ∘ t_{d, c} - t_{b, a} ∘ K_{d, c, b}

Key formal results:
1. `delta2_delta1_eq_commutator`:
   The second coboundary composition delta_2(delta_1(t)) on an operator 1-cochain t
   evaluates identically to the operator commutator [K, t] on every quadruple
   a <= b <= c <= d and all section elements sd : A.
2. `delta2_delta1_zero_of_flat`:
   When the restriction system is flat on the lower and upper triples
   (K_cba = 0 and K_dcb = 0), the coboundary composition vanishes identically,
   recovering standard nilpotency delta_2(delta_1(t)) = 0.
3. `residual_identically_zero`:
   The algebraic residual delta_2(delta_1(t)) - [K, t] is identically zero for all sd : A.
-/

namespace Paper001a

universe u

namespace QuadRestrictionOp

variable {A : Type u} [AddCommGroup A] (T : QuadRestrictionOp A)

/-- Operator commutator [K, t]_{d, c, b, a}(sd) = K_cba(t_dc(sd)) - t_ba(K_dcb(sd)). -/
def commutatorKT (t : Operator1Cochain T) (sd : A) : A :=
  T.curvatureCBA (t.tDC sd) - t.tBA (T.curvatureDCB sd)

/-- Second operator coboundary composition delta_2(delta_1(t))(sd). -/
def delta2_delta1 (t : Operator1Cochain T) (sd : A) : A :=
  T.delta2 (T.delta1_DCB t sd)
           (T.delta1_DCA t sd)
           (T.delta1_DBA t sd)
           (T.delta1_CBA t (T.rDC sd))

/-- Theorem 4.1 — Curved Operator Derivation Identity.
    delta_2(delta_1(t))(sd) equals [K, t](sd) unconditionally for all sd : A. -/
theorem delta2_delta1_eq_commutator
    (t : Operator1Cochain T)
    (rBA_add : forall x y : A, T.rBA (x + y) = T.rBA x + T.rBA y)
    (tBA_sub : forall x y : A, t.tBA (x - y) = t.tBA x - t.tBA y)
    (sd : A) :
    T.delta2_delta1 t sd = T.commutatorKT t sd := by
  simp [delta2_delta1, commutatorKT, delta2,
        delta1_DCB, delta1_DCA, delta1_DBA, delta1_CBA,
        curvatureCBA, curvatureDCB]
  rw [rBA_add, T.rBA_sub, tBA_sub]
  abel

/-- Corollary 4.1a — Nilpotency on Flat Systems.
    When both the lower triple (c, b, a) and upper triple (d, c, b) are flat,
    delta_2(delta_1(t))(sd) vanishes identically. -/
theorem delta2_delta1_zero_of_flat
    (t : Operator1Cochain T)
    (rBA_add : forall x y : A, T.rBA (x + y) = T.rBA x + T.rBA y)
    (tBA_sub : forall x y : A, t.tBA (x - y) = t.tBA x - t.tBA y)
    (tBA_zero : t.tBA 0 = 0)
    (h_cba_flat : forall sc, T.curvatureCBA sc = 0)
    (h_dcb_flat : forall sd, T.curvatureDCB sd = 0)
    (sd : A) :
    T.delta2_delta1 t sd = 0 := by
  rw [T.delta2_delta1_eq_commutator t rBA_add tBA_sub sd]
  dsimp [commutatorKT]
  rw [h_cba_flat (t.tDC sd)]
  rw [h_dcb_flat sd]
  rw [tBA_zero]
  abel

/-- Corollary 4.1b — Vanishing Algebraic Residual.
    delta_2(delta_1(t))(sd) - [K, t](sd) = 0 identically for all sd : A. -/
theorem residual_identically_zero
    (t : Operator1Cochain T)
    (rBA_add : forall x y : A, T.rBA (x + y) = T.rBA x + T.rBA y)
    (tBA_sub : forall x y : A, t.tBA (x - y) = t.tBA x - t.tBA y)
    (sd : A) :
    T.delta2_delta1 t sd - T.commutatorKT t sd = 0 := by
  rw [T.delta2_delta1_eq_commutator t rBA_add tBA_sub sd]
  abel

end QuadRestrictionOp

end Paper001a
