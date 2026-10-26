# AuthorityEffect: None.
"""Unit tests for DecodingGraph in C029."""

from __future__ import annotations

import unittest

from reference_solver.graph import DecodingGraph


class TestDecodingGraph(unittest.TestCase):
    def test_rotated_code_graph_construction(self) -> None:
        # Distance 3 rotated code has 4 Z stabilizers
        hz = [
            [1, 1, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 1, 0],
        ]
        weights = [1] * 9
        graph = DecodingGraph(hz, weights)
        self.assertEqual(graph.boundary_node, 4)
        self.assertIn(4, graph.adj)
        self.assertTrue(graph.has_boundary)

    def test_shortest_path_between_defects(self) -> None:
        # Two connected stabilizers via qubit 1
        hz = [
            [0, 1, 0],
            [0, 1, 0],
        ]
        weights = [1, 2, 1]
        graph = DecodingGraph(hz, weights)
        d, path = graph.shortest_path(0, 1)
        self.assertEqual(d, 2)
        self.assertEqual(path, [1])

    def test_shortest_path_to_boundary(self) -> None:
        # Qubit 0 connected only to stabilizer 0
        hz = [
            [1, 0],
            [0, 1],
        ]
        weights = [3, 5]
        graph = DecodingGraph(hz, weights)
        d, path = graph.shortest_path(0, graph.boundary_node)
        self.assertEqual(d, 3)
        self.assertEqual(path, [0])


if __name__ == "__main__":
    unittest.main()
