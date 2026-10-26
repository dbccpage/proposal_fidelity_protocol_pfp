import Pins
import Lean.Util.CollectAxioms

open Lean Elab Command

run_cmd do
  let env ← getEnv
  let entries := env.constants.toList.filter fun (n, c) =>
    (`ResearchPaper011G02).isPrefixOf n && c.isTheorem
  let expected := #[`ResearchPaper011G02.C1, `ResearchPaper011G02.C2, `ResearchPaper011G02.C3,
    `ResearchPaper011G02.equal_pair, `ResearchPaper011G02.first_outside,
    `ResearchPaper011G02.second_outside, `ResearchPaper011G02.zero_carrier,
    `ResearchPaper011G02.one_carrier, `ResearchPaper011G02.C3_at_nine,
    `ResearchPaper011G02.C3_at_ten, `ResearchPaper011G02.relabel_pair,
    `ResearchPaper011G02.poison_equal_pair, `ResearchPaper011G02.poison_no_lower_bound]
  for n in expected do
    unless entries.any (fun entry => entry.1 == n) do throwError "MISSING_TARGET {n}"
  let mut reports := #[]
  for (n, _) in entries do
    let axioms ← liftCoreM <| Lean.collectAxioms n
    for a in axioms do
      unless a == ``propext || a == ``Quot.sound do throwError "DISALLOWED_AXIOM {n} {a}"
    reports := reports.push <| Json.mkObj [("name", toJson n.toString),
      ("axioms", toJson (axioms.map Name.toString)), ("public_target", toJson (expected.contains n))]
  logInfo m!"G02_REPORTS={Json.compress (toJson reports)}"
