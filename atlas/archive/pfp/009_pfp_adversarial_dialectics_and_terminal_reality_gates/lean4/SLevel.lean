-- Copied without change from lean4/SLevel.lean in the repository
-- at commit 52cb5457f6c485ba548cfd292f6012a941ed22cf.
/-!
Finite S(n), packetization, and forgetfulness kernels for the Symbol Game /
packetization paper.

The file deliberately proves narrow contract facts. It does not assert that an
arbitrary natural-language prompt has been faithfully captured by a packet.
-/

namespace SnSymbolGameAndPackets

inductive AuthorityEffect where
  | none
  | claimed
  deriving DecidableEq, Repr

structure SLevel where
  n : Nat
  symbols : Nat
  operators : Nat
  packetFamilies : Nat
  witnesses : Nat
  liftBudget : Nat
  deriving Repr

def SLevel.declaredMass (S : SLevel) : Nat :=
  S.symbols + S.operators + S.packetFamilies + S.witnesses

structure LicensedLift (source target : SLevel) where
  level_step : target.n = source.n + 1
  budget_drops : target.liftBudget < source.liftBudget
  declares_new_structure : source.declaredMass < target.declaredMass

theorem licensed_lift_forces_next_level
    (source target : SLevel) (lift : LicensedLift source target) :
    target.n = source.n + 1 :=
  lift.level_step

theorem licensed_lift_consumes_budget
    (source target : SLevel) (lift : LicensedLift source target) :
    target.liftBudget < source.liftBudget :=
  lift.budget_drops

theorem licensed_lift_not_silent_on_declared_structure
    (source target : SLevel) (lift : LicensedLift source target) :
    source.declaredMass ≠ target.declaredMass := by
  intro hsame
  have hdecl := lift.declares_new_structure
  rw [hsame] at hdecl
  exact Nat.lt_irrefl target.declaredMass hdecl

structure RawSeed where
  taskIdentity : String
  protectedBoundary : String
  terminalTarget : String
  evidenceCeiling : String
  oraclePolicy : String
  allowedTransforms : String
  deriving Repr

structure TypedPacket where
  taskIdentity : String
  protectedBoundary : String
  terminalTarget : String
  evidenceCeiling : String
  oraclePolicy : String
  allowedTransforms : String
  authorityEffect : AuthorityEffect
  deriving Repr

def Fidelity (seed : RawSeed) (packet : TypedPacket) : Prop :=
  packet.taskIdentity = seed.taskIdentity ∧
    packet.protectedBoundary = seed.protectedBoundary ∧
    packet.terminalTarget = seed.terminalTarget ∧
    packet.evidenceCeiling = seed.evidenceCeiling ∧
    packet.oraclePolicy = seed.oraclePolicy ∧
    packet.allowedTransforms = seed.allowedTransforms

structure PacketizationContract where
  compile : RawSeed → Option TypedPacket
  sound :
    ∀ seed packet,
      compile seed = some packet →
        Fidelity seed packet ∧ packet.authorityEffect = AuthorityEffect.none

theorem packetization_contract_preserves_fidelity
    (C : PacketizationContract) (seed : RawSeed) (packet : TypedPacket)
    (hCompile : C.compile seed = some packet) :
    Fidelity seed packet :=
  (C.sound seed packet hCompile).1

theorem packetization_contract_no_authority
    (C : PacketizationContract) (seed : RawSeed) (packet : TypedPacket)
    (hCompile : C.compile seed = some packet) :
    packet.authorityEffect = AuthorityEffect.none :=
  (C.sound seed packet hCompile).2

inductive PromptWorld where
  | faithful
  | silentMutation
  deriving DecidableEq, Repr

def packetShape (_world : PromptWorld) : Unit :=
  ()

def semanticTruth : PromptWorld → Bool
  | PromptWorld.faithful => true
  | PromptWorld.silentMutation => false

theorem packet_shape_forgets_semantic_truth :
    ¬ ∃ F : Unit → Bool,
        ∀ world : PromptWorld, F (packetShape world) = semanticTruth world := by
  intro h
  rcases h with ⟨F, hF⟩
  have hFaithful := hF PromptWorld.faithful
  have hMutation := hF PromptWorld.silentMutation
  change F () = true at hFaithful
  change F () = false at hMutation
  rw [hFaithful] at hMutation
  cases hMutation

#print axioms SnSymbolGameAndPackets.licensed_lift_forces_next_level
#print axioms SnSymbolGameAndPackets.licensed_lift_consumes_budget
#print axioms SnSymbolGameAndPackets.licensed_lift_not_silent_on_declared_structure
#print axioms SnSymbolGameAndPackets.packetization_contract_preserves_fidelity
#print axioms SnSymbolGameAndPackets.packetization_contract_no_authority
#print axioms SnSymbolGameAndPackets.packet_shape_forgets_semantic_truth

end SnSymbolGameAndPackets
