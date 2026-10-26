# AuthorityEffect: None.
"""
Unit tests for CDCL SAT solver and DRAT proof emission.
"""

import unittest

from omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver.drat_engine import verify_drat_certificate
from omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver.sat_solver import solve_cnf
from omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver.solver import format_dimacs_cnf


class TestCDCLSolver(unittest.TestCase):
    def test_satisfiable_formula(self):
        # (x1 or x2) and (-x1 or x2)
        clauses = [[1, 2], [-1, 2]]
        is_sat, model, drat = solve_cnf(2, clauses)
        self.assertTrue(is_sat)
        self.assertIsNotNone(model)
        self.assertEqual(model[2], 1)

    def test_unsatisfiable_formula_with_drat(self):
        # (x1) and (-x1)
        clauses = [[1], [-1]]
        is_sat, model, drat = solve_cnf(1, clauses)
        self.assertFalse(is_sat)
        self.assertIsNone(model)
        self.assertTrue(drat.endswith("0"))

        cnf_str = format_dimacs_cnf(1, clauses)
        ok, msg = verify_drat_certificate(cnf_str, drat)
        self.assertTrue(ok, f"DRAT verification failed: {msg}")

    def test_triangle_k2_unsat(self):
        from omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver.family_solvers import encode_coloring

        num_vars, clauses, _ = encode_coloring(3, 2, [[0, 1], [1, 2], [0, 2]])
        is_sat, model, drat = solve_cnf(num_vars, clauses)
        self.assertFalse(is_sat)
        self.assertTrue(drat.endswith("0"))

        cnf_str = format_dimacs_cnf(num_vars, clauses)
        ok, msg = verify_drat_certificate(cnf_str, drat)
        self.assertTrue(ok, f"DRAT verification failed: {msg}")


if __name__ == "__main__":
    unittest.main()
