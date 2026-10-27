"""End-to-End challenge verification test for C024."""

from __future__ import annotations

import json
from pathlib import Path

from projects.mssn_sn_symgam.challenges.c_quantum.c024_local_clifford_graph_state_equivalence.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.c_quantum.c024_local_clifford_graph_state_equivalence.reference_solver.solver import (
    solve,
)


def test_all_base_cases():
    cases_dir = Path(__file__).resolve().parent.parent / "judge_packet" / "cases"
    base_cases = sorted(cases_dir.glob("c024_base_*.json"))
    assert len(base_cases) == 28  # two leaked base cases removed 2026-09-29

    for case_path in base_cases:
        with open(case_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        inp = data.get("input", data)
        ans = solve(inp)
        assert ans["status"] == "SOLVED", f"Failed on {case_path.name}: {ans}"
        passed, detail, meta = evaluate_dual(inp, ans)
        assert passed is True, f"Checker failed on {case_path.name}: {detail}"


def test_all_controls():
    cases_dir = Path(__file__).resolve().parent.parent / "judge_packet" / "cases"
    control_cases = sorted(cases_dir.glob("c024_ctrl_*.json"))
    assert len(control_cases) == 9  # ctrl_08 repeated base_08

    for case_path in control_cases:
        with open(case_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        inp = data.get("input", data)
        ans = solve(inp)
        assert ans["status"] == "SOLVED", f"Failed on {case_path.name}: {ans}"
        passed, detail, meta = evaluate_dual(inp, ans)
        assert passed is True, f"Checker failed on {case_path.name}: {detail}"


def test_all_poisoned_cases():
    cases_dir = Path(__file__).resolve().parent.parent / "judge_packet" / "cases"
    poisoned_cases = sorted(cases_dir.glob("c024_poison_*.json"))
    assert len(poisoned_cases) == 3  # three leaked poisoned cases removed

    for case_path in poisoned_cases:
        with open(case_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        inp = data.get("input", data)
        ans = solve(inp)
        passed, detail, meta = evaluate_dual(inp, ans)
        assert passed is True, f"Checker failed on {case_path.name}: {detail}"
