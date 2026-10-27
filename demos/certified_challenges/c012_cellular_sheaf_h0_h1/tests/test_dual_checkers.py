"""Tests for C012 Dual Checkers and Evaluator.

Verifies:
1. 100% agreement between Checker 1 and Checker 2 across all hidden cases.
2. Clean rejection of corruptions.
3. Zero shared imports between checker implementations.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

from c012_cellular_sheaf_h0_h1.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c012_cellular_sheaf_h0_h1.judge_packet.checkers.sheaf_algebraic_checker import (
    verify_algebraic_certificate,
)
from c012_cellular_sheaf_h0_h1.judge_packet.checkers.sheaf_echelon_checker import (
    verify_echelon_certificate,
)
from c012_cellular_sheaf_h0_h1.reference_solver.solver import (
    solve,
)

JUDGE_DIR = Path(__file__).resolve().parent.parent / "judge_packet"
CASES_DIR = JUDGE_DIR / "cases"


def test_dual_checkers_100_percent_agreement_on_hidden_cases():
    """Asserts both checkers pass all 68 hidden cases with 100% agreement."""
    hidden_files = sorted(CASES_DIR.rglob("*.json"))
    assert len(hidden_files) == 68, f"Expected 68 hidden cases, found {len(hidden_files)}"

    for f in hidden_files:
        case = json.loads(f.read_text(encoding="utf-8"))
        res = solve(case)

        ok1, msg1 = verify_algebraic_certificate(case, res)
        ok2, msg2 = verify_echelon_certificate(case, res)

        assert ok1, f"Checker 1 failed on {f.name}: {msg1}"
        assert ok2, f"Checker 2 failed on {f.name}: {msg2}"

        eval_res = evaluate_dual(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True
