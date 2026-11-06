# AuthorityEffect: None.
"""
Tests for exact and independent dual checkers (C028).
"""

from __future__ import annotations

import unittest

from c028_jordan_wigner_majorana_mapping.judge_packet.checkers.dual_evaluator import evaluate_dual
from c028_jordan_wigner_majorana_mapping.judge_packet.checkers.exact_checker import verify_exact
from c028_jordan_wigner_majorana_mapping.judge_packet.checkers.independent_checker import verify_independent
from c028_jordan_wigner_majorana_mapping.reference_solver.solver import solve


class TestDualCheckers(unittest.TestCase):
    def setUp(self):
        self.case = {
            "case_id": "fq_06",
            "num_modes": 2,
            "encoding": [[1, 0], [0, 1]],
            "terms": [
                {"coeff": ["1", "0"], "ops": [["dag", 0], ["ann", 1]]},
                {"coeff": ["1", "0"], "ops": [["dag", 1], ["ann", 0]]},
            ],
        }
        self.sol = solve(self.case)

    def test_dual_consensus_on_reference_solution(self):
        passed, msg, det = evaluate_dual(self.case, self.sol)
        self.assertTrue(passed)
        self.assertIn("DUAL CONSENSUS", msg)

    def test_exact_checker_rejects_majorana_sign_flip(self):
        bad_sol = dict(self.sol)
        bad_sol["majoranas"] = ["-XI", "+YI", "+ZX", "+ZY"]
        passed, msg, _ = verify_exact(self.case, bad_sol)
        self.assertFalse(passed)

    def test_independent_checker_rejects_qubit_coeff_alteration(self):
        bad_sol = dict(self.sol)
        bad_sol["hamiltonian"] = [["XX", "1"], ["YY", "1/2"]]
        passed, msg, _ = verify_independent(self.case, bad_sol)
        self.assertFalse(passed)

    def test_singular_encoding_dual_agreement(self):
        singular_case = {
            "case_id": "test_sing",
            "num_modes": 2,
            "encoding": [[1, 1], [1, 1]],
            "terms": [{"coeff": ["1", "0"], "ops": [["dag", 0], ["ann", 0]]}],
        }
        sol = solve(singular_case)
        passed, msg, _ = evaluate_dual(singular_case, sol)
        self.assertTrue(passed)


if __name__ == "__main__":
    unittest.main()
