"""Exact integer max-flow and min-cut solver using Dinic's algorithm."""

from collections import deque
from typing import Any, Dict, List, Tuple


class DinicMaxFlow:
    def __init__(self, n: int, s: int, t: int, arcs: List[List[Any]]):
        self.n = n
        self.s = s
        self.t = t
        self.num_arcs = len(arcs)
        self.adj: List[List[Dict[str, Any]]] = [[] for _ in range(n)]
        self.arc_edges: List[Dict[str, Any]] = []

        for arc_idx, arc in enumerate(arcs):
            u = int(arc[0])
            v = int(arc[1])
            cap = int(arc[2])

            # Forward edge
            fwd_idx = len(self.adj[u])
            rev_idx = len(self.adj[v]) + (1 if u == v else 0)

            fwd = {
                "to": v,
                "from": u,
                "cap": cap,
                "flow": 0,
                "arc_idx": arc_idx,
                "is_forward": True,
                "rev_idx": rev_idx,
            }
            rev = {
                "to": u,
                "from": v,
                "cap": 0,
                "flow": 0,
                "arc_idx": arc_idx,
                "is_forward": False,
                "rev_idx": fwd_idx,
            }
            self.adj[u].append(fwd)
            self.adj[v].append(rev)
            self.arc_edges.append(fwd)

    def _bfs_level_graph(self) -> bool:
        self.level = [-1] * self.n
        self.level[self.s] = 0
        q = deque([self.s])
        while q:
            u = q.popleft()
            for edge in self.adj[u]:
                rem = edge["cap"] - edge["flow"]
                v = edge["to"]
                if rem > 0 and self.level[v] == -1:
                    self.level[v] = self.level[u] + 1
                    q.append(v)
        return self.level[self.t] != -1

    def _dfs_blocking_flow(self, u: int, pushed: int) -> int:
        if pushed == 0 or u == self.t:
            return pushed
        for idx in range(self.ptr[u], len(self.adj[u])):
            self.ptr[u] = idx
            edge = self.adj[u][idx]
            v = edge["to"]
            rem = edge["cap"] - edge["flow"]
            if self.level[v] == self.level[u] + 1 and rem > 0:
                tr = self._dfs_blocking_flow(v, min(pushed, rem))
                if tr > 0:
                    edge["flow"] += tr
                    rev_idx = edge["rev_idx"]
                    self.adj[v][rev_idx]["flow"] -= tr
                    return tr
        return 0

    def compute_max_flow(self) -> Tuple[int, List[int], List[int]]:
        flow_val = 0
        INF = 10**32  # Arbitrary-precision large integer
        while self._bfs_level_graph():
            self.ptr = [0] * self.n
            while True:
                pushed = self._dfs_blocking_flow(self.s, INF)
                if pushed == 0:
                    break
                flow_val += pushed

        # Extract arc flows in input order
        arc_flows = [edge["flow"] for edge in self.arc_edges]

        # Extract min-cut S via BFS from source on residual graph
        visited = [False] * self.n
        visited[self.s] = True
        q = deque([self.s])
        while q:
            u = q.popleft()
            for edge in self.adj[u]:
                rem = edge["cap"] - edge["flow"]
                v = edge["to"]
                if rem > 0 and not visited[v]:
                    visited[v] = True
                    q.append(v)

        cut_S = [i for i in range(self.n) if visited[i]]
        return flow_val, arc_flows, cut_S
