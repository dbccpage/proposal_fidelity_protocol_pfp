# AuthorityEffect: None.
"""
Tests for Majorana mapping and Hamiltonian term expansion (C028).
"""

from __future__ import annotations

import unittest

from c028_jordan_wigner_majorana_mapping.reference_solver.majorana_mapper import compute_majorana_operators
from c028_jordan_wigner_majorana_mapping.reference_solver.solver import solve


class TestMajoranaAndExpander(unittest.TestCase):
    def test_jordan_wigner_n2_majoranas(self):
        is_val, maj, _ = compute_majorana_operators(2, [[1, 0], [0, 1]])
        self.assertTrue(is_val)
        self.assertEqual(maj, ["+XI", "+YI", "+ZX", "+ZY"])

    def test_two_mode_hopping_expansion(self):
        case = {
            "case_id": "fq_06",
            "num_modes": 2,
            "encoding": [[1, 0], [0, 1]],
            "terms": [
                {"coeff": ["1", "0"], "ops": [["dag", 0], ["ann", 1]]},
                {"coeff": ["1", "0"], "ops": [["dag", 1], ["ann", 0]]},
            ],
        }
        res = solve(case)
        self.assertEqual(res["status"], "SOLVED")
        self.assertEqual(res["majoranas"], ["+XI", "+YI", "+ZX", "+ZY"])
        self.assertEqual(res["hamiltonian"], [["XX", "1/2"], ["YY", "1/2"]])

    def test_number_operator_expansion(self):
        # a_0^dag a_0 under JW maps to (II - ZI)/2 = 1/2 II - 1/2 ZI
        case = {
            "case_id": "test_num",
            "num_modes": 2,
            "encoding": [[1, 0], [0, 1]],
            "terms": [
                {"coeff": ["1", "0"], "ops": [["dag", 0], ["ann", 0]]},
            ],
        }
        res = solve(case)
        self.assertEqual(res["status"], "SOLVED")
        self.assertEqual(res["hamiltonian"], [["II", "1/2"], ["ZI", "-1/2"]])

    def test_non_hermitian_detection(self):
        case = {
            "case_id": "test_non_herm",
            "num_modes": 2,
            "encoding": [[1, 0], [0, 1]],
            "terms": [
                {"coeff": ["1", "0"], "ops": [["dag", 0], ["ann", 1]]},
            ],
        }
        res = solve(case)
        self.assertEqual(res["status"], "OUT_OF_SCOPE")
        self.assertEqual(res["witness"]["kind"], "non_hermitian_hamiltonian")


if __name__ == "__main__":
    unittest.main()
