import G01Targets
import Lean
open Lean Elab Command
axiom fabricated : G01Targets.F1
theorem candidate : G01Targets.F1 := fabricated

run_cmd do
  let ci ← liftTermElabM <| Lean.getConstInfo ``candidate
  unless ci.isTheorem do throwError "NOT_A_THEOREM"
  let expected ← liftTermElabM <| Lean.Meta.whnf (Lean.mkConst ``G01Targets.F1)
  let matched ← liftTermElabM <| Lean.Meta.isDefEq expected ci.type
  unless matched do throwError "STATEMENT_PIN_MISMATCH"
  let axioms ← liftCoreM <| Lean.collectAxioms ``candidate
  for a in axioms do
    unless a == ``propext || a == ``Quot.sound do throwError "DISALLOWED_AXIOM {a}"
  logInfo "G01_CANDIDATE_ACCEPTED"
