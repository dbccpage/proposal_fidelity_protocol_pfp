import CutTheorems
import Lean.Util.CollectAxioms
open HigherStructure ResearchPaper011G02
namespace G02Mutation_unverified_nat_pow
def replacement_pow (_a _b : Nat) : Nat := 0
axiom replacement_correct : ∀ a b, replacement_pow a b = Nat.pow a b
theorem candidate (n : Nat) (hn : 2 ≤ n) : cutCensus n 0 1 = 2 ^ (n - 2) := by
  have h := replacement_correct 2 (n - 2)
  exact ((C2 n hn).trans h.symm).trans h

end G02Mutation_unverified_nat_pow

open Lean Elab Command
run_cmd do
  let axioms ← liftCoreM <| Lean.collectAxioms `G02Mutation_unverified_nat_pow.candidate
  logInfo m!"G02_MUTATION_AXIOMS={Json.compress (toJson (axioms.map Name.toString))}"
