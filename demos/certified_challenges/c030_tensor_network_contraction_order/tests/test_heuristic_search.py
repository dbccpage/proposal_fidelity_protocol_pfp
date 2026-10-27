# AuthorityEffect: None.
"""Unit tests for heuristic_search in C030."""

from __future__ import annotations

import unittest

from c030_tensor_network_contraction_order.reference_solver.heuristic_search import solve_heuristic_search
from c030_tensor_network_contraction_order.reference_solver.tensor_network import replay_contraction_order


class TestHeuristicSearch(unittest.TestCase):
    def test_heuristic_search_chain_15(self) -> None:
        # 15 tensors in a chain
        tensors = {f"T_{i}": [f"b_{i - 1}", f"b_{i}", f"p_{i}"] for i in range(1, 14)}
        tensors["T_0"] = ["b_0", "p_0"]
        tensors["T_14"] = ["b_13", "p_14"]
        dims = {f"b_{i}": 2 for i in range(14)}
        dims.update({f"p_{i}": 2 for i in range(15)})

        meets, cost, order = solve_heuristic_search(
            tensors, dims, cost_bound=1000000, num_restarts=10
        )
        self.assertTrue(meets)
        self.assertLessEqual(cost, 1000000)
        valid, r_cost, max_sz, msg = replay_contraction_order(tensors, dims, order)
        self.assertTrue(valid, msg)
        self.assertEqual(cost, r_cost)


if __name__ == "__main__":
    unittest.main()
