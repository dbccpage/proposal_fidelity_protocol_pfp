# AuthorityEffect: None.
"""
Tests for exact linear algebra over F_2 (C028).
"""

from __future__ import annotations

import unittest

from reference_solver.f2_linear_algebra import invert_matrix_f2


class TestF2LinearAlgebra(unittest.TestCase):
    def test_identity_inversion(self):
        M = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        is_inv, M_inv, k_vec = invert_matrix_f2(M)
        self.assertTrue(is_inv)
        self.assertEqual(M_inv, M)
        self.assertIsNone(k_vec)

    def test_parity_matrix_inversion(self):
        M = [[1, 0, 0], [1, 1, 0], [1, 1, 1]]
        is_inv, M_inv, k_vec = invert_matrix_f2(M)
        self.assertTrue(is_inv)
        self.assertEqual(M_inv, [[1, 0, 0], [1, 1, 0], [0, 1, 1]])
        self.assertIsNone(k_vec)

    def test_singular_matrix_kernel_witness(self):
        M = [[1, 1], [1, 1]]
        is_inv, M_inv, k_vec = invert_matrix_f2(M)
        self.assertFalse(is_inv)
        self.assertIsNone(M_inv)
        self.assertIsNotNone(k_vec)
        self.assertEqual(k_vec, [1, 1])
        # Verify M * k_vec == 0 mod 2
        for row in M:
            self.assertEqual(sum(r * k for r, k in zip(row, k_vec)) % 2, 0)


if __name__ == "__main__":
    unittest.main()
