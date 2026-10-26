"""End-to-End challenge verification test for C023."""

from __future__ import annotations

import json
from pathlib import Path

from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c023_clifford_tableau_synthesis.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c023_clifford_tableau_synthesis.reference_solver.synthesis import (
    solve,
)


def test_all_base_cases():
    cases_dir = Path(__file__).resolve().parent.parent / "judge_packet" / "cases"
    base_cases = sorted(
        p
        for p in cases_dir.glob("c023_base_*.json")
        if "_perm_" not in p.name and "_pauli_" not in p.name
    )
    assert len(base_cases) == 30

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
    control_cases = sorted(
        p for p in cases_dir.glob("c023_base_*.json") if "_perm_" in p.name or "_pauli_" in p.name
    )
    assert len(control_cases) == 10

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
    poisoned_cases = sorted(cases_dir.glob("c023_poison_*.json"))
    assert len(poisoned_cases) == 6

    for case_path in poisoned_cases:
        with open(case_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        inp = data.get("input", data)
        ans = solve(inp)
        # Poisoned cases should be handled cleanly (either solved if validly permuted or rejected if non-symplectic)
        passed, detail, meta = evaluate_dual(inp, ans)
        assert passed is True, f"Checker failed on {case_path.name}: {detail}"
