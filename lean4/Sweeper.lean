import SLevel
/-!
Omega Sweeper and Symbol Game authority/firewall kernels.

These theorems model the contract-level facts used by the paper: certificate
status is gated, append-only lanes are monotone in their own counters, and the
Symbol Game operation signature has no authority output color.
-/

namespace SnSymbolGameAndPackets

structure GatePacket where
  strictClean : Bool
  survivorVerdict : Bool
  witnessNonempty : Bool
  authorBlind : Bool
  deriving Repr

inductive HostTerminal where
  | certificate
  | refusal
  | oracleNeeded
  deriving DecidableEq, Repr

def Certifiable (p : GatePacket) : Prop :=
  p.strictClean = true ∧
    p.survivorVerdict = true ∧
    p.witnessNonempty = true ∧
    p.authorBlind = true

def hostTerminalize (p : GatePacket) : HostTerminal :=
  if p.strictClean && p.survivorVerdict && p.witnessNonempty && p.authorBlind then
    HostTerminal.certificate
  else
    HostTerminal.refusal

theorem certificate_requires_all_gates (p : GatePacket) :
    hostTerminalize p = HostTerminal.certificate → Certifiable p := by
  cases p with
  | mk strict survivor witness blind =>
      cases strict <;> cases survivor <;> cases witness <;> cases blind <;>
        intro hCert
      all_goals try cases hCert
      exact ⟨rfl, rfl, rfl, rfl⟩

theorem no_certificate_without_witness
    (p : GatePacket) (hWitness : p.witnessNonempty = false) :
    hostTerminalize p ≠ HostTerminal.certificate := by
  intro hCert
  have hGates := certificate_requires_all_gates p hCert
  have hWitnessTrue := hGates.2.2.1
  rw [hWitness] at hWitnessTrue
  cases hWitnessTrue

theorem no_certificate_without_author_blind_gate
    (p : GatePacket) (hAuthorBlind : p.authorBlind = false) :
    hostTerminalize p ≠ HostTerminal.certificate := by
  intro hCert
  have hGates := certificate_requires_all_gates p hCert
  have hAuthorBlindTrue := hGates.2.2.2
  rw [hAuthorBlind] at hAuthorBlindTrue
  cases hAuthorBlindTrue

structure SweepLedger where
  survived : Nat
  killed : Nat
  obligations : Nat
  deriving Repr

def appendSurvived (L : SweepLedger) : SweepLedger :=
  { L with survived := L.survived + 1 }

def appendKilled (L : SweepLedger) : SweepLedger :=
  { L with killed := L.killed + 1 }

def appendObligation (L : SweepLedger) : SweepLedger :=
  { L with obligations := L.obligations + 1 }

theorem append_survived_monotone (L : SweepLedger) :
    L.survived ≤ (appendSurvived L).survived := by
  change L.survived ≤ L.survived + 1
  exact Nat.le_succ L.survived

theorem append_killed_monotone (L : SweepLedger) :
    L.killed ≤ (appendKilled L).killed := by
  change L.killed ≤ L.killed + 1
  exact Nat.le_succ L.killed

theorem append_obligation_monotone (L : SweepLedger) :
    L.obligations ≤ (appendObligation L).obligations := by
  change L.obligations ≤ L.obligations + 1
  exact Nat.le_succ L.obligations

theorem append_survived_preserves_killed (L : SweepLedger) :
    (appendSurvived L).killed = L.killed :=
  rfl

theorem append_killed_preserves_obligations (L : SweepLedger) :
    (appendKilled L).obligations = L.obligations :=
  rfl

inductive SymbolColor where
  | raw
  | packet
  | trace
  | evidence
  | operator
  | terminal
  deriving DecidableEq, Repr

inductive ExtendedColor where
  | symbol : SymbolColor → ExtendedColor
  | authority
  deriving DecidableEq, Repr

inductive SgOperation where
  | parse
  | fidelity
  | replay
  | verify
  | discover
  | applyOperator
  | constrain
  | expand
  deriving DecidableEq, Repr

def operationOutput : SgOperation → ExtendedColor
  | SgOperation.parse => ExtendedColor.symbol SymbolColor.packet
  | SgOperation.fidelity => ExtendedColor.symbol SymbolColor.terminal
  | SgOperation.replay => ExtendedColor.symbol SymbolColor.trace
  | SgOperation.verify => ExtendedColor.symbol SymbolColor.terminal
  | SgOperation.discover => ExtendedColor.symbol SymbolColor.operator
  | SgOperation.applyOperator => ExtendedColor.symbol SymbolColor.trace
  | SgOperation.constrain => ExtendedColor.symbol SymbolColor.packet
  | SgOperation.expand => ExtendedColor.symbol SymbolColor.operator

theorem operation_output_not_authority (op : SgOperation) :
    operationOutput op ≠ ExtendedColor.authority := by
  cases op <;> intro h <;> cases h

inductive OperationTree where
  | node : SgOperation → Option OperationTree → OperationTree

def treeOutput : OperationTree → ExtendedColor
  | OperationTree.node op _child => operationOutput op

theorem operation_tree_output_not_authority (tree : OperationTree) :
    treeOutput tree ≠ ExtendedColor.authority := by
  cases tree with
  | node op child =>
      exact operation_output_not_authority op

#print axioms SnSymbolGameAndPackets.certificate_requires_all_gates
#print axioms SnSymbolGameAndPackets.no_certificate_without_witness
#print axioms SnSymbolGameAndPackets.no_certificate_without_author_blind_gate
#print axioms SnSymbolGameAndPackets.append_survived_monotone
#print axioms SnSymbolGameAndPackets.append_killed_monotone
#print axioms SnSymbolGameAndPackets.append_obligation_monotone
#print axioms SnSymbolGameAndPackets.operation_output_not_authority
#print axioms SnSymbolGameAndPackets.operation_tree_output_not_authority

-- Not declared, so not mechanized: formal_replay_remains_non_authority

end SnSymbolGameAndPackets
