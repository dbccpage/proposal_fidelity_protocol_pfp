"""Exact Rational Optimal Transport and Kantorovich Dual Potential Solver.

Solves the Monge-Kantorovich transportation problem in exact rational arithmetic
using pure Python standard library fractions.Fraction.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import defaultdict, deque
from fractions import Fraction
from typing import Any, Mapping


def is_exact_int(val: Any) -> bool:
    """Strict check for int, rejecting bool."""
    return type(val) is int and not isinstance(val, bool)


def format_rational(frac: Fraction) -> str:
    """Formats a Fraction into canonical reduced rational string format ('int' or 'num/den')."""
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def parse_rational(val: Any) -> Fraction:
    """Parses an int, str, or Fraction into an exact Fraction, rejecting bool and float."""
    if isinstance(val, bool):
        raise TypeError("Boolean value rejected")
    if isinstance(val, float):
        raise TypeError("Float values rejected: zero-float policy")
    if isinstance(val, int):
        return Fraction(val, 1)
    if isinstance(val, Fraction):
        return val
    if isinstance(val, str):
        # Must be valid rational string 'a' or 'a/b'
        val = val.strip()
        if "/" in val:
            parts = val.split("/")
            if len(parts) != 2:
                raise ValueError(f"Malformed rational string: {val}")
            num_str, den_str = parts[0].strip(), parts[1].strip()
            num = int(num_str)
            den = int(den_str)
            if den == 0:
                raise ZeroDivisionError("Denominator cannot be zero")
            return Fraction(num, den)
        else:
            return Fraction(int(val), 1)
    raise TypeError(f"Unsupported rational type: {type(val)}")


def exact_optimal_transport_primal_dual(
    sources: list[int],
    sinks: list[int],
    supply: Mapping[int, Fraction],
    demand: Mapping[int, Fraction],
    cost: Mapping[tuple[int, int], int],
) -> tuple[Fraction, dict[tuple[int, int], Fraction], dict[int, Fraction], dict[int, Fraction]]:
    """Solves exact bipartite transportation problem via the Primal-Dual algorithm.

    Minimizes sum_{i, j} pi(i, j) * cost(i, j) subject to:
      sum_j pi(i, j) = supply(i) for all i in sources
      sum_i pi(i, j) = demand(j) for all j in sinks
      pi(i, j) >= 0

    Returns:
      (W_1, active_plan, u, v) where active_plan contains entries with pi(i, j) > 0.
    """
    # Verify balance
    tot_supply = sum(supply.values())
    tot_demand = sum(demand.values())
    if tot_supply != tot_demand:
        raise ValueError(
            f"Unbalanced transportation problem: supply {tot_supply} != demand {tot_demand}"
        )

    # Dual potentials u_i, v_j satisfying u_i - v_j <= cost(i, j)
    # Initial dual feasible solution:
    u = {i: min(cost[i, j] for j in sinks) for i in sources}
    v = {j: Fraction(0) for j in sinks}

    # Flows pi[i, j]
    flow: dict[tuple[int, int], Fraction] = defaultdict(Fraction)
    source_deficit = {i: supply[i] for i in sources}
    sink_deficit = {j: demand[j] for j in sinks}

    max_iter = 10000
    iteration = 0

    while True:
        iteration += 1
        if iteration > max_iter:
            raise RuntimeError("Primal-dual algorithm exceeded maximum iterations")

        # Check termination: all supply satisfied
        if sum(source_deficit.values()) == 0:
            break

        # BFS on residual equality network
        visited_sources: set[int] = set()
        visited_sinks: set[int] = set()
        parent: dict[tuple[str, int], tuple[str, int]] = {}

        q: deque[tuple[str, int]] = deque()
        for i in sources:
            if source_deficit[i] > 0:
                visited_sources.add(i)
                q.append(("source", i))

        sink_reached: int | None = None
        while q:
            node_type, node_id = q.popleft()
            if node_type == "source":
                i = node_id
                for j in sinks:
                    if j not in visited_sinks:
                        # Equality edge: u_i - v_j == cost[i, j]
                        if u[i] - v[j] == cost[i, j]:
                            visited_sinks.add(j)
                            parent[("sink", j)] = ("source", i)
                            if sink_deficit[j] > 0:
                                sink_reached = j
                                break
                            q.append(("sink", j))
                if sink_reached is not None:
                    break
            else:
                j = node_id
                for i in sources:
                    if i not in visited_sources:
                        # Backward edge allowed if flow[i, j] > 0
                        if flow[i, j] > 0:
                            visited_sources.add(i)
                            parent[("source", i)] = ("sink", j)
                            q.append(("source", i))

        if sink_reached is not None:
            # Trace augmenting path and compute bottleneck
            path: list[tuple[tuple[str, int], tuple[str, int]]] = []
            curr: tuple[str, int] = ("sink", sink_reached)
            bottleneck = sink_deficit[sink_reached]

            while curr in parent:
                prev = parent[curr]
                path.append((prev, curr))
                if prev[0] == "sink" and curr[0] == "source":
                    # backward edge: capacity is flow[curr[1], prev[1]]
                    b_flow = flow[curr[1], prev[1]]
                    if b_flow < bottleneck:
                        bottleneck = b_flow
                curr = prev

            start_source = curr[1]
            if source_deficit[start_source] < bottleneck:
                bottleneck = source_deficit[start_source]

            # Augment flow along path
            for prev, nxt in path:
                if prev[0] == "source" and nxt[0] == "sink":
                    src = prev[1]
                    snk = nxt[1]
                    flow[src, snk] += bottleneck
                else:
                    snk = prev[1]
                    src = nxt[1]
                    flow[src, snk] -= bottleneck

            source_deficit[start_source] -= bottleneck
            sink_deficit[sink_reached] -= bottleneck

        else:
            # Dual adjustment
            delta: Fraction | None = None
            for i in visited_sources:
                for j in sinks:
                    if j not in visited_sinks:
                        slack = cost[i, j] - (u[i] - v[j])
                        if slack > 0:
                            if delta is None or slack < delta:
                                delta = slack

            if delta is None:
                raise RuntimeError(
                    "Failed to compute dual adjustment: graph disconnected or unbalanced"
                )

            for i in visited_sources:
                u[i] += delta
            for j in visited_sinks:
                v[j] += delta

    w_1 = sum(flow[i, j] * cost[i, j] for i in sources for j in sinks if flow[i, j] > 0)
    active_plan = {(i, j): flow[i, j] for i in sources for j in sinks if flow[i, j] > 0}
    return w_1, active_plan, u, v


def compute_kantorovich_potential_on_graph(
    all_vertices: list[int],
    edges: list[tuple[int, int]],
    active_plan: Mapping[tuple[int, int], Fraction],
    distances: Mapping[int, Mapping[int, int]],
) -> dict[int, int]:
    """Computes an exact integer 1-Lipschitz Kantorovich potential phi on all V(G).

    Constraints:
      1. For each edge (a, b) in E: |phi(a) - phi(b)| <= 1
      2. For each (i, j) with pi(i, j) > 0: phi(i) - phi(j) = d(i, j)
         which is enforced via phi(j) - phi(i) <= -d(i, j) in the difference constraint system.

    Returns:
      phi: dict of vertex_id -> integer potential value, normalized so min(phi) = 0.
    """
    adj: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for a, b in edges:
        adj[b].append((a, 1))  # phi(a) - phi(b) <= 1
        adj[a].append((b, 1))  # phi(b) - phi(a) <= 1

    for (i, j), mass in active_plan.items():
        if mass > 0:
            d_ij = distances[i][j]
            adj[i].append((j, -d_ij))  # phi(j) - phi(i) <= -d_ij

    phi = {v: 0 for v in all_vertices}
    num_v = len(all_vertices)

    for _ in range(num_v):
        updated = False
        for u in all_vertices:
            for v, w in adj[u]:
                if phi[u] + w < phi[v]:
                    phi[v] = phi[u] + w
                    updated = True
        if not updated:
            break
    else:
        # Check negative cycle
        for u in all_vertices:
            for v, w in adj[u]:
                if phi[u] + w < phi[v]:
                    raise RuntimeError("Negative cycle detected in Kantorovich constraint graph")

    min_val = min(phi.values())
    normalized_phi = {v: phi[v] - min_val for v in all_vertices}
    return normalized_phi
