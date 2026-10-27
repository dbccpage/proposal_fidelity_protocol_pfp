import SLevel
/-!
# Paper 043, T5: eight-clause fidelity and detector adequacy

The legacy Lean kernel stores six string-valued fidelity fields.  The finite
records below reuse its actual `RawSeed` and `TypedPacket` carriers and add the
missing normalized-constraint field.  The eighth clause is replayed against
the packet's actual `AuthorityEffect` field.

This is a located implementation contract.  Equality on the legacy string
fields is intentionally stricter than, and does not formalize, every transform
or evidence-ceiling order used by the Rust validator.  Passing these checks
does not certify unrestricted natural-language intent, detector adequacy, or
authority.  The `NoAuthorityExpansion` result below is a field-level contract
projection, not a proof of a universal authority firewall.
-/

namespace PaperER007

open SnSymbolGameAndPackets

/-- The authoritative eight-clause vocabulary, in shipped validator order. -/
inductive FidelityClause where
  | TaskIdentity
  | ConstraintPreservation
  | ProtectedBoundary
  | TerminalTarget
  | EvidenceCeiling
  | OraclePolicy
  | AllowedTransforms
  | NoAuthorityExpansion
  deriving DecidableEq, Repr

/-- The ordered, exhaustive finite list of fidelity clauses. -/
def allFidelityClauses : List FidelityClause :=
  [ FidelityClause.TaskIdentity
  , FidelityClause.ConstraintPreservation
  , FidelityClause.ProtectedBoundary
  , FidelityClause.TerminalTarget
  , FidelityClause.EvidenceCeiling
  , FidelityClause.OraclePolicy
  , FidelityClause.AllowedTransforms
  , FidelityClause.NoAuthorityExpansion
  ]

theorem fidelity_clause_mem_all (clause : FidelityClause) :
    clause ∈ allFidelityClauses := by
  cases clause <;> simp [allFidelityClauses]

/-- Finite seed-side data.  `normalizedConstraints` supplies the shipped field
that is absent from the legacy six-field `RawSeed`. -/
structure FidelitySeed where
  raw : RawSeed
  normalizedConstraints : String
  deriving Repr

/-- Finite packet-side data, retaining the actual legacy `TypedPacket`. -/
structure FidelityPacket where
  typed : TypedPacket
  normalizedConstraints : String
  deriving Repr

namespace FidelityClause

/-- Proposition-level meaning of each finite replay clause in this Lean
binding. -/
def Holds (clause : FidelityClause)
    (seed : FidelitySeed) (packet : FidelityPacket) : Prop :=
  match clause with
  | TaskIdentity => packet.typed.taskIdentity = seed.raw.taskIdentity
  | ConstraintPreservation =>
      packet.normalizedConstraints = seed.normalizedConstraints
  | ProtectedBoundary =>
      packet.typed.protectedBoundary = seed.raw.protectedBoundary
  | TerminalTarget => packet.typed.terminalTarget = seed.raw.terminalTarget
  | EvidenceCeiling => packet.typed.evidenceCeiling = seed.raw.evidenceCeiling
  | OraclePolicy => packet.typed.oraclePolicy = seed.raw.oraclePolicy
  | AllowedTransforms =>
      packet.typed.allowedTransforms = seed.raw.allowedTransforms
  | NoAuthorityExpansion =>
      packet.typed.authorityEffect = AuthorityEffect.none

end FidelityClause

/-- Executable replay for one clause. -/
def replayFidelityClause
    (clause : FidelityClause) (seed : FidelitySeed)
    (packet : FidelityPacket) : Bool :=
  match clause with
  | FidelityClause.TaskIdentity =>
      decide (packet.typed.taskIdentity = seed.raw.taskIdentity)
  | FidelityClause.ConstraintPreservation =>
      decide (packet.normalizedConstraints = seed.normalizedConstraints)
  | FidelityClause.ProtectedBoundary =>
      decide (packet.typed.protectedBoundary = seed.raw.protectedBoundary)
  | FidelityClause.TerminalTarget =>
      decide (packet.typed.terminalTarget = seed.raw.terminalTarget)
  | FidelityClause.EvidenceCeiling =>
      decide (packet.typed.evidenceCeiling = seed.raw.evidenceCeiling)
  | FidelityClause.OraclePolicy =>
      decide (packet.typed.oraclePolicy = seed.raw.oraclePolicy)
  | FidelityClause.AllowedTransforms =>
      decide (packet.typed.allowedTransforms = seed.raw.allowedTransforms)
  | FidelityClause.NoAuthorityExpansion =>
      decide (packet.typed.authorityEffect = AuthorityEffect.none)

/-- Every named clause has an exact executable replay on the finite records. -/
theorem replay_fidelity_clause_iff
    (clause : FidelityClause) (seed : FidelitySeed)
    (packet : FidelityPacket) :
    replayFidelityClause clause seed packet = true ↔
      clause.Holds seed packet := by
  cases clause <;>
    simp [replayFidelityClause, FidelityClause.Holds]

/-- Full satisfaction is the conjunction of all eight shipped clauses. -/
def EightClauseFidelity (seed : FidelitySeed) (packet : FidelityPacket) : Prop :=
  FidelityClause.TaskIdentity.Holds seed packet ∧
    FidelityClause.ConstraintPreservation.Holds seed packet ∧
    FidelityClause.ProtectedBoundary.Holds seed packet ∧
    FidelityClause.TerminalTarget.Holds seed packet ∧
    FidelityClause.EvidenceCeiling.Holds seed packet ∧
    FidelityClause.OraclePolicy.Holds seed packet ∧
    FidelityClause.AllowedTransforms.Holds seed packet ∧
    FidelityClause.NoAuthorityExpansion.Holds seed packet

/-- Executable conjunction of the same eight checks. -/
def replayAllEightFidelity
    (seed : FidelitySeed) (packet : FidelityPacket) : Bool :=
  replayFidelityClause FidelityClause.TaskIdentity seed packet &&
    (replayFidelityClause FidelityClause.ConstraintPreservation seed packet &&
      (replayFidelityClause FidelityClause.ProtectedBoundary seed packet &&
        (replayFidelityClause FidelityClause.TerminalTarget seed packet &&
          (replayFidelityClause FidelityClause.EvidenceCeiling seed packet &&
            (replayFidelityClause FidelityClause.OraclePolicy seed packet &&
              (replayFidelityClause FidelityClause.AllowedTransforms seed packet &&
                replayFidelityClause FidelityClause.NoAuthorityExpansion seed packet))))))

theorem replay_all_eight_fidelity_iff
    (seed : FidelitySeed) (packet : FidelityPacket) :
    replayAllEightFidelity seed packet = true ↔
      EightClauseFidelity seed packet := by
  simp [replayAllEightFidelity, EightClauseFidelity,
    replayFidelityClause, FidelityClause.Holds]

/-- Claim-scoped detector adequacy is separate evidence.  The fields explicitly
record positive and negative controls, protected distinctions, and known blind
spots.  The fifth adequacy concern, rejection of constant detectors, is derived
from those controls below rather than assumed as certificate data. -/
structure DetectorAdequacy {Case : Type} (detector : Case → Bool) : Type where
  positiveControl : Case
  positiveControlPasses : detector positiveControl = true
  negativeControl : Case
  negativeControlFails : detector negativeControl = false
  protectedDistinctions : List (Case × Case)
  protectedDistinctionsSeparated :
    ∀ pair, pair ∈ protectedDistinctions →
      detector pair.1 ≠ detector pair.2
  knownBlindSpots : List (Case × Case)
  knownBlindSpotsRecorded :
    ∀ pair, pair ∈ knownBlindSpots →
      detector pair.1 = detector pair.2

/-- Positive and negative controls cannot both be met by a constant detector;
every adequacy certificate therefore rejects both constant verdict functions. -/
theorem detector_adequacy_rejects_constant_detectors
    {Case : Type} {detector : Case → Bool}
    (adequate : DetectorAdequacy detector) :
    ∀ verdict : Bool, detector ≠ fun _case => verdict := by
  intro verdict hConstant
  cases verdict with
  | false =>
      have hFalse : false = true :=
        (congrFun hConstant adequate.positiveControl).symm.trans
          adequate.positiveControlPasses
      cases hFalse
  | true =>
      have hTrue : true = false :=
        (congrFun hConstant adequate.negativeControl).symm.trans
          adequate.negativeControlFails
      cases hTrue

/-- A total detector that passes every input. -/
def constantPassDetector {Case : Type} : Case → Bool :=
  fun _case => true

theorem constant_pass_detector_is_total {Case : Type} :
    ∀ input : Case, ∃ output : Bool,
      constantPassDetector input = output := by
  intro input
  exact ⟨true, rfl⟩

/-- Totality is not adequacy: the required negative control rejects the
constant-pass detector. -/
theorem constant_pass_detector_not_adequate {Case : Type} :
    ¬ Nonempty (DetectorAdequacy
      (constantPassDetector (Case := Case))) := by
  rintro ⟨adequate⟩
  have hNegative := adequate.negativeControlFails
  change true = false at hNegative
  cases hNegative

/-- Even full eight-clause fidelity supplies no adequacy certificate for an
unrelated detector. -/
theorem eight_clause_fidelity_does_not_certify_constant_detector
    {Case : Type} (seed : FidelitySeed) (packet : FidelityPacket) :
    EightClauseFidelity seed packet →
      ¬ Nonempty (DetectorAdequacy
        (constantPassDetector (Case := Case))) := by
  intro _hFidelity
  exact constant_pass_detector_not_adequate
/-- Concrete finite seed for the fidelity/adequacy separation witness. -/
def finiteSeparationSeed : FidelitySeed :=
  { raw :=
      { taskIdentity := "paper043-bool-witness"
        protectedBoundary := "preserve-boundary"
        terminalTarget := "finite-separation"
        evidenceCeiling := "located-contract"
        oraclePolicy := "no-oracle"
        allowedTransforms := "identity" }
    normalizedConstraints := "normalized" }

/-- Matching packet satisfies the same finite fields without adding authority. -/
def finiteSeparationPacket : FidelityPacket :=
  { typed :=
      { taskIdentity := "paper043-bool-witness"
        protectedBoundary := "preserve-boundary"
        terminalTarget := "finite-separation"
        evidenceCeiling := "located-contract"
        oraclePolicy := "no-oracle"
        allowedTransforms := "identity"
        authorityEffect := AuthorityEffect.none }
    normalizedConstraints := "normalized" }

/-- Explicit finite separation: all eight fidelity clauses pass, while on the
finite case type Bool a constant-pass detector has no adequacy certificate. -/
theorem finite_bool_fidelity_adequacy_separation :
    EightClauseFidelity finiteSeparationSeed finiteSeparationPacket ∧
      ¬ Nonempty (DetectorAdequacy
        (constantPassDetector (Case := Bool))) := by
  constructor
  · simp [EightClauseFidelity, FidelityClause.Holds,
      finiteSeparationSeed, finiteSeparationPacket]
  · rintro ⟨adequate⟩
    exact detector_adequacy_rejects_constant_detectors adequate true rfl


/-- Contract projection only: the eighth replayed field records `none`.  This
does not derive an authority theory or prove the universal nonpromotion rule. -/
theorem eight_clause_fidelity_records_no_authority_expansion
    (seed : FidelitySeed) (packet : FidelityPacket)
    (hFidelity : EightClauseFidelity seed packet) :
    packet.typed.authorityEffect = AuthorityEffect.none :=
  hFidelity.2.2.2.2.2.2.2

#print axioms PaperER007.fidelity_clause_mem_all
#print axioms PaperER007.replay_fidelity_clause_iff
#print axioms PaperER007.replay_all_eight_fidelity_iff
#print axioms PaperER007.constant_pass_detector_is_total
#print axioms PaperER007.constant_pass_detector_not_adequate
#print axioms PaperER007.eight_clause_fidelity_does_not_certify_constant_detector
#print axioms PaperER007.eight_clause_fidelity_records_no_authority_expansion
#print axioms PaperER007.detector_adequacy_rejects_constant_detectors
#print axioms PaperER007.finite_bool_fidelity_adequacy_separation

end PaperER007
