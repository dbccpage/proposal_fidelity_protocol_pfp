import ExactRat
import ExactRat.Basic
import ExactRat.Laws
import ExactRat.Linear
import ExactRat.Poly
import FlowCertificate
import Level16IndObject
import Level21DiscreteRegge
import Level22FibredDependentContexts
import Level23SheafDescent
import Lean
open Lean Elab Command
run_cmd do
  let env ← getEnv
  let modules : Array Name := #[`ExactRat, `ExactRat.Basic, `ExactRat.Laws, `ExactRat.Linear, `ExactRat.Poly, `FlowCertificate, `Level16IndObject, `Level21DiscreteRegge, `Level22FibredDependentContexts, `Level23SheafDescent]
  for (name, _) in env.constants.toList do
    if let some idx := env.getModuleIdxFor? name then
      if modules.contains env.header.moduleNames[idx.toNat]! then
        let axioms ← collectAxioms name
        if axioms.isEmpty then
          logInfo m!"'{name}' does not depend on any axioms"
        else
          let names := String.intercalate ", " (axioms.toList.map toString)
          logInfo m!"'{name}' depends on axioms: [{names}]"
