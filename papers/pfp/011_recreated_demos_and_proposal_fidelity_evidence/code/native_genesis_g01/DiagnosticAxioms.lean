import ResearchG01
import Lean
#print axioms ResearchG01.fixed_valid
#print axioms ResearchG01.bounded_valid
#print axioms ResearchG01.state_arity_invariant
#print axioms ResearchG01.binary_diag_noniso
#print axioms ResearchG01.req_nonzero
#print axioms ResearchG01.target_to_genout_noniso
#print axioms ResearchG01.target_to_genin_noniso
#print axioms ResearchG01.genout_to_genin_noniso
#print axioms ResearchG01.bounded_pairwise
#print axioms ResearchG01.relabelled_pairwise

open Lean Elab Command
run_cmd do
  let env ← getEnv
  for n in env.header.moduleData[(env.getModuleIdx? `ResearchG01).get!.toNat]!.constNames do
    if (`ResearchG01.req_nonzero).isPrefixOf n then
      let ci := env.find? n |>.get!
      if let some value := ci.value? (allowOpaque := true) then
        for c in value.getUsedConstants do
          let ax ← liftCoreM <| Lean.collectAxioms c
          if ax.contains ``Classical.choice then logInfo m!"CHOICE_DEPENDENCY {n} -> {c}"
