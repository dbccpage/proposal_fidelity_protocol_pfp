# AuthorityEffect: None.
"""Unit tests for ExactSimplex in C029."""

from __future__ import annotations

import unittest
from fractions import Fraction

from c029_surface_code_min_weight_decoding.reference_solver.exact_simplex import (
    ExactSimplex,
    format_fraction,
    parse_fraction,
)


class TestExactSimplex(unittest.TestCase):
    def test_parse_and_format_fraction(self) -> None:
        self.assertEqual(parse_fraction("1/3"), Fraction(1, 3))
        self.assertEqual(parse_fraction(5), Fraction(5, 1))
        self.assertEqual(format_fraction(Fraction(4, 2)), "2")
        self.assertEqual(format_fraction(Fraction(3, 4)), "3/4")

    def test_simple_feasible_lp(self) -> None:
        # min x1 + 2 x2
        # s.t. x1 + x2 = 3, x1, x2 >= 0
        c = [Fraction(1), Fraction(2)]
        A = [[Fraction(1), Fraction(1)]]
        b = [Fraction(3)]
        solver = ExactSimplex(c, A, b)
        ok, val, x = solver.solve()
        self.assertTrue(ok)
        self.assertEqual(val, Fraction(3))
        self.assertEqual(x, [Fraction(3), Fraction(0)])

    def test_infeasible_lp(self) -> None:
        # x1 + x2 = 1, x1 + x2 = 2
        c = [Fraction(1), Fraction(1)]
        A = [
            [Fraction(1), Fraction(1)],
            [Fraction(1), Fraction(1)],
        ]
        b = [Fraction(1), Fraction(2)]
        solver = ExactSimplex(c, A, b)
        ok, val, x = solver.solve()
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
