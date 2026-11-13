import ParkedAudit
import Lean.Meta.Basic
import Lean.PrettyPrinter

open Lean Elab Command Meta

namespace G12

def wrapperName (n : Name) : Name :=
  Name.str `G12.Wrappers (n.toString.replace "." "_")

def census (env : Environment) : MetaM (Array (Name × Name)) := do
  let mut found := #[]
  for m in ParkedAudit.parkedModules do
    let some idx := env.getModuleIdx? m | throwError "MISSING_PARKED_MODULE {m}"
    for n in env.header.moduleData[idx.toNat]!.constNames do
      let some ci := env.find? n | throwError "MISSING_CONSTANT {n}"
      unless ci.isTheorem do
        let isTarget ← forallTelescope ci.type fun _ body => do
          return (← whnf body).getAppFn == mkConst ``Derivation.Iso
        if isTarget then found := found.push (m, n)
  return found.qsort (fun a b => a.2.toString < b.2.toString)

end G12

run_cmd do
  let env ← getEnv
  let entries ← liftTermElabM do
    let found ← G12.census env
    let mut output := #[]
    for (m, n) in found do
      let ci := env.find? n |>.get!
      let item ← forallTelescope ci.type fun xs body => do
        let prop ← mkAppM ``Nonempty #[body]
        let lifted ← mkForallFVars xs prop
        let pretty ← ppExpr lifted
        let original ← ppExpr ci.type
        let binderNames ← xs.mapM fun x => return (← x.fvarId!.getDecl).userName.toString
        let binderKinds ← xs.mapM fun x => return reprStr (← x.fvarId!.getDecl).binderInfo
        return Json.mkObj [("module", toJson m.toString), ("definition", toJson n.toString),
          ("wrapper", toJson (G12.wrapperName n).toString),
          ("original_type", toJson original.pretty), ("prop_type", toJson pretty.pretty),
          ("binders", toJson binderNames), ("binder_kinds", toJson binderKinds)]
      output := output.push item
    return output
  logInfo m!"G12_CENSUS={Json.compress (toJson entries)}"
