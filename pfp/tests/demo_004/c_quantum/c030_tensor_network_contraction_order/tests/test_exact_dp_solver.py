# AuthorityEffect: None.
"""Unit tests for exact_dp_solver in C030."""

from __future__ import annotations

import unittest

from reference_solver.exact_dp_solver import solve_exact_subset_dp


class TestExactDPSolver(unittest.TestCase):
    def test_dp_three_chain_optimum(self) -> None:
        tensors = {"A": ["i", "j"], "B": ["j", "k"], "C": ["k", "l"]}
        dims = {"i": 2, "j": 64, "k": 64, "l": 2}
        ok, opt_cost, order = solve_exact_subset_dp(tensors, dims)
        self.assertTrue(ok)
        self.assertEqual(opt_cost, 8448)
        self.assertEqual(len(order), 2)

    def test_dp_size_bound_enforcement(self) -> None:
        tensors = {"A": ["i", "j"], "B": ["j", "k"], "C": ["k", "l"]}
        dims = {"i": 2, "j": 4, "k": 4, "l": 2}
        # Intermediate size is at least 4. If size_bound=2, must fail
        ok, opt_cost, order = solve_exact_subset_dp(tensors, dims, size_bound=2)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
