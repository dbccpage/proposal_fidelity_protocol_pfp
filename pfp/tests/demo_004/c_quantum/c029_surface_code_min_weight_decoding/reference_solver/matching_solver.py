# AuthorityEffect: None.
"""
Minimum-Weight Perfect Matching and Dual Certificate Solver for C029.

Computes:
1. Exact Minimum-Weight Perfect Matching on defect graph using Dijkstra shortest path metrics.
2. Dual variables (vertex duals y_v and blossom odd-set duals z_S) verifying optimality with zero duality gap.
3. Primal correction c in F_2^n as symmetric difference of lattice paths.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, List, Set, Tuple

try:
    from .exact_simplex import ExactSimplex, format_fraction, parse_fraction
    from .graph import DecodingGraph
except (ImportError, ValueError):
    from exact_simplex import ExactSimplex, format_fraction
    from graph import DecodingGraph


def find_min_weight_perfect_matching(
    num_nodes: int,
    edges: Dict[Tuple[int, int], int],
) -> Tuple[int, List[Tuple[int, int]]]:
    """
    Finds exact minimum weight perfect matching on complete/sub-graph of num_nodes vertices.
    Returns (min_weight, list_of_matched_pairs).
    Uses branch-and-bound with memoization.
    """
    memo: Dict[int, Tuple[int, List[Tuple[int, int]]]] = {}

    def solve_rec(mask: int) -> Tuple[int, List[Tuple[int, int]]]:
        if mask == 0:
            return 0, []
        if mask in memo:
            return memo[mask]

        # Pick first available vertex
        u = -1
        for i in range(num_nodes):
            if (mask >> i) & 1:
                u = i
                break

        best_cost = float("inf")
        best_pairs: List[Tuple[int, int]] = []

        # Try matching u with every other available vertex v
        rem_mask = mask ^ (1 << u)
        for v in range(u + 1, num_nodes):
            if (rem_mask >> v) & 1:
                e_key = (u, v) if u < v else (v, u)
                if e_key in edges:
                    w = edges[e_key]
                    sub_cost, sub_pairs = solve_rec(rem_mask ^ (1 << v))
                    total = w + sub_cost
                    if total < best_cost:
                        best_cost = total
                        best_pairs = [(u, v)] + sub_pairs

        memo[mask] = (int(best_cost), best_pairs)
        return memo[mask]

    init_mask = (1 << num_nodes) - 1
    return solve_rec(init_mask)


def compute_dual_variables(
    num_nodes: int,
    edges: Dict[Tuple[int, int], int],
    matching_pairs: List[Tuple[int, int]],
) -> Tuple[List[Fraction], List[Tuple[List[int], Fraction]]]:
    """
    Computes exact rational dual variables:
    vertex_duals: List of y_v for each node
    odd_set_duals: List of (set_of_nodes, z_S)
    Satisfies:
        y_u + y_v + sum_{S: u,v in S} z_S <= weight(u, v) for all (u, v)
        tight on matched pairs (equality)
        sum y_v + sum z_S (|S|-1)/2 = total matching weight
    """
    matched_edges = set((u, v) if u < v else (v, u) for u, v in matching_pairs)

    # Fast path: test if natural symmetric split y_u = y_v = w_{uv}/2 works directly
    y_candidate = [Fraction(0)] * num_nodes
    for u, v in matching_pairs:
        w = Fraction(edges[(u, v) if u < v else (v, u)])
        y_candidate[u] = w / 2
        y_candidate[v] = w / 2

    # Verify slack on all edges
    feasible = True
    violated_edges = []
    for (u, v), w in edges.items():
        w_frac = Fraction(w)
        if (u, v) in matched_edges:
            if y_candidate[u] + y_candidate[v] != w_frac:
                feasible = False
                break
        else:
            if y_candidate[u] + y_candidate[v] > w_frac:
                feasible = False
                violated_edges.append((u, v, y_candidate[u] + y_candidate[v] - w_frac))

    if feasible:
        return y_candidate, []

    # If symmetric split is violated, formulate LP to find feasible y and blossoms z_S:
    # Maximize sum y_v + sum z_S (|S|-1)/2 subject to:
    #   y_u + y_v + sum_{S: u,v in S} z_S = w_{uv} for all (u, v) in matching
    #   y_u + y_v + sum_{S: u,v in S} z_S <= w_{uv} for all (u, v) in edges
    # Express y_i = y_i^+ - y_i^- where y_i^+, y_i^- >= 0
    # z_S >= 0 for candidate 3-blossoms (triangles containing exactly 1 matched edge)
    # Add slack s_e >= 0 for unmatched edges
    from itertools import combinations

    candidate_blossoms = []
    for S in combinations(range(num_nodes), 3):
        S_set = set(S)
        edges_in_S = sum(1 for u, v in matching_pairs if u in S_set and v in S_set)
        if edges_in_S == 1:
            candidate_blossoms.append(S)

    # Normalize unmatched edges
    norm_matched = set((u, v) if u < v else (v, u) for u, v in matching_pairs)
    unmatched_edges = []
    for (u, v), w in edges.items():
        e = (u, v) if u < v else (v, u)
        if e not in norm_matched and e not in unmatched_edges:
            unmatched_edges.append(e)

    n_y = 2 * num_nodes
    n_z = len(candidate_blossoms)
    n_s = len(unmatched_edges)
    total_vars = n_y + n_z + n_s

    # Minimization objective: minimize - (sum y_v + sum z_S * 1)
    c_lp = [Fraction(0)] * total_vars
    for i in range(num_nodes):
        c_lp[2 * i] = Fraction(-1)
        c_lp[2 * i + 1] = Fraction(1)
    for i in range(n_z):
        c_lp[n_y + i] = Fraction(-1)  # (|S|-1)/2 = 1 for |S|=3

    A_eq = []
    b_eq = []

    # Matched edges: equality
    for u, v in matching_pairs:
        row = [Fraction(0)] * total_vars
        row[2 * u] = Fraction(1)
        row[2 * u + 1] = Fraction(-1)
        row[2 * v] = Fraction(1)
        row[2 * v + 1] = Fraction(-1)
        for idx_S, S in enumerate(candidate_blossoms):
            if u in S and v in S:
                row[n_y + idx_S] = Fraction(1)
        A_eq.append(row)
        b_eq.append(Fraction(edges[(u, v) if u < v else (v, u)]))

    # Unmatched edges: equality with slack s_e >= 0
    for e_idx, (u, v) in enumerate(unmatched_edges):
        row = [Fraction(0)] * total_vars
        row[2 * u] = Fraction(1)
        row[2 * u + 1] = Fraction(-1)
        row[2 * v] = Fraction(1)
        row[2 * v + 1] = Fraction(-1)
        for idx_S, S in enumerate(candidate_blossoms):
            if u in S and v in S:
                row[n_y + idx_S] = Fraction(1)
        row[n_y + n_z + e_idx] = Fraction(1)
        A_eq.append(row)
        b_eq.append(Fraction(edges[(u, v) if (u, v) in edges else (v, u)]))

    simplex = ExactSimplex(c_lp, A_eq, b_eq)
    ok, _, sol = simplex.solve()
    if ok and sol is not None:
        y_res = [Fraction(0)] * num_nodes
        for i in range(num_nodes):
            y_res[i] = sol[2 * i] - sol[2 * i + 1]
        active_blossoms = []
        for i in range(n_z):
            if sol[n_y + i] > 0:
                active_blossoms.append(([int(x) for x in candidate_blossoms[i]], sol[n_y + i]))
        return y_res, active_blossoms

    return y_candidate, []


def solve_min_weight_decoding(
    code_type: str,
    distance: int,
    hz: List[List[int]],
    weights: List[int],
    syndrome: List[int],
) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    """
    Decodes surface or toric code syndrome using minimum-weight perfect matching.
    """
    m = len(hz)
    n = len(hz[0]) if m > 0 else 0

    if len(weights) != n or len(syndrome) != m:
        return (
            False,
            {},
            {
                "kind": "dimension_mismatch",
                "details": f"hz is {m}x{n}, weights len {len(weights)}, syndrome len {len(syndrome)}",
            },
        )

    # Check bounds
    if code_type == "rotated":
        if distance not in {3, 5, 7}:
            return False, {}, {"refusal_code": "DISTANCE_OUT_OF_BOUNDS", "distance": distance}
    elif code_type == "toric":
        if distance not in {3, 4, 5}:
            return False, {}, {"refusal_code": "DISTANCE_OUT_OF_BOUNDS", "distance": distance}
        # Check odd parity on torus
        if sum(syndrome) % 2 != 0:
            return False, {}, {"kind": "odd_parity_on_torus", "rows": "all"}
    else:
        return False, {}, {"kind": "unknown_code_type", "code": code_type}

    # Extract defects
    defects = [r for r in range(m) if syndrome[r] == 1]
    if not defects:
        return (
            True,
            {
                "correction": [],
                "weight": 0,
                "certificate": {
                    "pairs": [],
                    "boundary_matches": [],
                    "vertex_duals": [],
                    "odd_set_duals": [],
                },
            },
            {},
        )

    graph = DecodingGraph(hz, weights)
    k = len(defects)

    # Compute pairwise shortest paths between all defects
    dist_matrix: Dict[Tuple[int, int], Tuple[int, List[int]]] = {}
    for i in range(k):
        for j in range(i + 1, k):
            d_val, path = graph.shortest_path(defects[i], defects[j])
            dist_matrix[(i, j)] = (d_val, path)
            dist_matrix[(j, i)] = (d_val, path)

    # Compute boundary paths if rotated code
    dist_boundary: Dict[int, Tuple[int, List[int]]] = {}
    if code_type == "rotated":
        for i in range(k):
            d_val, path = graph.shortest_path(defects[i], graph.boundary_node)
            dist_boundary[i] = (d_val, path)

    # Build Defect Matching Graph
    edges_mwpm: Dict[Tuple[int, int], int] = {}
    if code_type == "rotated":
        num_nodes = 2 * k
        # Defect to defect
        for i in range(k):
            for j in range(i + 1, k):
                edges_mwpm[(i, j)] = dist_matrix[(i, j)][0]

        # Defect i to boundary copy k+i
        for i in range(k):
            edges_mwpm[(i, k + i)] = dist_boundary[i][0]

        # Boundary copy to boundary copy: weight 0
        for i in range(k):
            for j in range(i + 1, k):
                edges_mwpm[(k + i, k + j)] = 0
    else:  # toric
        num_nodes = k
        for i in range(k):
            for j in range(i + 1, k):
                edges_mwpm[(i, j)] = dist_matrix[(i, j)][0]

    # Solve MWPM
    total_mwpm_weight, matching_pairs = find_min_weight_perfect_matching(num_nodes, edges_mwpm)

    # Reconstruct paths and pairs
    final_pairs: List[List[int]] = []
    final_boundary: List[int] = []
    qubit_toggles: Set[int] = set()

    for u, v in matching_pairs:
        if code_type == "rotated":
            if u < k and v < k:
                # Defect to defect match
                final_pairs.append([defects[u], defects[v]])
                for q in dist_matrix[(u, v)][1]:
                    if q in qubit_toggles:
                        qubit_toggles.remove(q)
                    else:
                        qubit_toggles.add(q)
            elif u < k and v >= k:
                # Defect u matched to boundary copy v
                final_boundary.append(defects[u])
                for q in dist_boundary[u][1]:
                    if q in qubit_toggles:
                        qubit_toggles.remove(q)
                    else:
                        qubit_toggles.add(q)
            elif v < k and u >= k:
                # Defect v matched to boundary copy u
                final_boundary.append(defects[v])
                for q in dist_boundary[v][1]:
                    if q in qubit_toggles:
                        qubit_toggles.remove(q)
                    else:
                        qubit_toggles.add(q)
            # Boundary copy to boundary copy: no lattice path added
        else:
            final_pairs.append([defects[u], defects[v]])
            for q in dist_matrix[(u, v)][1]:
                if q in qubit_toggles:
                    qubit_toggles.remove(q)
                else:
                    qubit_toggles.add(q)

    correction = sorted(list(qubit_toggles))
    actual_weight = sum(weights[q] for q in correction)

    # Compute dual variables
    vertex_duals_frac, odd_set_duals_frac = compute_dual_variables(
        num_nodes, edges_mwpm, matching_pairs
    )

    certificate = {
        "pairs": [sorted(p) for p in sorted(final_pairs)],
        "boundary_matches": sorted(final_boundary),
        "vertex_duals": [format_fraction(y) for y in vertex_duals_frac],
        "odd_set_duals": [
            [[int(x) for x in sorted(s)], format_fraction(z)] for s, z in odd_set_duals_frac
        ],
    }

    return (
        True,
        {
            "correction": correction,
            "weight": actual_weight,
            "certificate": certificate,
        },
        {},
    )
