import ParkedAudit
import Lean.Meta.Basic
import Lean.AddDecl
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
  liftTermElabM do
    for (_, n) in ← G12.census env do
      let ci := env.find? n |>.get!
      forallTelescope ci.type fun xs body => do
        let prop ← mkAppM ``Nonempty #[body]
        let type ← instantiateMVars (← mkForallFVars xs prop)
        let witness := mkAppN (mkConst n (ci.levelParams.map Level.param)) xs
        let intro ← mkAppM ``Nonempty.intro #[witness]
        let value ← instantiateMVars (← mkLambdaFVars xs intro)
        Lean.addDecl <| .thmDecl {
          name := G12.wrapperName n, levelParams := ci.levelParams, type := type, value := value }
