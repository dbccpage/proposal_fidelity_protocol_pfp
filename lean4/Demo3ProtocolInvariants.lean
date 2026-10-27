import Std.Tactic

/-!
# Finite Demo 3 Protocol Model

The fuel bound applies to the explicit valid-trace relation below. It is not a
verification of the Python runner. The arithmetic mixer is a toy function with
a displayed collision, not a cryptographic hash or a security argument.
HostCertificate records an assumed host Boolean; it does not implement an oracle.

AuthorityEffect: None.
-/

namespace MSSN.Demo3Protocol

/-- Protocol lifecycle phases. -/
inductive Phase where
  | intake
  | coverage
  | witness
  | verify
  | terminal
  deriving DecidableEq, Repr

/-- Protocol terminal exit statuses. -/
inductive ExitStatus where
  | scopedCertificate
  | rejectLocal
  | needsEvidence
  | unknownNotCertified
  | fuelExhausted
  deriving DecidableEq, Repr

/-- Protocol execution state at step n. -/
structure ExecutionState where
  stepIndex : Nat
  remainingFuel : Nat
  phase : Phase
  stateDigest : Nat
  deriving DecidableEq, Repr

/-- Monotonic Fuel Step Invariant:
    Every execution step consumes at least 1 unit of fuel until exhaustion. -/
def validStepTransition (before_st after_st : ExecutionState) : Prop :=
  before_st.remainingFuel > 0 ∧
  after_st.remainingFuel = before_st.remainingFuel - 1 ∧
  after_st.stepIndex = before_st.stepIndex + 1

/-- Monotonic fuel decrease theorem. -/
theorem fuel_strictly_decreases (s1 s2 : ExecutionState) (h_trans : validStepTransition s1 s2) :
    s2.remainingFuel < s1.remainingFuel := by
  rcases h_trans with ⟨h_pos, h_fuel, _⟩
  rw [h_fuel]
  exact Nat.sub_lt h_pos (by decide)

/-- An explicit finite chain of valid step transitions. -/
inductive ValidTrace : ExecutionState → Nat → ExecutionState → Prop where
  | nil (s : ExecutionState) : ValidTrace s 0 s
  | cons {first middle last : ExecutionState} {n : Nat}
      (step : validStepTransition first middle)
      (tail : ValidTrace middle n last) : ValidTrace first (n + 1) last

/-- Every valid transition chain of length k consumes exactly k units of fuel. -/
theorem trace_fuel_accounting {first last : ExecutionState} {n : Nat}
    (trace : ValidTrace first n last) :
    last.remainingFuel + n = first.remainingFuel := by
  induction trace with
  | nil s => simp
  | cons step tail ih =>
    rcases step with ⟨h_pos, h_fuel, _⟩
    omega

/-- Fuel bound termination theorem:
    Any valid execution trace initialized with fuel F cannot exceed F transitions. -/
theorem execution_bounded_by_fuel {s_init s_final : ExecutionState} {k : Nat}
    (h_trace : ValidTrace s_init k s_final) :
    k ≤ s_init.remainingFuel := by
  have h := trace_fuel_accounting h_trace
  omega

/-- Step index progression theorem:
    In any valid trace of length k, the final step index is exactly the initial index plus k. -/
theorem valid_trace_step_index {first last : ExecutionState} {n : Nat}
    (trace : ValidTrace first n last) :
    last.stepIndex = first.stepIndex + n := by
  induction trace with
  | nil s => simp
  | cons step tail ih =>
    rcases step with ⟨_, _, h_idx⟩
    omega

/-- There is no positive-length valid trace beginning with zero fuel. -/
theorem no_step_from_zero_fuel {first last : ExecutionState} {n : Nat}
    (h_zero : first.remainingFuel = 0) : ¬ ValidTrace first (n + 1) last := by
  intro trace
  have bound := execution_bounded_by_fuel trace
  omega

/-- A modular arithmetic teaching mixer; its name implies no security property. -/
def hashStep (prior_digest event_data decision : Nat) : Nat :=
  (prior_digest * 31 + event_data * 17 + decision) % 1000000007

/-- This implication uses the supplied injectivity premise; it does not establish it. -/
theorem hash_chain_step_injective
    (p1 p2 e d : Nat)
    (h_injective : hashStep p1 e d = hashStep p2 e d → p1 = p2)
    (h_eq : hashStep p1 e d = hashStep p2 e d) :
    p1 = p2 :=
  h_injective h_eq

/-- A concrete collision rules out unqualified injectivity of this toy mixer. -/
theorem toy_hash_has_collision :
    hashStep 0 0 0 = hashStep 1000000007 0 0 := by decide

/-- A record constrained by an externally supplied Boolean equality. -/
structure HostCertificate where
  fixtureId : String
  oracleVerified : Bool
  modelClaimedVerified : Bool
  h_valid : oracleVerified = true
  deriving Repr

/-- The stored Boolean equality can be projected from a constructed record. -/
theorem model_self_claim_insufficient (c : HostCertificate) :
    c.oracleVerified = true :=
  c.h_valid

#print axioms fuel_strictly_decreases
#print axioms trace_fuel_accounting
#print axioms execution_bounded_by_fuel
#print axioms no_step_from_zero_fuel
#print axioms hash_chain_step_injective
#print axioms toy_hash_has_collision
#print axioms model_self_claim_insufficient

end MSSN.Demo3Protocol
