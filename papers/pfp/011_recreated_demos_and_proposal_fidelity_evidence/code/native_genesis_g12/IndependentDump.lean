import ParkedAudit
import Lean.Meta.Basic

open Lean Elab Command Meta

run_cmd do
  let env ← getEnv
  let mut modules := #[]
  for m in ParkedAudit.parkedModules do
    let some idx := env.getModuleIdx? m | throwError "MISSING_MODULE {m}"
    let data := env.header.moduleData[idx.toNat]!
    let mut constants := #[]
    for n in data.constNames do
      let some ci := env.find? n | throwError "MISSING_CONSTANT {n}"
      let head ← liftTermElabM <| forallTelescopeReducing ci.type fun _ result => do
        return (← whnf result).getAppFn.constName?.map Name.toString
      constants := constants.push <| Json.mkObj [
        ("name", toJson n.toString), ("is_theorem", toJson ci.isTheorem),
        ("forall_result_head", toJson head)]
    modules := modules.push <| Json.mkObj [
      ("module", toJson m.toString), ("constNames", toJson (data.constNames.map Name.toString)),
      ("constants", toJson constants)]
  logInfo m!"G12_INDEPENDENT_DUMP={Json.compress (toJson modules)}"
