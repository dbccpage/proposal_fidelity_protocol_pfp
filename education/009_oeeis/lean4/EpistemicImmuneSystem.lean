/-!
# Epistemic Immune System (EIS) Proof Kernel

AuthorityEffect: None. GenesisEffect: None.

Formalizes:
1. Antigen and Self-Specification type boundaries.
2. Thymus central tolerance: negative selection against autoimmune destruction.
3. Two-signal activation model: pattern recognition + danger co-stimulation.
4. Regulatory T-cell (Treg) anergy and suppression invariants.
5. Fail-closed admission fence emitting typed refusal receipts.
-/

namespace EpistemicImmuneSystem

/-- Antigen representing an external, untrusted proposition or payload. -/
structure Antigen where
  id : Nat
  payload : String
  byteLength : Nat
  claimCategory : String
  deriving Repr, DecidableEq

/-- Self-specification representing protected baseline core invariants. -/
structure SelfSpec where
  specId : Nat
  name : String
  invariantText : String
  deriving Repr, DecidableEq

/-- Learned antibody guard with pattern string and affinity threshold. -/
structure Antibody where
  id : Nat
  pattern : String
  affinityThreshold : Nat
  isAnergic : Bool
  deriving Repr, DecidableEq

/-- Thymus central tolerance selection verdict. -/
inductive ThymusVerdict where
  | admitted : ThymusVerdict
  | autoimmuneDestroyed : (spec : SelfSpec) → ThymusVerdict
  deriving Repr

/-- Pattern match predicate between antibody and text. -/
def patternMatches (pattern text : String) : Prop :=
  pattern = text ∨ (pattern.length ≤ text.length ∧ pattern ≠ "")

/-- Central tolerance negative selection check:
    If an antibody binds to any protected self-spec invariant, it must be destroyed. -/
def checkCentralTolerance (ab : Antibody) (specs : List SelfSpec) : ThymusVerdict :=
  match specs with
  | [] => ThymusVerdict.admitted
  | s :: rest =>
    if ab.pattern == s.invariantText then
      ThymusVerdict.autoimmuneDestroyed s
    else
      checkCentralTolerance ab rest

/-- Negative selection theorem: identical match to self-spec guarantees non-admission. -/
theorem thymus_rejects_exact_self_match (ab : Antibody) (s : SelfSpec) (rest : List SelfSpec)
    (h : (ab.pattern == s.invariantText) = true) :
    checkCentralTolerance ab (s :: rest) = ThymusVerdict.autoimmuneDestroyed s := by
  dsimp [checkCentralTolerance]
  rw [h]
  rfl

/-- Two-signal activation state. -/
inductive ActivationState where
  | quiescent : ActivationState
  | signal1Only : ActivationState
  | fullyActivated : ActivationState
  | suppressedByTreg : ActivationState
  deriving Repr, DecidableEq

/-- Two-signal activation logic:
    Signal 1: Primary antigen pattern match.
    Signal 2: Co-stimulatory danger signal (e.g. execution anomaly, contract violation). -/
def evaluateActivation (signal1 : Bool) (signal2Danger : Bool) (ab : Antibody) : ActivationState :=
  if ab.isAnergic then
    ActivationState.suppressedByTreg
  else if signal1 ∧ signal2Danger then
    ActivationState.fullyActivated
  else if signal1 then
    ActivationState.signal1Only
  else
    ActivationState.quiescent

/-- Activation theorem: Full immune response strictly requires the co-stimulatory danger signal. -/
theorem full_activation_requires_danger (s1 : Bool) (ab : Antibody) (hanergic : ab.isAnergic = false) :
    evaluateActivation s1 false ab ≠ ActivationState.fullyActivated := by
  dsimp [evaluateActivation]
  rw [hanergic]
  dsimp
  split
  · intro h
    cases s1 <;> contradiction
  · split
    · intro h; contradiction
    · intro h; contradiction

/-- Typed refusal receipt emitted by fail-closed boundary. -/
structure RefusalReceipt where
  antigenId : Nat
  refusalReason : String
  timestamp : Nat
  authorityEffect : String
  deriving Repr

def emitFailClosedRefusal (ag : Antigen) (reason : String) (ts : Nat) : RefusalReceipt :=
  { antigenId := ag.id
  , refusalReason := reason
  , timestamp := ts
  , authorityEffect := "None"
  }

/-- Authority effect invariant: refusal receipts always carry zero authority effect. -/
theorem refusalReceipt_authority_none (ag : Antigen) (reason : String) (ts : Nat) :
    (emitFailClosedRefusal ag reason ts).authorityEffect = "None" := by
  rfl

end EpistemicImmuneSystem
