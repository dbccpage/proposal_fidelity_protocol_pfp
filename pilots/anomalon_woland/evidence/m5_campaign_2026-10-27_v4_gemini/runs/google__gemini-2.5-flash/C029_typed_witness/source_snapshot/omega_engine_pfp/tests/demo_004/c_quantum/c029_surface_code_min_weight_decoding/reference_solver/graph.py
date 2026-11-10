# AuthorityEffect: None.
"""
Decoding graph and exact shortest path computation for C029.

Extracts the syndrome graph from Z-type parity check matrix H_Z:
- Checks (rows of H_Z) are graph vertices.
- Qubits (columns of H_Z) are weighted edges:
  * Column with two 1s connects check u and check v with weight w_q.
  * Column with one 1 connects check u to virtual boundary B with weight w_q.
- Computes all-pairs shortest paths using Dijkstra's algorithm with exact integer/rational weights.
"""

from __future__ import annotations

import heapq
from typing import Dict, List, Tuple


class DecodingGraph:
    """Graph of checks and boundary with qubit edges."""

    def __init__(self, hz: List[List[int]], weights: List[int]) -> None:
        self.m = len(hz)
        self.n = len(hz[0]) if self.m > 0 else 0
        self.weights = list(weights)
        self.boundary_node = self.m  # Index of virtual boundary
        self.has_boundary = False

        # Adjacency list: u -> list of (v, weight, qubit_index)
        self.adj: Dict[int, List[Tuple[int, int, int]]] = {i: [] for i in range(self.m + 1)}

        for q in range(self.n):
            w = self.weights[q]
            ones = [r for r in range(self.m) if hz[r][q] == 1]
            if len(ones) == 2:
                u, v = ones[0], ones[1]
                self.adj[u].append((v, w, q))
                self.adj[v].append((u, w, q))
            elif len(ones) == 1:
                u = ones[0]
                self.has_boundary = True
                self.adj[u].append((self.boundary_node, w, q))
                self.adj[self.boundary_node].append((u, w, q))

    def shortest_path(self, start: int, target: int) -> Tuple[int, List[int]]:
        """
        Dijkstra shortest path from start to target.
        Returns (distance, list_of_qubit_indices).
        """
        if start == target:
            return 0, []

        dist: Dict[int, int] = {start: 0}
        parent: Dict[int, Tuple[int, int]] = {}  # v -> (u, qubit_idx)
        pq = [(0, start)]

        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, float("inf")):
                continue
            if u == target:
                break

            for v, w, q in self.adj[u]:
                new_d = d + w
                if new_d < dist.get(v, float("inf")):
                    dist[v] = new_d
                    parent[v] = (u, q)
                    heapq.heappush(pq, (new_d, v))

        if target not in dist:
            return -1, []

        # Reconstruct path
        path_qubits: List[int] = []
        curr = target
        while curr != start:
            prev, q = parent[curr]
            path_qubits.append(q)
            curr = prev
        path_qubits.reverse()
        return dist[target], path_qubits
