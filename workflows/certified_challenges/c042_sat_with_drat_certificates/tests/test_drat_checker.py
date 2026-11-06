# AuthorityEffect: None.
"""
Unit tests for DRAT proof verification engine.
"""

import unittest

from c042_sat_with_drat_certificates.reference_solver.drat_engine import verify_drat_certificate


class TestDRATChecker(unittest.TestCase):
    def test_valid_simple_drat(self):
        cnf = "p cnf 2 3\n1 0\n-1 2 0\n-2 0\n"
        # Proof: derive empty clause
        drat = "0\n"
        ok, msg = verify_drat_certificate(cnf, drat)
        self.assertTrue(ok)

    def test_rejected_without_empty_clause(self):
        cnf = "p cnf 2 3\n1 0\n-1 2 0\n-2 0\n"
        drat = "1 2 0\n"
        ok, msg = verify_drat_certificate(cnf, drat)
        self.assertFalse(ok)
        self.assertIn("without validly deriving the empty clause", msg)

    def test_rejected_invalid_lemma(self):
        cnf = "p cnf 2 1\n1 2 0\n"
        # False lemma: -1 -2 does not follow by RUP from (1 or 2)
        drat = "-1 -2 0\n0\n"
        ok, msg = verify_drat_certificate(cnf, drat)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
