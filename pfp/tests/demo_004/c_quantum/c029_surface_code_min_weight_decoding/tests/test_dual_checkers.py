# AuthorityEffect: None.
"""Unit tests for Dual Checkers and Evaluator in C029."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from judge_packet.checkers.dual_evaluator import evaluate_dual
from judge_packet.checkers.exact_checker import verify_exact
from judge_packet.checkers.independent_checker import verify_independent
from reference_solver.solver import solve


class TestDualCheckers(unittest.TestCase):
    def setUp(self) -> None:
        self.cases_dir = Path(__file__).resolve().parent.parent / "judge_packet" / "cases"

    def test_dual_checkers_on_base_cases(self) -> None:
        # Test on first 5 base cases
        for i in range(1, 6):
            cf = self.cases_dir / f"base_{i:02d}.json"
            if not cf.exists():
                continue
            with open(cf, "r", encoding="utf-8") as f:
                case = json.load(f)
            ans = solve(case)
            ok, msg, det = evaluate_dual(case, ans)
            self.assertTrue(ok, f"Failed on {cf.name}: {msg}")

    def test_rejection_of_corrupted_weight(self) -> None:
        cf = self.cases_dir / "base_02.json"  # base_01 repeated a public example
        with open(cf, "r", encoding="utf-8") as f:
            case = json.load(f)
        ans = solve(case)
        ans["weight"] = ans["weight"] + 99  # Corrupt weight
        ok_exact, _, _ = verify_exact(case, ans)
        ok_indep, _, _ = verify_independent(case, ans)
        self.assertFalse(ok_exact)
        self.assertFalse(ok_indep)


if __name__ == "__main__":
    unittest.main()
