# AuthorityEffect: None.
"""End-to-End integration test for C025 Challenge Suite."""

import json
from pathlib import Path

from c025_mub_prime_power_exact.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c025_mub_prime_power_exact.reference_solver.solver import (
    solve,
)

_pkg_dir = Path(__file__).resolve().parent.parent


def test_e2e_all_judge_cases():
    cases_dir = _pkg_dir / "judge_packet" / "cases"
    case_files = sorted(cases_dir.glob("*.json"))
    assert len(case_files) == 23, f"Expected 23 judge cases, found {len(case_files)}"

    for cf in case_files:
        with open(cf, "r", encoding="utf-8") as f:
            case_data = json.load(f)

        ans = solve(case_data)
        passed, msg, det = evaluate_dual(case_data, ans)
        assert passed, f"Case {cf.name} failed dual evaluation: {msg} (details: {det})"


def test_e2e_100_percent_hostile_mutation_kill_rate():
    mut_dir = _pkg_dir / "judge_packet" / "mutation_suite"
    mut_files = sorted(mut_dir.glob("*.json"))
    assert len(mut_files) == 55, f"Expected 55 hostile mutations, found {len(mut_files)}"

    survived = []
    for mf in mut_files:
        with open(mf, "r", encoding="utf-8") as f:
            mdata = json.load(f)
        m_case = mdata["case"]
        m_ans = mdata["answer"]

        passed, msg, _ = evaluate_dual(m_case, m_ans)
        if passed:
            survived.append(mf.name)

    assert not survived, f"Hostile mutations survived: {survived}"
