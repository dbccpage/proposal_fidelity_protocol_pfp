import CutTheorems
import Lean.Util.CollectAxioms
open HigherStructure ResearchPaper011G02
namespace G02Mutation_native_decide
theorem candidate : cutCensus 5 0 1 = 8 := by native_decide

end G02Mutation_native_decide
