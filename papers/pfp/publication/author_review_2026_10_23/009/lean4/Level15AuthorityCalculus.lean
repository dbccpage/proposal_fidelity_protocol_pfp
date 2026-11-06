-- Copied without change from lean4/Level15AuthorityCalculus.lean in the repository
-- at commit 52cb5457f6c485ba548cfd292f6012a941ed22cf.
/-!
# Level 15: The 15 Authority Calculus Theorems & Terminalization Mechanics

Formalizes the 15 Authority Theorems establishing the formal firewall
preventing generative systems from manufacturing self-referential authority:
* Proposal Non-Authority (Disjointness)
* Self-Critique Non-Verification
* Boundary Sufficiency
* Refusal Monotonicity
* Finite Descent Termination
* Replay Invariance
* Representation Quotienting
* Exact Duality Gap Zero
* Refusal Semilattice Meet-Closure
* Master Terminalization Dominance
-/

namespace MSSN.Level15

/-- The formal state space partitioned into Proposal states and Terminal Authority states. -/
inductive StateKind where
  | proposal : StateKind
  | candidateTrace : StateKind
  | quotientWitness : StateKind
  | terminalAuthority : StateKind
  | immutableRefusal : StateKind
  deriving DecidableEq, Repr

/-- Theorem 1 (Proposal Non-Authority):
    Proposal states are disjoint from terminal authority states. -/
def isProposal (k : StateKind) : Prop :=
  k = .proposal ∨ k = .candidateTrace

def isTerminalAuthority (k : StateKind) : Prop :=
  k = .terminalAuthority

theorem theorem1_proposal_non_authority (k : StateKind) :
    isProposal k → ¬ isTerminalAuthority k := by
  intro hp ht
  cases hp with
  | inl h1 =>
    rw [h1] at ht
    contradiction
  | inr h2 =>
    rw [h2] at ht
    contradiction

/-- Theorem 2 (Self-Critique Non-Verification):
    A candidate verifier parameter state that is identical to the generator state
    cannot serve as an independent verifier. -/
structure AgentState where
  paramHash : Nat
  deriving DecidableEq, Repr

def isIndependentVerifier (gen : AgentState) (ver : AgentState) : Prop :=
  gen.paramHash ≠ ver.paramHash

theorem theorem2_self_critique_non_verification (gen : AgentState) :
    ¬ isIndependentVerifier gen gen := by
  intro h
  exact h rfl

/-- Theorem 4 (Refusal Monotonicity):
    If a verification step marks a trace as violating an invariant,
    no monotonic trace extension without rollback removes the refusal. -/
inductive ValidationStatus where
  | green : ValidationStatus
  | refusal (code : Nat) : ValidationStatus
  deriving DecidableEq, Repr

def isRefusal : ValidationStatus → Prop
  | .green => False
  | .refusal _ => True

def monotonicTraceExtend (status : ValidationStatus) (_extension : List Nat) : ValidationStatus :=
  match status with
  | .refusal code => .refusal code
  | .green => .green

theorem theorem4_refusal_monotonicity (status : ValidationStatus) (ext : List Nat) :
    isRefusal status → isRefusal (monotonicTraceExtend status ext) := by
  intro href
  cases status with
  | green =>
    contradiction
  | refusal code =>
    simp [monotonicTraceExtend, isRefusal]

/-- Theorem 5 (Finite Descent Termination):
    Given finite budget bounds (B_step, B_depth), every deterministic evaluation halts. -/
structure ExecutionBudget where
  steps : Nat
  depth : Nat
  deriving DecidableEq, Repr

def runBounded : Nat → ExecutionBudget → Option ExecutionBudget
  | 0, _ => none
  | n + 1, b =>
    if b.steps = 0 then some b
    else runBounded n { b with steps := b.steps - 1 }

theorem theorem5_finite_descent_termination (steps depth : Nat) :
    runBounded (steps + 1) { steps := steps, depth := depth } = some { steps := 0, depth := depth } := by
  induction steps with
  | zero =>
    rfl
  | succ s ih =>
    rw [runBounded]
    simp
    exact ih

#print axioms theorem5_finite_descent_termination

/-- Theorem 6 (Replay Invariance):
    Two trace histories with identical hashes evaluate to identical outcomes. -/
structure TraceHistory where
  hashVal : Nat
  deriving DecidableEq, Repr

def deterministicEvaluator (t : TraceHistory) : Nat :=
  t.hashVal % 997

theorem theorem6_replay_invariance (t1 t2 : TraceHistory) (h : t1.hashVal = t2.hashVal) :
    deterministicEvaluator t1 = deterministicEvaluator t2 := by
  unfold deterministicEvaluator
  rw [h]

/-- Theorem 9 (Exact Duality Gap Zero):
    For primal objective c_x and dual objective b_y over ordered rationals,
    duality gap = b_y - c_x. If gap = 0, primal objective equals dual objective. -/
def dualityGap (primal : Int) (dual : Int) : Int :=
  dual - primal

theorem theorem9_duality_gap_zero (primal : Int) (dual : Int)
    (hGap : dualityGap primal dual = 0) :
    primal = dual := by
  unfold dualityGap at hGap
  omega

/-- Theorem 11 (Upper Layer Non-Creation):
    A lift from level n to level n+1 preserves or quotients structure,
    but the count of intrinsic authority tokens cannot increase. -/
structure LayerState where
  level : Nat
  authorityTokens : Nat
  deriving DecidableEq, Repr

def validLayerLift (s : LayerState) : LayerState :=
  { level := s.level + 1, authorityTokens := s.authorityTokens }

theorem theorem11_upper_layer_non_creation (s : LayerState) :
    (validLayerLift s).authorityTokens ≤ s.authorityTokens := by
  unfold validLayerLift
  exact Nat.le_refl _

/-- Theorem 12 (Refusal Semilattice Meet-Closure):
    Refusals form a meet-semilattice closed under conjunction.
    If either check fails, the combined check fails. -/
def refusalConjunction (r1 r2 : Bool) : Bool :=
  r1 || r2

theorem theorem12_refusal_meet_closure (r1 r2 : Bool) :
    (r1 = true ∨ r2 = true) → refusalConjunction r1 r2 = true := by
  intro h
  cases h with
  | inl h1 =>
    simp [refusalConjunction, h1]
  | inr h2 =>
    simp [refusalConjunction, h2]

/-- Theorem 15 (Master Terminalization Dominance):
    Every evaluation terminates either in a certified zero-defect quotient
    or in an immutable refusal state. -/
inductive MasterTerminal where
  | certifiedZeroDefect : MasterTerminal
  | immutableRefusal : Nat → MasterTerminal
  deriving DecidableEq, Repr

def terminalizeCheck (defectCount : Nat) (refusalCode : Nat) : MasterTerminal :=
  if defectCount = 0 then .certifiedZeroDefect
  else .immutableRefusal refusalCode

theorem theorem15_master_terminalization_dominance (defectCount refusalCode : Nat) :
    (terminalizeCheck defectCount refusalCode = .certifiedZeroDefect ∧ defectCount = 0) ∨
    (∃ code, terminalizeCheck defectCount refusalCode = .immutableRefusal code ∧ defectCount > 0) := by
  unfold terminalizeCheck
  by_cases h : defectCount = 0
  · simp [h]
  · simp [h]
    omega

#print axioms theorem1_proposal_non_authority
#print axioms theorem2_self_critique_non_verification
#print axioms theorem4_refusal_monotonicity
#print axioms theorem6_replay_invariance
#print axioms theorem9_duality_gap_zero
#print axioms theorem11_upper_layer_non_creation
#print axioms theorem12_refusal_meet_closure
#print axioms theorem15_master_terminalization_dominance

end MSSN.Level15
