# AuthorityEffect: None.
"""Unit tests for tensor_network module in C030."""

from __future__ import annotations

import unittest

from c030_tensor_network_contraction_order.reference_solver.tensor_network import (
    compute_step_cost_and_size,
    replay_contraction_order,
    validate_network,
)


class TestTensorNetwork(unittest.TestCase):
    def test_validate_valid_network(self) -> None:
        tensors = {"A": ["i", "j"], "B": ["j", "k"]}
        dims = {"i": 2, "j": 4, "k": 3}
        ok, witness = validate_network(tensors, dims)
        self.assertTrue(ok)
        self.assertIsNone(witness)

    def test_validate_hyperedge_detected(self) -> None:
        tensors = {"A": ["i", "h"], "B": ["j", "h"], "C": ["k", "h"]}
        dims = {"i": 2, "j": 2, "k": 2, "h": 2}
        ok, witness = validate_network(tensors, dims)
        self.assertFalse(ok)
        self.assertEqual(witness.get("kind"), "hyperedge")
        self.assertEqual(witness.get("index"), "h")

    def test_compute_step_cost_and_size(self) -> None:
        dims = {"i": 2, "j": 4, "k": 3}
        cost, size, out_idx = compute_step_cost_and_size({"i", "j"}, {"j", "k"}, dims)
        self.assertEqual(cost, 2 * 4 * 3)  # 24
        self.assertEqual(size, 2 * 3)  # 6
        self.assertEqual(out_idx, {"i", "k"})

    def test_replay_contraction_order_worked_example(self) -> None:
        tensors = {"A": ["i", "j"], "B": ["j", "k"], "C": ["k", "l"]}
        dims = {"i": 2, "j": 64, "k": 64, "l": 2}
        order = [["A", "B"], ["@step:0", "C"]]
        ok, cost, max_sz, msg = replay_contraction_order(tensors, dims, order, cost_bound=16384)
        self.assertTrue(ok)
        self.assertEqual(cost, 8448)


if __name__ == "__main__":
    unittest.main()
