# AuthorityEffect: None.
"""
Unit tests for dual checkers and consensus evaluator.
"""

import unittest

from omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.judge_packet.checkers.dual_evaluator import evaluate_dual


class TestDualCheckers(unittest.TestCase):
    def test_sat_strict_int_type_discipline(self):
        case = {
            "case_id": "test_case",
            "family": "coloring",
            "n": 2,
            "k": 2,
            "edges": [[0, 1]],
        }
        # Valid int answer
        valid_ans = {
            "status": "SOLVED",
            "kind": "SAT",
            "solution": {"colour": [0, 1]},
        }
        ok, msg, _ = evaluate_dual(case, valid_ans)
        self.assertTrue(ok)

        # Corrupted bool answer: True instead of 1
        corrupt_ans = {
            "status": "SOLVED",
            "kind": "SAT",
            "solution": {"colour": [0, True]},
        }
        ok, msg, _ = evaluate_dual(case, corrupt_ans)
        self.assertFalse(ok)
        self.assertIn("not strict int", msg)

    def test_out_of_scope_handling(self):
        case = {"case_id": "oos_case", "family": "coloring"}
        ans = {
            "status": "OUT_OF_SCOPE",
            "witness": {"field": "edges", "reason": "VERTEX_OUT_OF_RANGE"},
        }
        ok, msg, _ = evaluate_dual(case, ans)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
