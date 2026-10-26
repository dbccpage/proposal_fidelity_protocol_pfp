import CutTheorems
import Lean.Util.CollectAxioms
open HigherStructure ResearchPaper011G02
namespace G02Mutation_open_classical
open Classical
theorem candidate (n : Nat) (hn : 2 ≤ n) : cutCensus n 0 1 = 2 ^ (n - 2) := C2 n hn

end G02Mutation_open_classical

open Lean Elab Command
run_cmd do
  let axioms ← liftCoreM <| Lean.collectAxioms `G02Mutation_open_classical.candidate
  logInfo m!"G02_MUTATION_AXIOMS={Json.compress (toJson (axioms.map Name.toString))}"
