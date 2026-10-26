import Instances
import Lean.Util.CollectAxioms

open Lean Elab Command Meta

namespace G12

def instanceName (n : Name) : Name :=
  match n.toString with
  | "Derivation.Iso.of_components" => `G12.Instances.of_components
  | "Derivation.Iso.symm" => `G12.Instances.symm
  | "Derivation.Iso.trans" => `G12.Instances.trans
  | "Derivation.iso_of_relabel_eq" => `G12.Instances.iso_of_relabel_eq
  | "Derivation.relabel_iso" => `G12.Instances.relabel_iso
  | _ => Name.anonymous

def checkWrapper (d w : Name) : MetaM Unit := do
  let original ← getConstInfo d
  let wrapper ← getConstInfo w
  unless wrapper.isTheorem do throwError "WRAPPER_IS_NOT_THEOREM {w}"
  let vacuous ← forallTelescope wrapper.type fun xs _ => do
    for x in xs do
      if (← whnf (← inferType x)) == mkConst ``False then return true
    return false
  if vacuous then throwError "VACUOUS_WRAPPER {w}"
  let expected ← forallTelescope original.type fun xs body => do
    instantiateMVars (← mkForallFVars xs (← mkAppM ``Nonempty #[body]))
  unless expected == wrapper.type do throwError "STATEMENT_PIN_MISMATCH {d} {w}"

end G12

run_cmd do
  let env ← getEnv
  let entries ← liftTermElabM <| G12.census env
  let names := entries.map (fun (_, n) => G12.wrapperName n)
  let actual := env.constants.toList.filterMap fun (n, _) =>
    if (`G12.Wrappers).isPrefixOf n then some n else none
  if actual.length != names.size || !actual.all names.contains then
    throwError "WRAPPER_CENSUS_MISMATCH"
  let mut reports := #[]
  for (m, d) in entries do
    let w := G12.wrapperName d
    let i := G12.instanceName d
    liftTermElabM <| G12.checkWrapper d w
    let axioms ← liftCoreM <| Lean.collectAxioms w
    let instanceAxioms ← liftCoreM <| Lean.collectAxioms i
    for a in axioms ++ instanceAxioms do
      unless a == ``propext || a == ``Quot.sound do throwError "DISALLOWED_AXIOM {a}"
    let some inst := env.find? i | throwError "MISSING_CONCRETE_INSTANCE {d}"
    unless inst.isTheorem do throwError "INSTANCE_IS_NOT_THEOREM {i}"
    let closed ← liftTermElabM do
      return (← whnf inst.type).getAppFn.constName? == some ``Nonempty
    unless closed do throwError "INSTANCE_HAS_UNDISCHARGED_HYPOTHESES {i}"
    logInfo (ParkedAudit.renderReport w axioms)
    reports := reports.push <| Json.mkObj [
      ("definition", toJson d.toString), ("module", toJson m.toString),
      ("wrapper", toJson w.toString), ("instance", toJson i.toString),
      ("axioms", toJson (axioms.map Name.toString)),
      ("instance_axioms", toJson (instanceAxioms.map Name.toString)),
      ("status", toJson "SOLVED")]
  logInfo m!"G12_REPORTS={Json.compress (toJson reports)}"
