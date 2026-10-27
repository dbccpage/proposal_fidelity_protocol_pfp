# AuthorityEffect: None.
"""Unit tests for Dual Checkers in C030."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from c030_tensor_network_contraction_order.judge_packet.checkers.dual_evaluator import evaluate_dual
from c030_tensor_network_contraction_order.judge_packet.checkers.exact_checker import verify_exact
from c030_tensor_network_contraction_order.judge_packet.checkers.independent_checker import verify_independent
from c030_tensor_network_contraction_order.reference_solver.solver import solve


class TestDualCheckers(unittest.TestCase):
    def setUp(self) -> None:
        self.cases_dir = Path(__file__).resolve().parent.parent / "judge_packet" / "cases"

    def test_dual_checkers_first_5_base_cases(self) -> None:
        for i in range(1, 6):
            matches = list(self.cases_dir.glob(f"c030_base_{i:02d}_*.json"))
            if not matches:
                continue
            cf = matches[0]
            with open(cf, "r", encoding="utf-8") as f:
                case = json.load(f)
            ans = solve(case)
            ok, msg, det = evaluate_dual(case, ans)
            self.assertTrue(ok, f"Failed on {cf.name}: {msg}")

    def test_rejection_of_corrupted_cost(self) -> None:
        matches = list(self.cases_dir.glob("c030_base_01_*.json"))
        self.assertTrue(matches)
        cf = matches[0]
        with open(cf, "r", encoding="utf-8") as f:
            case = json.load(f)
        ans = solve(case)
        ans["total_cost"] = str(int(ans["total_cost"]) + 1)
        ok_exact, _, _ = verify_exact(case, ans)
        ok_indep, _, _ = verify_independent(case, ans)
        self.assertFalse(ok_exact)
        self.assertFalse(ok_indep)


if __name__ == "__main__":
    unittest.main()
