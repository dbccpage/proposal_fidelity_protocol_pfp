# AuthorityEffect: None.
"""Tests for Dual Checkers and Mutation Suite Kill Rate in C027."""

import json
from pathlib import Path

import pytest
from c027_kochen_specker_contextuality.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c027_kochen_specker_contextuality.judge_packet.checkers.exact_checker import (
    verify_exact,
)
from c027_kochen_specker_contextuality.reference_solver.solver import (
    solve,
)


# The independent checker enumerates subsets and refuses refutations with more
# than MAX_ENUMERATION_RAYS rays (Peres-33 and its relabelled copy). Those cases
# are checked by the exact checker alone, and the dual judge fails closed on them.
ONE_CHECKER_ONLY = "C027_INDEPENDENT_ENUMERATION_UNAVAILABLE"


def _assert_dual_or_bounded(name, case, ans):
    passed, msg, det = evaluate_dual(case, ans)
    if ONE_CHECKER_ONLY in msg:
        assert verify_exact(case, ans)[0], f"Exact checker rejects {name}"
        return False
    assert passed, f"Failed on {name}: {msg}"
    return True


@pytest.fixture
def pkg_dir():
    return Path(__file__).resolve().parent.parent


def test_dual_checkers_on_base_cases(pkg_dir):
    cases_dir = pkg_dir / "judge_packet" / "cases"
    base_cases = sorted(cases_dir.glob("base_*.json"))
    assert len(base_cases) >= 18

    for bf in base_cases:
        with open(bf, "r", encoding="utf-8") as f:
            case = json.load(f)
        ans = solve(case)
        if _assert_dual_or_bounded(bf.name, case, ans):
            _, _, det = evaluate_dual(case, ans)
            assert det["exact_checker"]["passed"] is True
            assert det["independent_checker"]["passed"] is True


def test_dual_checkers_on_control_cases(pkg_dir):
    cases_dir = pkg_dir / "judge_packet" / "cases"
    ctrl_cases = sorted(cases_dir.glob("ctrl_*.json"))
    assert len(ctrl_cases) >= 8

    for cf in ctrl_cases:
        with open(cf, "r", encoding="utf-8") as f:
            case = json.load(f)
        ans = solve(case)
        _assert_dual_or_bounded(cf.name, case, ans)


def test_dual_checkers_on_poisoned_cases(pkg_dir):
    cases_dir = pkg_dir / "judge_packet" / "cases"
    poison_cases = sorted(cases_dir.glob("poison_*.json"))
    assert len(poison_cases) >= 6

    for pf in poison_cases:
        with open(pf, "r", encoding="utf-8") as f:
            case = json.load(f)
        ans = solve(case)
        passed, msg, det = evaluate_dual(case, ans)
        assert passed, f"Failed on poison {pf.name}: {msg}"


def test_mutation_suite_kill_rate(pkg_dir):
    mut_dir = pkg_dir / "judge_packet" / "mutation_suite"
    mut_files = sorted(mut_dir.glob("*.json"))
    assert len(mut_files) >= 40

    killed = 0
    total = len(mut_files)
    for mf in mut_files:
        with open(mf, "r", encoding="utf-8") as f:
            mdata = json.load(f)
        m_case = mdata["case"]
        m_ans = mdata["answer"]
        passed, msg, _ = evaluate_dual(m_case, m_ans)
        if not passed:
            killed += 1

    assert killed == total, f"Kill rate {killed}/{total} != 100%"
