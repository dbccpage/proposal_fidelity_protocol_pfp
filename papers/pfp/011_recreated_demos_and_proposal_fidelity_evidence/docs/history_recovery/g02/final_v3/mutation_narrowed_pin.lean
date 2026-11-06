import CutTheorems
import Lean.Util.CollectAxioms
open HigherStructure ResearchPaper011G02
namespace G02Mutation_narrowed_pin
theorem candidate (n : Nat) (hn : 4 ≤ n) : cutCensus n 0 1 = 2 ^ (n - 2) :=
  C2 n (by omega)

end G02Mutation_narrowed_pin
