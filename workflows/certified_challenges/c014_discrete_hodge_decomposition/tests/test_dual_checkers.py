"""Tests for C014 Dual Checkers.

Verifies:
1. Checker 1 (Exact Algebraic & Orthogonality Certifier).
2. Checker 2 (Independent Elimination & Betti 1 Certifier).
3. 100% agreement on base, control, and poisoned cases.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

from c014_discrete_hodge_decomposition.judge_packet.checkers.dual_evaluator import (
    assert_dual_agreement,
)
from c014_discrete_hodge_decomposition.reference_solver.solver import (
    solve,
)

JUDGE_DIR = Path(__file__).resolve().parent.parent / "judge_packet"
CASES_DIR = JUDGE_DIR / "cases"


def test_dual_checkers_all_base_cases():
    """Asserts 100% dual checker agreement on every hidden base case."""
    base_files = sorted((CASES_DIR / "base").glob("*.json"))
    assert len(base_files) == 36, f"Expected 36 base cases, found {len(base_files)}"

    for bf in base_files:
        with open(bf, "r", encoding="utf-8") as f:
            case = json.load(f)
        res = solve(case)
        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"


def test_dual_checkers_all_control_cases():
    """Asserts 100% dual checker agreement on all 16 control cases."""
    ctrl_files = sorted((CASES_DIR / "controls").glob("*.json"))
    assert len(ctrl_files) == 16, f"Expected 16 control cases, found {len(ctrl_files)}"

    for cf in ctrl_files:
        with open(cf, "r", encoding="utf-8") as f:
            case = json.load(f)
        res = solve(case)
        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"


def test_dual_checkers_all_poisoned_cases():
    """Asserts 100% dual checker agreement on every poisoned case."""
    psn_files = sorted((CASES_DIR / "poisoned").glob("*.json"))
    assert len(psn_files) == 10, f"Expected 10 poisoned cases, found {len(psn_files)}"

    for pf in psn_files:
        with open(pf, "r", encoding="utf-8") as f:
            case = json.load(f)
        res = solve(case)
        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
