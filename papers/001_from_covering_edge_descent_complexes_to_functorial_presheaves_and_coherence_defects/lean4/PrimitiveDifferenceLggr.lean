import PrimitiveDifference
import CurvatureCochain

/-!
Paper PO-001 PrimitiveDifference / LGGR boundary.

Payload-only primitive quotienting is safe for local payload observations. It is
not safe for curvature observations unless curvature is also preserved. This is
the finite EPK reading of the Paper PO-001 slogan: local green does not imply
global red has disappeared.
-/

namespace Paper001a

open OmegaCore

universe u v

structure CurvaturePacket (Payload : Type u) (Curv : Type v) where
  payload : Payload
  curvature : Curv

def payloadPrimitiveDifference
    (Payload : Type u) (Curv : Type v) :
    PrimitiveDifference
      (CurvaturePacket Payload Curv)
      (Payload × Payload) where
  δ := fun x y => (x.payload, y.payload)
  Zero := fun pair => pair.1 = pair.2
  zero_refl := by
    intro x
    rfl
  zero_symm := by
    intro x y hxy
    exact hxy.symm
  zero_trans := by
    intro x y z hxy hyz
    exact hxy.trans hyz

def payloadCurvaturePrimitiveDifference
    (Payload : Type u) (Curv : Type v) :
    PrimitiveDifference
      (CurvaturePacket Payload Curv)
      ((Payload × Curv) × (Payload × Curv)) where
  δ := fun x y => ((x.payload, x.curvature), (y.payload, y.curvature))
  Zero := fun pair => pair.1 = pair.2
  zero_refl := by
    intro x
    rfl
  zero_symm := by
    intro x y hxy
    exact hxy.symm
  zero_trans := by
    intro x y z hxy hyz
    exact hxy.trans hyz

def packetPayload
    {Payload : Type u} {Curv : Type v}
    (p : CurvaturePacket Payload Curv) : Payload :=
  p.payload

def packetCurvature
    {Payload : Type u} {Curv : Type v}
    (p : CurvaturePacket Payload Curv) : Curv :=
  p.curvature

theorem payload_relation_ignores_curvature
    {Payload : Type u} {Curv : Type v}
    (payload : Payload) (k l : Curv) :
    (payloadPrimitiveDifference Payload Curv).ZeroRel
      ({ payload := payload, curvature := k } :
        CurvaturePacket Payload Curv)
      ({ payload := payload, curvature := l } :
        CurvaturePacket Payload Curv) := by
  rfl

theorem payload_classifier_invariant
    {Payload : Type u} {Curv : Type v} :
    (payloadPrimitiveDifference Payload Curv).InvariantCongruent
      (packetPayload (Payload := Payload) (Curv := Curv)) := by
  intro x y hxy
  exact hxy

theorem payload_classifier_factors
    {Payload : Type u} {Curv : Type v} :
    exists F :
        (payloadPrimitiveDifference Payload Curv).ResidualQuotient -> Payload,
      forall p : CurvaturePacket Payload Curv,
        F ((payloadPrimitiveDifference Payload Curv).classOf p) =
          packetPayload p := by
  exact
    (PrimitiveDifference.invariantFactor_exists_iff_invariantCongruent
      (payloadPrimitiveDifference Payload Curv)
      (packetPayload (Payload := Payload) (Curv := Curv))).mpr
      (payload_classifier_invariant (Payload := Payload) (Curv := Curv))

theorem curvature_classifier_not_invariant_when_curvature_differs
    {Payload : Type u} {Curv : Type v}
    (payload : Payload) {k l : Curv} (hne : k ≠ l) :
    Not (
      (payloadPrimitiveDifference Payload Curv).InvariantCongruent
        (packetCurvature (Payload := Payload) (Curv := Curv))) := by
  intro hcongr
  let x : CurvaturePacket Payload Curv := { payload := payload, curvature := k }
  let y : CurvaturePacket Payload Curv := { payload := payload, curvature := l }
  have hxy : (payloadPrimitiveDifference Payload Curv).ZeroRel x y :=
    payload_relation_ignores_curvature payload k l
  exact hne (hcongr x y hxy)

theorem curvature_not_factor_through_payload_quotient
    {Payload : Type u} {Curv : Type v}
    (payload : Payload) {k l : Curv} (hne : k ≠ l) :
    Not (exists F :
        (payloadPrimitiveDifference Payload Curv).ResidualQuotient -> Curv,
      forall p : CurvaturePacket Payload Curv,
        F ((payloadPrimitiveDifference Payload Curv).classOf p) =
          packetCurvature p) := by
  exact
    PrimitiveDifference.invariantFactor_no_factor_of_not_invariant
      (payloadPrimitiveDifference Payload Curv)
      (packetCurvature (Payload := Payload) (Curv := Curv))
      (curvature_classifier_not_invariant_when_curvature_differs
        (Payload := Payload) (Curv := Curv) payload hne)

theorem payload_green_curvature_red
    {Payload : Type u} {Curv : Type v}
    (payload : Payload) {k l : Curv} (hne : k ≠ l) :
    (exists F :
        (payloadPrimitiveDifference Payload Curv).ResidualQuotient -> Payload,
      forall p : CurvaturePacket Payload Curv,
        F ((payloadPrimitiveDifference Payload Curv).classOf p) =
          packetPayload p) /\
      Not (exists F :
        (payloadPrimitiveDifference Payload Curv).ResidualQuotient ->
          Payload × Curv,
      forall p : CurvaturePacket Payload Curv,
        F ((payloadPrimitiveDifference Payload Curv).classOf p) =
          (packetPayload p, packetCurvature p)) := by
  let P := payloadPrimitiveDifference Payload Curv
  let x : CurvaturePacket Payload Curv := { payload := payload, curvature := k }
  let y : CurvaturePacket Payload Curv := { payload := payload, curvature := l }
  have hxy : P.ZeroRel x y := by
    rfl
  constructor
  · exact payload_classifier_factors (Payload := Payload) (Curv := Curv)
  · intro hFactor
    rcases hFactor with ⟨F, hF⟩
    have hcongr :
        P.InvariantCongruent
          (fun p : CurvaturePacket Payload Curv =>
            (packetPayload p, packetCurvature p)) :=
      PrimitiveDifference.invariantFactor_requires_congruence
        P
        (fun p : CurvaturePacket Payload Curv =>
          (packetPayload p, packetCurvature p))
        F
        hF
    exact hne (congrArg Prod.snd (hcongr x y hxy))

theorem curvature_invariant_when_preserved
    {Payload : Type u} {Curv : Type v} :
    (payloadCurvaturePrimitiveDifference Payload Curv).InvariantCongruent
      (packetCurvature (Payload := Payload) (Curv := Curv)) := by
  intro x y hxy
  exact congrArg Prod.snd hxy

theorem curvature_factors_when_preserved
    {Payload : Type u} {Curv : Type v} :
    exists F :
        (payloadCurvaturePrimitiveDifference Payload Curv).ResidualQuotient ->
          Curv,
      forall p : CurvaturePacket Payload Curv,
        F ((payloadCurvaturePrimitiveDifference Payload Curv).classOf p) =
          packetCurvature p := by
  exact
    (PrimitiveDifference.invariantFactor_exists_iff_invariantCongruent
      (payloadCurvaturePrimitiveDifference Payload Curv)
      (packetCurvature (Payload := Payload) (Curv := Curv))).mpr
      (curvature_invariant_when_preserved
        (Payload := Payload) (Curv := Curv))

end Paper001a
