import G01Targets
import Lean

open Lean Elab Command Meta

def targetBindings : Array (Name × Name) := #[
  (``G01Targets.F1, ``ResearchG01.F_1), (``G01Targets.F5, ``ResearchG01.F_5),
  (``G01Targets.FK, ``ResearchG01.F_K),
  (``G01Targets.H01, ``ResearchG01.H01_relabelled_F5),
  (``G01Targets.H02, ``ResearchG01.H02_family_vs_genout),
  (``G01Targets.H03, ``ResearchG01.H03_family_vs_genin),
  (``G01Targets.H04, ``ResearchG01.H04_fixed_k3),
  (``G01Targets.H05, ``ResearchG01.H05_bounded_family_members),
  (``G01Targets.H06, ``ResearchG01.H06_genesis_mark_refuted),
  (``G01Targets.H07, ``ResearchG01.H07_mu2_unique_witness),
  (``G01Targets.H08, ``ResearchG01.H08_reading_identification_refuted)]

run_cmd do
  let env ← getEnv
  let some idx := env.getModuleIdx? `ResearchG01 | throwError "MISSING_RESEARCH_MODULE"
  let mut census := #[]
  let mut reports := #[]
  for n in env.header.moduleData[idx.toNat]!.constNames do
    let some ci := env.find? n | throwError "MISSING_CONSTANT {n}"
    let typ ← liftTermElabM <| ppExpr ci.type
    let ax ← liftCoreM <| Lean.collectAxioms n
    if ci.isTheorem then
      for a in ax do
        unless a == ``propext || a == ``Quot.sound do throwError "DISALLOWED_AXIOM {n} {a}"
      reports := reports.push <| Json.mkObj [
        ("name", toJson n.toString), ("axioms", toJson (ax.map Name.toString)),
        ("type", toJson typ.pretty)]
    census := census.push <| Json.mkObj [
      ("name", toJson n.toString), ("is_theorem", toJson ci.isTheorem),
      ("type", toJson typ.pretty), ("axioms", toJson (ax.map Name.toString))]
  let mut pins := #[]
  for (goal, proof) in targetBindings do
    let proofInfo ← liftTermElabM <| getConstInfo proof
    unless proofInfo.isTheorem do throwError "NOT_A_THEOREM {proof}"
    let expected ← liftTermElabM <| whnf (mkConst goal)
    let matchType ← liftTermElabM <| isDefEq expected proofInfo.type
    unless matchType do throwError "STATEMENT_PIN_MISMATCH {proof}"
    let typ ← liftTermElabM <| ppExpr expected
    pins := pins.push <| Json.mkObj [
      ("goal", toJson goal.toString), ("proof", toJson proof.toString),
      ("type", toJson typ.pretty), ("matched", toJson true)]
  logInfo m!"G01_CENSUS={Json.compress (toJson census)}"
  logInfo m!"G01_AXIOMS={Json.compress (toJson reports)}"
  logInfo m!"G01_PINS={Json.compress (toJson pins)}"

#print axioms ResearchG01.F_1
#print axioms ResearchG01.F_5
#print axioms ResearchG01.F_K
#print axioms ResearchG01.H01_relabelled_F5
#print axioms ResearchG01.H02_family_vs_genout
#print axioms ResearchG01.H03_family_vs_genin
#print axioms ResearchG01.H04_fixed_k3
#print axioms ResearchG01.H05_bounded_family_members
#print axioms ResearchG01.H06_genesis_mark_refuted
#print axioms ResearchG01.H07_mu2_unique_witness
#print axioms ResearchG01.H08_reading_identification_refuted
