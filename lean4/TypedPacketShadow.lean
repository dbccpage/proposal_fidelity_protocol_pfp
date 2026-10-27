import SLevel
/-!
# Paper 043, T3: typed-packet shadow collision

This file replaces the older `Unit` packet-shape example with an obstruction
whose shadow really has type `SnSymbolGameAndPackets.TypedPacket`.

The scope is deliberately existential: the finite instance below shows that
one declared packet projection omits one declared target distinction.  It does
not say that every typed packet forgets semantic truth, or that a richer packet
cannot carry the target.
-/

namespace PaperER007

open SnSymbolGameAndPackets

/-- A collision in an actual `TypedPacket` projection prevents a decoder from
recovering a target value on every source state. -/
theorem no_typed_packet_decoder_of_collision
    {Source Value : Type}
    (packetOf : Source → TypedPacket)
    (value : Source → Value)
    (a b : Source)
    (hPacket : packetOf a = packetOf b)
    (hValue : value a ≠ value b) :
    ¬ ∃ decode : TypedPacket → Value,
        ∀ source, decode (packetOf source) = value source := by
  intro hDecoder
  rcases hDecoder with ⟨decode, hDecode⟩
  apply hValue
  calc
    value a = decode (packetOf a) := (hDecode a).symm
    _ = decode (packetOf b) := congrArg decode hPacket
    _ = value b := hDecode b

/-- Two finite source states differing only in an intentionally unrepresented
target value. -/
inductive FinitePacketSource where
  | targetFalse
  | targetTrue
  deriving DecidableEq, Repr

/-- The finite projection.  Both sources produce this same concrete
`TypedPacket`; its fields are declared data rather than the former `Unit` toy
shadow. -/
def finiteCollisionPacket (_source : FinitePacketSource) : TypedPacket :=
  { taskIdentity := "paper043-finite-packet-collision"
    protectedBoundary := "declared-boundary"
    terminalTarget := "diagnostic-only"
    evidenceCeiling := "finite-replay"
    oraclePolicy := "no-oracle"
    allowedTransforms := "none"
    authorityEffect := AuthorityEffect.none }

/-- The target deliberately omitted by `finiteCollisionPacket`. -/
def finiteCollisionValue : FinitePacketSource → Bool
  | FinitePacketSource.targetFalse => false
  | FinitePacketSource.targetTrue => true

theorem finite_typed_packet_projection_collides :
    finiteCollisionPacket FinitePacketSource.targetFalse =
      finiteCollisionPacket FinitePacketSource.targetTrue :=
  rfl

theorem finite_typed_packet_targets_differ :
    finiteCollisionValue FinitePacketSource.targetFalse ≠
      finiteCollisionValue FinitePacketSource.targetTrue := by
  decide

/-- A finite, actual-`TypedPacket` decoder obstruction.  This theorem is only
about `finiteCollisionPacket`, not about all possible packet projections. -/
theorem finite_typed_packet_collision_blocks_total_decoder :
    ¬ ∃ decode : TypedPacket → Bool,
        ∀ source,
          decode (finiteCollisionPacket source) = finiteCollisionValue source :=
  no_typed_packet_decoder_of_collision
    finiteCollisionPacket
    finiteCollisionValue
    FinitePacketSource.targetFalse
    FinitePacketSource.targetTrue
    finite_typed_packet_projection_collides
    finite_typed_packet_targets_differ

#print axioms PaperER007.no_typed_packet_decoder_of_collision
#print axioms PaperER007.finite_typed_packet_projection_collides
#print axioms PaperER007.finite_typed_packet_targets_differ
#print axioms PaperER007.finite_typed_packet_collision_blocks_total_decoder

end PaperER007
