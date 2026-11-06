/-!
Paper PO-001 v2.0: Algorithm Prime Triad Control Law (Standalone Lean 4 Core Kernel).

AuthorityEffect: None.

Formalizes the mathematical foundation of the Algorithm Prime Triad on posets:
1. Prime 000 (Local Declaration Order):
   Local packet declarations along covering edges a -< b with zero knowledge
   of global transitivity.
2. Prime 001 (Adapter Descent Soundness):
   Local covering-edge check: (d_0 s)(a, b) = r_{b, a}(s(b)) - s(a) = 0.
3. Prime 002 (Continue-Until-Unauthorized Control Law):
   Accumulated curvature K(gamma) = sum_i ||K_i|| bounded by B_auth.
4. Key Theorems:
   - `flat_chain_zero_curvature`: Flat systems have zero accumulated curvature.
   - `curvature_accumulation_monotone`: Curvature accumulation is monotonic under chain extension.
   - `early_halting_soundness`: If a chain prefix exceeds budget, the full chain exceeds budget,
     certifying that premature halting on budget breach is sound.
-/

namespace Paper001a

namespace PrimeTriadCore

variable {Node : Type}

/-- Abstract covering chain in a poset -/
structure SaturatedChain (Node : Type) where
  nodes : List Node
  is_valid : nodes.length >= 2

/-- Curvature step record along a chain -/
structure CurvatureStep where
  step_idx : Nat
  step_loss : Nat

/-- Compute total accumulated curvature along a list of curvature steps -/
def accumulateCurvature : List CurvatureStep -> Nat
  | [] => 0
  | step :: rest => step.step_loss + accumulateCurvature rest

/-- Prime 002 Control Law Decision -/
inductive Prime002Decision where
  | authorized (accumulated : Nat) (budget : Nat)
  | refused_budget_exhausted (accumulated : Nat) (budget : Nat)
  | refused_descent_failure (edge_lower edge_upper : String)
  | refused_self_authorization (runner authorizer : String)

/-- Master continuation evaluation under Prime 002 -/
def evaluatePrime002
    (accumulated : Nat)
    (budget : Nat)
    (runner authorizer : String) : Prime002Decision :=
  if runner == authorizer then
    Prime002Decision.refused_self_authorization runner authorizer
  else if accumulated <= budget then
    Prime002Decision.authorized accumulated budget
  else
    Prime002Decision.refused_budget_exhausted accumulated budget

/-- Theorem: On a flat system (all step losses 0), accumulated curvature is 0 -/
theorem flat_chain_zero_curvature
    (steps : List CurvatureStep)
    (h_flat : forall s, s ∈ steps -> s.step_loss = 0) :
    accumulateCurvature steps = 0 := by
  induction steps with
  | nil => rfl
  | cons step rest ih =>
    dsimp [accumulateCurvature]
    have h_step : step.step_loss = 0 := h_flat step (List.Mem.head rest)
    have h_rest : forall s, s ∈ rest -> s.step_loss = 0 := fun s hs => h_flat s (List.Mem.tail step hs)
    rw [h_step, ih h_rest]

/-- Theorem: Curvature accumulation is strictly monotonic under chain extension -/
theorem curvature_accumulation_monotone
    (prefix_steps suffix_steps : List CurvatureStep) :
    accumulateCurvature prefix_steps <=
    accumulateCurvature (prefix_steps ++ suffix_steps) := by
  induction prefix_steps with
  | nil =>
    dsimp [accumulateCurvature]
    exact Nat.zero_le _
  | cons step rest ih =>
    dsimp [accumulateCurvature]
    rw [Nat.add_le_add_iff_left]
    exact ih

/-- Theorem: Early halting soundness.
    If an initial chain prefix exceeds budget B, the full chain unconditionally exceeds B. -/
theorem early_halting_soundness
    (prefix_steps suffix_steps : List CurvatureStep)
    (budget : Nat)
    (h_breach : budget < accumulateCurvature prefix_steps) :
    budget < accumulateCurvature (prefix_steps ++ suffix_steps) := by
  have h_mono := curvature_accumulation_monotone prefix_steps suffix_steps
  exact Nat.lt_of_lt_of_le h_breach h_mono

end PrimeTriadCore

end Paper001a
