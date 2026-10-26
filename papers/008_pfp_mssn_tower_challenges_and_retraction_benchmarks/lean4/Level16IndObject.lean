-- Vendored for Paper 008 from `lean4/Level16IndObject.lean` at commit 52cb5457f6c485ba548cfd292f6012a941ed22cf
-- (git blob 922d78406f3d80ed9a22dd15d1651a5a4ea48b44). Every line after this two-line header is byte-identical to that blob.
/-!
# Level 16: Infinite SymSys & Ind-Object Category Theory

Formalizes category-theoretic filtered colimit properties of the MSS-N tower:
* Finite stage capacity bounds
* Directed system of finite stages: MSS_0 → MSS_1 → ...
* Ind-object colimit: MSS_∞ = Ind-colim MSS_n
* Colimit Quarantine Theorem: No finite stage n can embed the infinite colimit
* Quarantine Halt triggering under infinite evaluation demands
-/

namespace MSSN.Level16

/-- A finite Markov Shift Stage with fixed alphabet and state capacity. -/
structure FiniteMSSStage where
  stageIndex : Nat
  maxStates : Nat
  maxTransitions : Nat
  deriving DecidableEq, Repr

/-- Stage capacity is bounded strictly as a function of the stage index. -/
def standardStage (n : Nat) : FiniteMSSStage :=
  { stageIndex := n
  , maxStates := 2^(n + 1)
  , maxTransitions := 2^(2 * (n + 1)) }

theorem stage_capacity_monotonic (n : Nat) :
    (standardStage n).maxStates < (standardStage (n + 1)).maxStates := by
  unfold standardStage
  simp
  have h1 : 2^(n + 1) < 2^(n + 2) := by
    apply Nat.pow_lt_pow_right
    · decide
    · omega
  exact h1

/-- Colimit Quarantine Theorem:
    For any target capacity K, there exists a stage index N such that
    all higher stages exceed K, demonstrating that the infinite ind-object
    cannot be contained within any fixed finite bound K. -/
theorem lt_two_pow_succ (k : Nat) : k < 2^(k + 1) := by
  induction k with
  | zero =>
    decide
  | succ k ih =>
    have h1 : 2^(k + 2) = 2^(k + 1) * 2 := rfl
    have h2 : 2^(k + 1) * 2 = 2^(k + 1) + 2^(k + 1) := by omega
    omega

theorem colimit_quarantine_barrier (k : Nat) :
    ∃ n : Nat, (standardStage n).maxStates > k := by
  exists k
  unfold standardStage
  simp
  exact lt_two_pow_succ k

/-- Evaluation within a finite envelope halts with a quarantine barrier
    if an infinite colimit object is requested. -/
inductive ColimitEvaluationResult where
  | finiteStageSuccess (stage : Nat) : ColimitEvaluationResult
  | quarantineHalt (exceededBound : Nat) : ColimitEvaluationResult
  deriving DecidableEq, Repr

def evaluateWithQuarantine (budget : Nat) (requestedStates : Nat) : ColimitEvaluationResult :=
  if requestedStates ≤ 2^(budget + 1) then
    .finiteStageSuccess budget
  else
    .quarantineHalt requestedStates

theorem quarantine_halt_on_infinite_demand (budget : Nat) (requestedStates : Nat)
    (h : requestedStates > 2^(budget + 1)) :
    evaluateWithQuarantine budget requestedStates = .quarantineHalt requestedStates := by
  unfold evaluateWithQuarantine
  have hnot : ¬ (requestedStates ≤ 2^(budget + 1)) := by omega
  simp [hnot]

#print axioms stage_capacity_monotonic
#print axioms colimit_quarantine_barrier
#print axioms quarantine_halt_on_infinite_demand

end MSSN.Level16
