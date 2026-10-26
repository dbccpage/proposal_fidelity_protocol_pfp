import CutTheorems
import Lean.Util.CollectAxioms
open HigherStructure ResearchPaper011G02
namespace G02Mutation_valid_control
theorem candidate (n : Nat) (hn : 2 ≤ n) : cutCensus n 0 1 = 2 ^ (n - 2) := C2 n hn

end G02Mutation_valid_control

example : ∀ n, 2 ≤ n → cutCensus n 0 1 = 2 ^ (n - 2) :=
  G02Mutation_valid_control.candidate
