# AuthorityEffect: None.
"""
Tests for exact phase-tracked Pauli algebra (C028).
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from reference_solver.pauli_algebra import (
    format_fraction,
    multiply_pauli_strings,
)


class TestPauliAlgebra(unittest.TestCase):
    def test_single_pauli_products(self):
        # X * Y = i Z
        re, im, p = multiply_pauli_strings(1, "X", 1, "Y")
        self.assertEqual((re, im, p), (Fraction(0, 1), Fraction(1, 1), "Z"))

        # Y * X = -i Z
        re, im, p = multiply_pauli_strings(1, "Y", 1, "X")
        self.assertEqual((re, im, p), (Fraction(0, 1), Fraction(-1, 1), "Z"))

        # Z * X = i Y
        re, im, p = multiply_pauli_strings(1, "Z", 1, "X")
        self.assertEqual((re, im, p), (Fraction(0, 1), Fraction(1, 1), "Y"))

        # X * Z = -i Y
        re, im, p = multiply_pauli_strings(1, "X", 1, "Z")
        self.assertEqual((re, im, p), (Fraction(0, 1), Fraction(-1, 1), "Y"))

        # X * X = I
        re, im, p = multiply_pauli_strings(1, "X", 1, "X")
        self.assertEqual((re, im, p), (Fraction(1, 1), Fraction(0, 1), "I"))

    def test_multi_qubit_pauli_products(self):
        # (XI) * (ZX) = (XZ)(IX) = (-i Y)(X) = -i YX
        re, im, p = multiply_pauli_strings(1, "XI", 1, "ZX")
        self.assertEqual((re, im, p), (Fraction(0, 1), Fraction(-1, 1), "YX"))

        # (-XI) * (-ZX) = -i YX
        re, im, p = multiply_pauli_strings(-1, "XI", -1, "ZX")
        self.assertEqual((re, im, p), (Fraction(0, 1), Fraction(-1, 1), "YX"))

    def test_format_fraction(self):
        self.assertEqual(format_fraction(Fraction(1, 1)), "1")
        self.assertEqual(format_fraction(Fraction(0, 1)), "0")
        self.assertEqual(format_fraction(Fraction(-3, 1)), "-3")
        self.assertEqual(format_fraction(Fraction(1, 2)), "1/2")
        self.assertEqual(format_fraction(Fraction(-3, 4)), "-3/4")


if __name__ == "__main__":
    unittest.main()
