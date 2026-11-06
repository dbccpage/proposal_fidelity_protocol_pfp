"""Graph algorithms for C018: 2-connected blocks, cycles, and local switching."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


def parse_graph(
    case: dict[str, Any],
) -> tuple[list[str], list[tuple[str, str, int]], dict[tuple[str, str], int]]:
    """Parse vertices, undirected edges with signs (+1 or -1).

    Edges are stored canonically with u < v.
    """
    vertices = list(case.get("vertices", []))
    raw_edges = case.get("edges", [])
    edge_list: list[tuple[str, str, int]] = []
    edge_dict: dict[tuple[str, str], int] = {}

    for e in raw_edges:
        u = str(e[0])
        v = str(e[1])
        sign = int(e[2]) if len(e) > 2 else 1
        if u == v:
            # Self-loop
            raise ValueError(f"SELF_LOOP:{u}")
        if sign not in (1, -1):
            raise ValueError(f"INVALID_SIGN:{sign}")
        u_can, v_can = (u, v) if u < v else (v, u)
        edge_list.append((u_can, v_can, sign))
        edge_dict[(u_can, v_can)] = sign

    return vertices, edge_list, edge_dict


def find_biconnected_components(
    vertices: list[str],
    edges: list[tuple[str, str, int]],
) -> list[list[tuple[str, str, int]]]:
    """Find 2-connected blocks (biconnected components of edges)."""
    adj: dict[str, list[tuple[str, int]]] = defaultdict(list)
    edge_map: dict[tuple[str, str], tuple[str, str, int]] = {}

    for u, v, s in edges:
        adj[u].append((v, s))
        adj[v].append((u, s))
        u_can, v_can = (u, v) if u < v else (v, u)
        edge_map[(u_can, v_can)] = (u_can, v_can, s)

    tin: dict[str, int] = {}
    low: dict[str, int] = {}
    timer = 0
    stack: list[tuple[str, str]] = []
    blocks: list[list[tuple[str, str, int]]] = []

    def dfs(u: str, p: str | None = None) -> None:
        nonlocal timer
        timer += 1
        tin[u] = low[u] = timer
        for to, _ in adj[u]:
            if to == p:
                continue
            if to in tin:
                low[u] = min(low[u], tin[to])
                if tin[to] < tin[u]:
                    stack.append((u, to))
            else:
                stack.append((u, to))
                dfs(to, u)
                low[u] = min(low[u], low[to])
                if low[to] >= tin[u]:
                    # u is an articulation point, pop block
                    block_edges: list[tuple[str, str, int]] = []
                    while stack:
                        e = stack.pop()
                        u_can, v_can = (e[0], e[1]) if e[0] < e[1] else (e[1], e[0])
                        if (u_can, v_can) in edge_map:
                            block_edges.append(edge_map[(u_can, v_can)])
                        if e == (u, to) or e == (to, u):
                            break
                    if block_edges:
                        blocks.append(block_edges)

    for v in vertices:
        if v not in tin:
            dfs(v, None)

    return blocks


def count_negative_edges(
    edges: list[tuple[str, str, int]],
    switching: dict[str, int],
) -> tuple[int, list[list[str]]]:
    """Calculate number of negative edges under switching s: V -> {+1, -1}."""
    neg_count = 0
    deleted: list[list[str]] = []
    for u, v, s in edges:
        s_u = switching.get(u, 1)
        s_v = switching.get(v, 1)
        switched_sign = s_u * s * s_v
        if switched_sign == -1:
            neg_count += 1
            deleted.append([u, v])
    return neg_count, deleted


def find_negative_cycle_packing(
    vertices: list[str],
    edges: list[tuple[str, str, int]],
) -> list[list[str]]:
    """Greedy search for edge-disjoint cycles with odd number of negative edges."""
    remaining_edges = list(edges)
    packing: list[list[str]] = []

    while True:
        # Build adjacency with remaining edges
        adj: dict[str, list[tuple[str, int, int]]] = defaultdict(list)
        for idx, (u, v, s) in enumerate(remaining_edges):
            adj[u].append((v, s, idx))
            adj[v].append((u, s, idx))

        # BFS for shortest odd-negative cycle
        found_cycle: list[int] | None = None
        cycle_nodes: list[str] | None = None

        # State in BFS: (current_node, parity_of_negatives: 0 or 1)
        # To avoid reversing along same edge, track edge_idx
        for start in vertices:
            if found_cycle is not None:
                break
            # dist[(node, parity)] = (parent_node, parent_parity, edge_idx)
            parent: dict[tuple[str, int], tuple[str, int, int] | None] = {(start, 0): None}
            queue = deque([(start, 0)])

            while queue:
                curr, par = queue.popleft()
                for nxt, sign, e_idx in adj[curr]:
                    nxt_par = par ^ (1 if sign == -1 else 0)
                    if nxt == start and nxt_par == 1:
                        # Found odd cycle back to start!
                        # Reconstruct path
                        path_edges = [e_idx]
                        path_nodes = [start]
                        step = (curr, par)
                        while step is not None and step[0] != start:
                            p_info = parent[step]
                            if p_info is None:
                                break
                            p_node, p_par, p_eidx = p_info
                            path_edges.append(p_eidx)
                            path_nodes.append(step[0])
                            step = (p_node, p_par)
                        found_cycle = path_edges
                        cycle_nodes = list(reversed(path_nodes))
                        break

                    if (nxt, nxt_par) not in parent:
                        parent[(nxt, nxt_par)] = (curr, par, e_idx)
                        queue.append((nxt, nxt_par))
                if found_cycle is not None:
                    break

        if found_cycle is None:
            break

        # Record cycle and remove its edges
        packing.append(cycle_nodes)
        used_indices = set(found_cycle)
        remaining_edges = [e for i, e in enumerate(remaining_edges) if i not in used_indices]

    return packing


def solve_exhaustive(
    vertices: list[str],
    edges: list[tuple[str, str, int]],
) -> tuple[int, dict[str, int]]:
    """Solve frustration index exactly by exhaustively checking 2^{|V|-1} switchings."""
    n = len(vertices)
    if n == 0:
        return 0, {}
    if n > 20:
        raise ValueError("Exhaustive solve only supported for |V| <= 20")

    best_l = len(edges) + 1
    best_switching: dict[str, int] = {}
    v0 = vertices[0]
    other_v = vertices[1:]

    # Fix v0 switching to +1 to break Z/2 symmetry
    for mask in range(1 << len(other_v)):
        switching = {v0: 1}
        for i, v in enumerate(other_v):
            switching[v] = -1 if ((mask >> i) & 1) else 1
        l, _ = count_negative_edges(edges, switching)
        if l < best_l:
            best_l = l
            best_switching = switching
            if best_l == 0:
                break

    return best_l, best_switching


def local_search_switching(
    vertices: list[str],
    edges: list[tuple[str, str, int]],
    max_passes: int | None = None,
) -> tuple[int, dict[str, int]]:
    """Local descent search: flip vertex sign if it strictly lowers negative edge count.

    Runs to a local optimum by default (each flip lowers the count, so it terminates);
    the judge rejects an UNKNOWN whose switching still has an improving flip.
    """
    adj: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for u, v, s in edges:
        adj[u].append((v, s))
        adj[v].append((u, s))

    switching = {v: 1 for v in vertices}
    best_l, _ = count_negative_edges(edges, switching)

    improved = True
    passes = 0
    while improved and (max_passes is None or passes < max_passes):
        improved = False
        passes += 1
        for v in vertices:
            # Check delta if we flip v
            curr_s = switching[v]
            # Net negative incident edges
            neg_before = 0
            neg_after = 0
            for to, s in adj[v]:
                to_s = switching[to]
                if curr_s * s * to_s == -1:
                    neg_before += 1
                else:
                    neg_after += 1
            if neg_after < neg_before:
                switching[v] = -curr_s
                best_l -= neg_before - neg_after
                improved = True

    return best_l, switching
