import G01Targets
import Lean
open Lean Elab Command
theorem candidate : G01Targets.F1 :=
  Or.elim (Classical.em G01Targets.F1) id
    (fun h => False.elim (h ResearchG01.F_1))

run_cmd do
  let ci ← liftTermElabM <| Lean.getConstInfo ``candidate
  unless ci.isTheorem do throwError "NOT_A_THEOREM"
  let expected ← liftTermElabM <| Lean.Meta.whnf (Lean.mkConst ``G01Targets.F1)
  let matched ← liftTermElabM <| Lean.Meta.isDefEq expected ci.type
  unless matched do throwError "STATEMENT_PIN_MISMATCH"
  let axioms ← liftCoreM <| Lean.collectAxioms ``candidate
  logInfo m!"G01_CANDIDATE_AXIOMS={Lean.Json.compress (Lean.toJson (axioms.map Lean.Name.toString))}"
  for a in axioms do
    unless a == ``propext || a == ``Quot.sound do throwError "DISALLOWED_AXIOM {a}"
  logInfo "G01_CANDIDATE_ACCEPTED"
