# AuthorityEffect: None.
"""Unit tests for Blossom Matching and Decoding Solver in C029."""

from __future__ import annotations

import unittest

from c029_surface_code_min_weight_decoding.reference_solver.matching_solver import (
    find_min_weight_perfect_matching,
    solve_min_weight_decoding,
)


class TestMatchingSolver(unittest.TestCase):
    def test_min_weight_matching_triangle_with_slack(self) -> None:
        edges = {
            (0, 1): 2,
            (0, 2): 4,
            (1, 2): 3,
            (0, 3): 10,
            (1, 3): 10,
            (2, 3): 10,
        }
        cost, pairs = find_min_weight_perfect_matching(4, edges)
        self.assertEqual(cost, 12)  # (0, 1) cost 2 + (2, 3) cost 10

    def test_solve_min_weight_decoding_empty_syndrome(self) -> None:
        hz = [[1, 0], [0, 1]]
        weights = [1, 1]
        syndrome = [0, 0]
        ok, ans, ref = solve_min_weight_decoding("rotated", 3, hz, weights, syndrome)
        self.assertTrue(ok)
        self.assertEqual(ans["weight"], 0)
        self.assertEqual(ans["correction"], [])

    def test_solve_min_weight_decoding_odd_torus_refusal(self) -> None:
        hz = [[1, 1], [1, 1]]
        weights = [1, 1]
        syndrome = [1, 0]
        ok, ans, ref = solve_min_weight_decoding("toric", 3, hz, weights, syndrome)
        self.assertFalse(ok)
        self.assertEqual(ref.get("kind"), "odd_parity_on_torus")


if __name__ == "__main__":
    unittest.main()
