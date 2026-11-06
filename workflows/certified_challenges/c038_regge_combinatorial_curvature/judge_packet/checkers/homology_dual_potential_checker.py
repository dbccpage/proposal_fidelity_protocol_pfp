"""Checker 2: Homology Dual Potential Verifier for Challenge C038.

Evaluates surface invariants via simplicial homology over Q (Betti numbers B_0, B_1, B_2,
top homology orientability B_2 == 1, discrete angle deficits). Evaluates graph curvature
via Kantorovich dual potential 1-Lipschitz condition, dual objective D, zero duality gap,
and integer-scaled successive shortest path min-cost flow.

Shares ZERO code with Checker 1.
AuthorityEffect: None.
"""

from __future__ import annotations

import heapq
import math
from fractions import Fraction
from typing import Any, Mapping

# -------------------------------------------------------------------------
# Checker 2 Private Type Guards & Rational Validators
# -------------------------------------------------------------------------


def _c2_is_int(val: Any) -> bool:
    """Strict check for int, rejecting bool."""
    return type(val) is int and not isinstance(val, bool)


def _c2_is_integer_str(val: Any) -> bool:
    """Checks if val is an exact integer string without decimals."""
    if type(val) is not str:
        return False
    if "." in val or "e" in val.lower() or "/" in val:
        return False
    s = val.lstrip("-")
    return s.isdigit() and len(s) > 0


def _c2_is_reduced_rational_str(val: Any) -> bool:
    """Checks if val is a canonical reduced rational string 'p/q' or integer string."""
    if type(val) is not str:
        return False
    if "." in val or "e" in val.lower():
        return False
    if "/" in val:
        parts = val.split("/")
        if len(parts) != 2:
            return False
        num_s, den_s = parts
        if not _c2_is_integer_str(num_s) or not den_s.isdigit():
            return False
        den = int(den_s)
        if den <= 1:
            return False
        num = int(num_s)
        if math.gcd(abs(num), den) != 1:
            return False
        return True
    return _c2_is_integer_str(val)


def _c2_to_reduced_str(frac: Fraction) -> str:
    """Formats a Fraction as a canonical reduced string."""
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def _c2_verify_refusal_warranted(case: Mapping[str, Any], refusal_code: str) -> tuple[bool, str]:
    """Validates that a claimed UNKNOWN refusal code is defect-grounded and warranted in Checker 2."""
    valid_codes = frozenset(
        {
            "TOO_MANY_TRIANGLES",
            "GRAPH_TOO_LARGE",
            "INVALID_ALPHA",
            "MALFORMED_CASE_STRUCTURE",
        }
    )
    if refusal_code not in valid_codes:
        return False, f"FAIL (C2): unrecognized refusal code {refusal_code!r}"

    if not isinstance(case, Mapping):
        if refusal_code == "MALFORMED_CASE_STRUCTURE":
            return True, "PASS (C2): valid UNKNOWN refusal for non-Mapping case"
        return (
            False,
            f"FAIL (C2): non-Mapping case requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
        )

    query = case.get("query")
    if query not in ("surface", "graph"):
        if refusal_code == "MALFORMED_CASE_STRUCTURE":
            return True, "PASS (C2): valid UNKNOWN refusal for invalid query"
        return (
            False,
            f"FAIL (C2): invalid query requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
        )

    if query == "surface":
        triangles = case.get("triangles")
        if not isinstance(triangles, list) or len(triangles) == 0:
            if refusal_code == "MALFORMED_CASE_STRUCTURE":
                return True, "PASS (C2): valid UNKNOWN refusal for malformed/empty triangles list"
            return (
                False,
                f"FAIL (C2): malformed triangles requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
            )

        if len(triangles) > 200:
            if refusal_code == "TOO_MANY_TRIANGLES":
                return True, "PASS (C2): valid UNKNOWN refusal for TOO_MANY_TRIANGLES"
            return (
                False,
                f"FAIL (C2): > 200 triangles requires TOO_MANY_TRIANGLES, got {refusal_code}",
            )

        for t in triangles:
            if not (isinstance(t, (list, tuple)) and len(t) == 3):
                if refusal_code == "MALFORMED_CASE_STRUCTURE":
                    return True, "PASS (C2): valid UNKNOWN refusal for malformed triangle length"
                return (
                    False,
                    f"FAIL (C2): malformed triangle length requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
                )
            for v in t:
                if not _c2_is_int(v):
                    if refusal_code == "MALFORMED_CASE_STRUCTURE":
                        return True, "PASS (C2): valid UNKNOWN refusal for non-integer vertex"
                    return (
                        False,
                        f"FAIL (C2): non-integer vertex requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
                    )
            u, v, w = t[0], t[1], t[2]
            if u == v or v == w or w == u:
                if refusal_code == "MALFORMED_CASE_STRUCTURE":
                    return True, "PASS (C2): valid UNKNOWN refusal for degenerate triangle"
                return (
                    False,
                    f"FAIL (C2): degenerate triangle requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
                )

        return (
            False,
            f"FAIL (C2): unwarranted UNKNOWN refusal ({refusal_code}) on syntactically valid surface",
        )

    if query == "graph":
        if "alpha" not in case:
            if refusal_code == "MALFORMED_CASE_STRUCTURE":
                return True, "PASS (C2): valid UNKNOWN refusal for missing alpha"
            return (
                False,
                f"FAIL (C2): missing alpha requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
            )

        alpha_raw = case["alpha"]
        alpha_str = str(alpha_raw) if alpha_raw is not None else ""
        if not _c2_is_reduced_rational_str(alpha_str):
            if refusal_code == "INVALID_ALPHA":
                return True, "PASS (C2): valid UNKNOWN refusal for non-rational alpha"
            return (
                False,
                f"FAIL (C2): non-rational alpha requires INVALID_ALPHA, got {refusal_code}",
            )

        alpha_val = Fraction(alpha_str)
        if alpha_val < 0 or alpha_val >= 1:
            if refusal_code == "INVALID_ALPHA":
                return True, "PASS (C2): valid UNKNOWN refusal for alpha out of [0, 1) bounds"
            return (
                False,
                f"FAIL (C2): out of bounds alpha requires INVALID_ALPHA, got {refusal_code}",
            )

        edges_raw = case.get("edges")
        if not isinstance(edges_raw, list) or len(edges_raw) == 0:
            if refusal_code == "MALFORMED_CASE_STRUCTURE":
                return True, "PASS (C2): valid UNKNOWN refusal for malformed/empty edges list"
            return (
                False,
                f"FAIL (C2): malformed edges requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
            )

        cleaned_edges: set[tuple[int, int]] = set()
        vertex_set: set[int] = set()
        for e in edges_raw:
            if not (isinstance(e, (list, tuple)) and len(e) == 2):
                if refusal_code == "MALFORMED_CASE_STRUCTURE":
                    return True, "PASS (C2): valid UNKNOWN refusal for malformed edge length"
                return (
                    False,
                    f"FAIL (C2): malformed edge length requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
                )
            u, v = e[0], e[1]
            if not (_c2_is_int(u) and _c2_is_int(v)):
                if refusal_code == "MALFORMED_CASE_STRUCTURE":
                    return True, "PASS (C2): valid UNKNOWN refusal for non-integer edge vertices"
                return (
                    False,
                    f"FAIL (C2): non-integer edge vertices requires MALFORMED_CASE_STRUCTURE, got {refusal_code}",
                )

            if u != v:
                cleaned_edges.add((min(u, v), max(u, v)))
                vertex_set.add(u)
                vertex_set.add(v)

        if len(vertex_set) > 60 or len(cleaned_edges) > 200:
            if refusal_code == "GRAPH_TOO_LARGE":
                return True, "PASS (C2): valid UNKNOWN refusal for GRAPH_TOO_LARGE"
            return (
                False,
                f"FAIL (C2): graph size bounds exceeded requires GRAPH_TOO_LARGE, got {refusal_code}",
            )

        return (
            False,
            f"FAIL (C2): unwarranted UNKNOWN refusal ({refusal_code}) on syntactically valid graph within bounds",
        )

    return False, "FAIL (C2): refusal verification fell through"


# -------------------------------------------------------------------------
# Checker 2 Exact Gaussian Row Reduction over Q
# -------------------------------------------------------------------------


def _c2_matrix_rank_q(matrix: list[list[Fraction]]) -> int:
    """Computes exact matrix rank over Q using Gaussian elimination."""
    if not matrix or not matrix[0]:
        return 0
    nrows = len(matrix)
    ncols = len(matrix[0])
    mat = [[val for val in row] for row in matrix]

    row = 0
    col = 0
    while row < nrows and col < ncols:
        pivot_row = None
        for r in range(row, nrows):
            if mat[r][col] != 0:
                pivot_row = r
                break
        if pivot_row is None:
            col += 1
            continue
        # Swap rows
        mat[row], mat[pivot_row] = mat[pivot_row], mat[row]
        pivot_val = mat[row][col]
        # Eliminate below
        for r in range(row + 1, nrows):
            if mat[r][col] != 0:
                factor = mat[r][col] / pivot_val
                for c in range(col, ncols):
                    mat[r][c] -= factor * mat[row][c]
        row += 1
        col += 1

    return row


# -------------------------------------------------------------------------
# Checker 2 Simplicial Homology Pipeline
# -------------------------------------------------------------------------


def _c2_compute_simplicial_homology(
    triangles: list[Any],
) -> tuple[int, int, int, bool, int, dict[str, Any] | None]:
    """Computes Betti numbers B0, B1, B2 and checks 2-manifold hypothesis via homology."""
    v_set = set()
    e_counts: dict[tuple[int, int], int] = {}
    norm_faces = []
    v_to_triangles: dict[int, list[list[int]]] = {}

    for t in triangles:
        if not (isinstance(t, (list, tuple)) and len(t) == 3):
            return 0, 0, 0, False, 0, "MALFORMED_CASE_STRUCTURE"
        for vert in t:
            if not _c2_is_int(vert):
                return 0, 0, 0, False, 0, "MALFORMED_CASE_STRUCTURE"
            v_set.add(vert)
        u, v, w = t[0], t[1], t[2]
        if u == v or v == w or w == u:
            return 0, 0, 0, False, 0, "MALFORMED_CASE_STRUCTURE"

        norm_faces.append(tuple(sorted([u, v, w])))
        for a, b in [(u, v), (v, w), (w, u)]:
            e = (min(a, b), max(a, b))
            e_counts[e] = e_counts.get(e, 0) + 1

        for vert in (u, v, w):
            if vert not in v_to_triangles:
                v_to_triangles[vert] = []
            v_to_triangles[vert].append(list(t))

    # Check edge incidence count == 2
    for e, cnt in e_counts.items():
        if cnt != 2:
            return (
                0,
                0,
                0,
                False,
                0,
                {
                    "kind": "edge_not_two_triangles",
                    "edge": list(e),
                    "count": cnt,
                },
            )

    # Check vertex link topology: each vertex link must be a single 2-regular cycle
    for v in v_set:
        tris = v_to_triangles.get(v, [])
        link_adj: dict[int, list[int]] = {}
        for t_item in tris:
            other = [x for x in t_item if x != v]
            if len(other) != 2:
                continue
            for nbr, peer in [(other[0], other[1]), (other[1], other[0])]:
                if nbr not in link_adj:
                    link_adj[nbr] = []
                link_adj[nbr].append(peer)

        if len(link_adj) < 3:
            return (
                0,
                0,
                0,
                False,
                0,
                {
                    "kind": "vertex_link_not_a_cycle",
                    "vertex": v,
                },
            )

        for l_node, peers in link_adj.items():
            if len(peers) != 2:
                return (
                    0,
                    0,
                    0,
                    False,
                    0,
                    {
                        "kind": "vertex_link_not_a_cycle",
                        "vertex": v,
                    },
                )

        start_node = next(iter(link_adj.keys()))
        visited = set()
        curr = start_node
        prev = None
        while curr not in visited:
            visited.add(curr)
            peers = link_adj[curr]
            next_node = peers[0] if peers[0] != prev else peers[1]
            prev = curr
            curr = next_node
        if len(visited) != len(link_adj):
            return (
                0,
                0,
                0,
                False,
                0,
                {
                    "kind": "vertex_link_not_a_cycle",
                    "vertex": v,
                },
            )

    sorted_v = sorted(list(v_set))
    sorted_e = sorted(list(e_counts.keys()))
    sorted_f = sorted(list(set(norm_faces)))

    nV = len(sorted_v)
    nE = len(sorted_e)
    nF = len(sorted_f)

    v_idx = {v: i for i, v in enumerate(sorted_v)}
    e_idx = {e: i for i, e in enumerate(sorted_e)}

    # Construct d1: C1 -> C0 (size nV x nE)
    d1 = [[Fraction(0) for _ in range(nE)] for _ in range(nV)]
    for j, (u, w) in enumerate(sorted_e):
        d1[v_idx[u]][j] = Fraction(-1)
        d1[v_idx[w]][j] = Fraction(1)

    # Construct d2: C2 -> C1 (size nE x nF)
    d2 = [[Fraction(0) for _ in range(nF)] for _ in range(nE)]
    for k, (a, b, c) in enumerate(sorted_f):
        e_bc = (min(b, c), max(b, c))
        e_ac = (min(a, c), max(a, c))
        e_ab = (min(a, b), max(a, b))
        d2[e_idx[e_bc]][k] += Fraction(1)
        d2[e_idx[e_ac]][k] -= Fraction(1)
        d2[e_idx[e_ab]][k] += Fraction(1)

    # Compute ranks
    r1 = _c2_matrix_rank_q(d1)
    r2 = _c2_matrix_rank_q(d2)

    B0 = nV - r1
    B1 = nE - r1 - r2
    B2 = nF - r2
    chi_homology = B0 - B1 + B2

    # In a connected closed surface, B0 == 1
    if B0 != 1:
        return 0, 0, 0, False, 0, {"kind": "surface_disconnected"}

    # Orientability via top homology over Q: B2 == 1 iff orientable
    is_orientable = B2 == 1

    return B0, B1, B2, is_orientable, chi_homology, None


def _c2_verify_surface_answer(
    case: Mapping[str, Any], answer: Mapping[str, Any]
) -> tuple[bool, str]:
    """Verifies surface query answer against Checker 2 homology criteria."""
    status = answer.get("status")
    triangles = case.get("triangles")

    # Closed schema whitelist for surface answers
    if status == "SOLVED":
        allowed_keys = {
            "id",
            "case_id",
            "status",
            "V",
            "E",
            "F",
            "euler",
            "orientable",
            "classification",
            "vertex_curvature",
        }
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C2): unexpected key '{k}' in SOLVED answer"
    elif status == "OUT_OF_SCOPE":
        allowed_keys = {"id", "case_id", "status", "witness"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C2): unexpected key '{k}' in OUT_OF_SCOPE answer"
    elif status == "UNKNOWN":
        allowed_keys = {"id", "case_id", "status", "refusal_code", "refusal"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C2): unexpected key '{k}' in UNKNOWN answer"

    if not isinstance(triangles, list):
        if status == "UNKNOWN":
            ref_code = answer.get("refusal_code") or answer.get("refusal")
            if ref_code == "MALFORMED_CASE_STRUCTURE":
                return True, "PASS (C2): valid UNKNOWN refusal for non-list triangles"
            return (
                False,
                f"FAIL (C2): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
            )
        return False, "FAIL (C2): triangles must be a list"

    if len(triangles) == 0:
        if status != "UNKNOWN":
            return False, "FAIL (C2): empty surface must be UNKNOWN"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if ref_code != "MALFORMED_CASE_STRUCTURE":
            return (
                False,
                f"FAIL (C2): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
            )
        return True, "PASS (C2): empty surface refused"

    if len(triangles) > 200:
        if status != "UNKNOWN":
            return False, "FAIL (C2): > 200 triangles must be UNKNOWN"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if ref_code != "TOO_MANY_TRIANGLES":
            return False, f"FAIL (C2): expected refusal_code 'TOO_MANY_TRIANGLES', got '{ref_code}'"
        return True, "PASS (C2): > 200 triangles refused"

    for t in triangles:
        if not (isinstance(t, (list, tuple)) and len(t) == 3):
            if status == "UNKNOWN":
                ref_code = answer.get("refusal_code") or answer.get("refusal")
                if ref_code == "MALFORMED_CASE_STRUCTURE":
                    return True, "PASS (C2): valid UNKNOWN refusal for malformed triangle length"
                return (
                    False,
                    f"FAIL (C2): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
                )
            return (
                False,
                f"FAIL (C2): malformed triangle length must be refused with UNKNOWN, got {status}",
            )
        for v in t:
            if not _c2_is_int(v):
                if status == "UNKNOWN":
                    ref_code = answer.get("refusal_code") or answer.get("refusal")
                    if ref_code == "MALFORMED_CASE_STRUCTURE":
                        return True, "PASS (C2): valid UNKNOWN refusal for non-integer vertex"
                    return (
                        False,
                        f"FAIL (C2): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
                    )
                return (
                    False,
                    f"FAIL (C2): non-integer vertex must be refused with UNKNOWN, got {status}",
                )
        if t[0] == t[1] or t[1] == t[2] or t[2] == t[0]:
            if status == "UNKNOWN":
                ref_code = answer.get("refusal_code") or answer.get("refusal")
                if ref_code == "MALFORMED_CASE_STRUCTURE":
                    return True, "PASS (C2): valid UNKNOWN refusal for degenerate triangle"
                return (
                    False,
                    f"FAIL (C2): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
                )
            return (
                False,
                f"FAIL (C2): degenerate triangle must be refused with UNKNOWN, got {status}",
            )

    B0, B1, B2, is_orientable, chi_hom, witness = _c2_compute_simplicial_homology(triangles)

    if witness == "MALFORMED_CASE_STRUCTURE":
        if status != "UNKNOWN":
            return False, f"FAIL (C2): expected UNKNOWN for MALFORMED_CASE_STRUCTURE, got {status}"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if ref_code != "MALFORMED_CASE_STRUCTURE":
            return (
                False,
                f"FAIL (C2): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
            )
        return True, "PASS (C2): valid UNKNOWN refusal for MALFORMED_CASE_STRUCTURE"
    elif witness is not None:
        if status != "OUT_OF_SCOPE":
            return False, f"FAIL (C2): non-manifold surface must be OUT_OF_SCOPE, got {status}"
        act_wit = answer.get("witness")
        if not isinstance(act_wit, Mapping):
            return False, "FAIL (C2): witness must be a Mapping"
        if act_wit.get("kind") != witness.get("kind"):
            return (
                False,
                f"FAIL (C2): witness kind mismatch: expected {witness.get('kind')}, got {act_wit.get('kind')}",
            )
        return True, "PASS (C2): valid OUT_OF_SCOPE witness for non-manifold"

    if status != "SOLVED":
        return False, f"FAIL (C2): unwarranted refusal on valid surface: {status}"

    # Verify Strict Integer Types (Reject Booleans)
    for int_field in ["V", "E", "F", "euler"]:
        val = answer.get(int_field)
        if not _c2_is_int(val):
            return False, f"FAIL (C2): field '{int_field}' must be strict int, got {type(val)}"

    if type(answer.get("orientable")) is not bool:
        return False, "FAIL (C2): orientable must be a boolean"

    # Verify Euler characteristic from homology
    if answer.get("euler") != chi_hom:
        return (
            False,
            f"FAIL (C2): euler mismatch with homology chi: expected {chi_hom}, got {answer.get('euler')}",
        )

    # Verify Orientability from Top Homology B2
    if answer.get("orientable") is not is_orientable:
        return (
            False,
            f"FAIL (C2): orientability mismatch with B2={B2}: expected {is_orientable}, got {answer.get('orientable')}",
        )

    # Verify Classification
    classif = answer.get("classification")
    if not isinstance(classif, Mapping):
        return False, "FAIL (C2): classification must be a Mapping"
    if is_orientable:
        g = (2 - chi_hom) // 2
        g_val = classif.get("orientable_genus")
        if not _c2_is_int(g_val) or g_val != g or "non_orientable_genus" in classif or g < 0:
            return (
                False,
                f"FAIL (C2): classification mismatch: expected orientable_genus {g}, got {g_val}",
            )
    else:
        h = 2 - chi_hom
        h_val = classif.get("non_orientable_genus")
        if not _c2_is_int(h_val) or h_val != h or "orientable_genus" in classif or h < 1:
            return (
                False,
                f"FAIL (C2): classification mismatch: expected non_orientable_genus {h}, got {h_val}",
            )

    # Verify Discrete Angle Deficit Curvature
    act_curv = answer.get("vertex_curvature")
    if not isinstance(act_curv, Mapping):
        return False, "FAIL (C2): vertex_curvature must be a Mapping"

    deg_counts: dict[int, int] = {}
    for t in triangles:
        for v in t:
            deg_counts[v] = deg_counts.get(v, 0) + 1

    sum_curv = Fraction(0)
    for v, deg_v in deg_counts.items():
        v_str = str(v)
        if v_str not in act_curv:
            return False, f"FAIL (C2): missing curvature for vertex {v}"
        c_val = act_curv[v_str]
        if not _c2_is_reduced_rational_str(c_val):
            return False, f"FAIL (C2): vertex {v} curvature not reduced rational: {c_val}"
        # Discrete angle deficit normalized: (6 - deg_v) / 6
        exp_k = Fraction(6 - deg_v, 6)
        if Fraction(c_val) != exp_k:
            return (
                False,
                f"FAIL (C2): vertex {v} curvature mismatch: expected {_c2_to_reduced_str(exp_k)}, got {c_val}",
            )
        sum_curv += Fraction(c_val)

    if sum_curv != Fraction(chi_hom):
        return False, f"FAIL (C2): Gauss-Bonnet sum mismatch with homology: {sum_curv} != {chi_hom}"

    return True, "PASS (C2): valid homology surface certificate"


# -------------------------------------------------------------------------
# Checker 2 Graph Dual Potential & Min-Cost Flow Pipeline
# -------------------------------------------------------------------------


def _c2_solve_integer_min_cost_flow(
    sources: list[int],
    sinks: list[int],
    supply_int: dict[int, int],
    demand_int: dict[int, int],
    cost_matrix: dict[tuple[int, int], int],
) -> int:
    """Solves metric uncapacitated transportation problem in Z via Successive Shortest Path on residual graph."""
    nodes = list(set(sources) | set(sinks))
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    N = len(nodes)

    adj: list[list[list[int]]] = [[] for _ in range(N)]

    def add_edge(u: int, v: int, cap: int, cost_val: int) -> None:
        ui = node_to_idx[u]
        vi = node_to_idx[v]
        fwd = [vi, cap, 0, cost_val, len(adj[vi])]
        bwd = [ui, 0, 0, -cost_val, len(adj[ui])]
        adj[ui].append(fwd)
        adj[vi].append(bwd)

    for i in sources:
        for j in sinks:
            add_edge(i, j, supply_int[i], cost_matrix.get((i, j), cost_matrix.get((j, i), 0)))

    pi = [0] * N
    supply_left = {node_to_idx[i]: supply_int[i] for i in sources}
    demand_left = {node_to_idx[j]: demand_int[j] for j in sinks}

    while sum(supply_left.values()) > 0:
        dist = [999999999] * N
        prev_node = [-1] * N
        prev_edge = [-1] * N
        pq: list[tuple[int, int]] = []

        for ui, s_val in supply_left.items():
            if s_val > 0:
                dist[ui] = 0
                heapq.heappush(pq, (0, ui))

        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            for edge_idx, edge in enumerate(adj[u]):
                v, cap, flow, edge_cost, rev_idx = edge
                if cap - flow > 0:
                    reduced_cost = edge_cost + pi[u] - pi[v]
                    if dist[u] + reduced_cost < dist[v]:
                        dist[v] = dist[u] + reduced_cost
                        prev_node[v] = u
                        prev_edge[v] = edge_idx
                        heapq.heappush(pq, (dist[v], v))

        reached_sink = None
        min_d = 999999999
        for vi, d_val in demand_left.items():
            if d_val > 0 and dist[vi] < min_d:
                min_d = dist[vi]
                reached_sink = vi

        if reached_sink is None:
            raise RuntimeError("Cannot reach any unsatisfied sink")

        for u in range(N):
            if dist[u] < 999999999:
                pi[u] += dist[u]

        push = demand_left[reached_sink]
        curr = reached_sink
        while prev_node[curr] != -1:
            u = prev_node[curr]
            e_idx = prev_edge[curr]
            edge = adj[u][e_idx]
            rem_cap = edge[1] - edge[2]
            if rem_cap < push:
                push = rem_cap
            curr = u
        if supply_left[curr] < push:
            push = supply_left[curr]

        start_node = curr
        curr = reached_sink
        while prev_node[curr] != -1:
            u = prev_node[curr]
            e_idx = prev_edge[curr]
            edge = adj[u][e_idx]
            rev_idx = edge[4]
            edge[2] += push
            adj[curr][rev_idx][2] -= push
            curr = u

        supply_left[start_node] -= push
        demand_left[reached_sink] -= push

    total_int_cost = 0
    for u in range(N):
        for edge in adj[u]:
            if edge[2] > 0 and edge[3] > 0:
                total_int_cost += edge[2] * edge[3]

    return total_int_cost


def _c2_verify_transport_plan(
    plan: list[Any],
    m_u: Mapping[int, Fraction],
    m_v: Mapping[int, Fraction],
    d_mat: Mapping[tuple[int, int], int],
    vertices: set[int],
    exact_w1: Fraction,
) -> tuple[bool, str | None]:
    """Validates primal transport plan marginal conservation and cost verification against exact_w1."""
    row_sums: dict[int, Fraction] = {}
    col_sums: dict[int, Fraction] = {}
    plan_cost = Fraction(0)

    for idx, p_entry in enumerate(plan):
        if not isinstance(p_entry, Mapping):
            return False, f"plan entry at {idx} must be a Mapping"
        p_from = p_entry.get("from")
        if p_from is None:
            p_from = p_entry.get("source")
        p_to = p_entry.get("to")
        if p_to is None:
            p_to = p_entry.get("target")
        p_mass_s = p_entry.get("mass")

        if not (_c2_is_int(p_from) and _c2_is_int(p_to)):
            return False, "plan from/to must be ints"
        if p_from not in vertices or p_to not in vertices:
            return False, "plan contains vertex not in graph"
        if not _c2_is_reduced_rational_str(p_mass_s):
            return False, f"plan mass not reduced rational: {p_mass_s}"
        mass_f = Fraction(p_mass_s)
        if mass_f <= 0:
            return False, "plan mass must be positive"

        row_sums[p_from] = row_sums.get(p_from, Fraction(0)) + mass_f
        col_sums[p_to] = col_sums.get(p_to, Fraction(0)) + mass_f

        d_val = d_mat.get((p_from, p_to))
        if d_val is None or d_val >= 9999:
            return False, f"unreachable pair ({p_from}, {p_to})"
        plan_cost += mass_f * d_val

    # Marginal source conservation: sum_j pi(i, j) == m_u(i)
    all_sources = set(m_u.keys()) | set(row_sums.keys())
    for s_node in all_sources:
        if row_sums.get(s_node, Fraction(0)) != m_u.get(s_node, Fraction(0)):
            return (
                False,
                f"source marginal violation at {s_node}: plan={row_sums.get(s_node, 0)} != m_u={m_u.get(s_node, 0)}",
            )

    # Marginal target conservation: sum_i pi(i, j) == m_v(j)
    all_targets = set(m_v.keys()) | set(col_sums.keys())
    for t_node in all_targets:
        if col_sums.get(t_node, Fraction(0)) != m_v.get(t_node, Fraction(0)):
            return (
                False,
                f"target marginal violation at {t_node}: plan={col_sums.get(t_node, 0)} != m_v={m_v.get(t_node, 0)}",
            )

    # Primal cost verification: sum pi(i, j) * d_G(i, j) == exact_w1
    if plan_cost != exact_w1:
        return False, f"plan cost mismatch: plan_cost={plan_cost} != exact_w1={exact_w1}"

    return True, None


def _c2_verify_graph_answer(case: Mapping[str, Any], answer: Mapping[str, Any]) -> tuple[bool, str]:
    """Verifies graph query answer against Checker 2 dual potential & zero duality gap criteria."""
    status = answer.get("status")
    edges_raw = case.get("edges")
    alpha_raw = case.get("alpha")

    # Closed schema whitelist for graph answers
    if status == "SOLVED":
        allowed_keys = {"id", "case_id", "status", "edges"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C2): unexpected key '{k}' in SOLVED graph answer"
    elif status == "OUT_OF_SCOPE":
        allowed_keys = {"id", "case_id", "status", "witness"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C2): unexpected key '{k}' in OUT_OF_SCOPE graph answer"
    elif status == "UNKNOWN":
        allowed_keys = {"id", "case_id", "status", "refusal_code", "refusal"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C2): unexpected key '{k}' in UNKNOWN graph answer"

    if not isinstance(edges_raw, list):
        if status == "UNKNOWN":
            ref_code = answer.get("refusal_code") or answer.get("refusal")
            if ref_code == "MALFORMED_CASE_STRUCTURE":
                return True, "PASS (C2): valid UNKNOWN refusal for non-list edges"
            return (
                False,
                f"FAIL (C2): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
            )
        return False, "FAIL (C2): edges must be a list"

    # Validate alpha
    if "alpha" not in case:
        if status == "UNKNOWN":
            ref_code = answer.get("refusal_code") or answer.get("refusal")
            if ref_code == "MALFORMED_CASE_STRUCTURE":
                return True, "PASS (C2): valid UNKNOWN refusal for missing alpha"
            return (
                False,
                f"FAIL (C2): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
            )
        return False, "FAIL (C2): missing alpha must be refused with UNKNOWN"

    alpha_str = str(alpha_raw) if alpha_raw is not None else ""
    if not _c2_is_reduced_rational_str(alpha_str):
        if status != "UNKNOWN":
            return False, "FAIL (C2): invalid alpha must be refused with UNKNOWN"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if ref_code != "INVALID_ALPHA":
            return False, f"FAIL (C2): expected refusal_code 'INVALID_ALPHA', got '{ref_code}'"
        return True, "PASS (C2): invalid alpha refused"
    alpha = Fraction(alpha_str)
    if alpha < 0 or alpha >= 1:
        if status != "UNKNOWN":
            return False, "FAIL (C2): alpha out of bounds must be refused with UNKNOWN"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if ref_code != "INVALID_ALPHA":
            return False, f"FAIL (C2): expected refusal_code 'INVALID_ALPHA', got '{ref_code}'"
        return True, "PASS (C2): alpha out of bounds refused"

    if len(edges_raw) == 0:
        if status != "UNKNOWN":
            return False, "FAIL (C2): empty graph must be UNKNOWN"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if ref_code != "MALFORMED_CASE_STRUCTURE":
            return (
                False,
                f"FAIL (C2): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
            )
        return True, "PASS (C2): empty graph refused"

    vertices = set()
    adj: dict[int, set[int]] = {}
    edges_set = set()

    for e in edges_raw:
        if not (isinstance(e, (list, tuple)) and len(e) == 2):
            if status == "UNKNOWN":
                ref_code = answer.get("refusal_code") or answer.get("refusal")
                if ref_code == "MALFORMED_CASE_STRUCTURE":
                    return True, "PASS (C2): valid UNKNOWN refusal for malformed edge length"
                return (
                    False,
                    f"FAIL (C2): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
                )
            return (
                False,
                f"FAIL (C2): malformed edge list must be refused with UNKNOWN, got {status}",
            )
        u, v = e[0], e[1]
        if not (_c2_is_int(u) and _c2_is_int(v)):
            if status == "UNKNOWN":
                ref_code = answer.get("refusal_code") or answer.get("refusal")
                if ref_code == "MALFORMED_CASE_STRUCTURE":
                    return True, "PASS (C2): valid UNKNOWN refusal for non-integer edge vertices"
                return (
                    False,
                    f"FAIL (C2): expected refusal_code 'MALFORMED_CASE_STRUCTURE', got '{ref_code}'",
                )
            return False, "FAIL (C2): edge vertices must be ints"
        if u == v:
            if status != "OUT_OF_SCOPE":
                return False, "FAIL (C2): self loop must be OUT_OF_SCOPE"
            wit = answer.get("witness")
            if not isinstance(wit, Mapping) or wit.get("kind") != "self_loop":
                return False, f"FAIL (C2): invalid self_loop witness: {wit}"
            return True, "PASS (C2): self loop refused"
        e_norm = (min(u, v), max(u, v))
        if e_norm in edges_set:
            if status != "OUT_OF_SCOPE":
                return False, "FAIL (C2): duplicate edge must be OUT_OF_SCOPE"
            wit = answer.get("witness")
            if not isinstance(wit, Mapping) or wit.get("kind") != "multigraph":
                return False, f"FAIL (C2): invalid multigraph witness: {wit}"
            return True, "PASS (C2): duplicate edge refused"
        edges_set.add(e_norm)
        vertices.add(u)
        vertices.add(v)
        for a, b in [(u, v), (v, u)]:
            if a not in adj:
                adj[a] = set()
            adj[a].add(b)

    n = len(vertices)
    if n > 60 or len(edges_set) > 200:
        if status != "UNKNOWN":
            return False, "FAIL (C2): graph bounds exceeded must be UNKNOWN"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if ref_code != "GRAPH_TOO_LARGE":
            return False, f"FAIL (C2): expected refusal_code 'GRAPH_TOO_LARGE', got '{ref_code}'"
        return True, "PASS (C2): graph bounds exceeded refused"

    nodes = sorted(list(vertices))
    d_mat: dict[tuple[int, int], int] = {}
    for i in nodes:
        for j in nodes:
            d_mat[(i, j)] = 0 if i == j else (1 if j in adj.get(i, set()) else 9999)

    for k in nodes:
        for i in nodes:
            for j in nodes:
                if d_mat[(i, k)] + d_mat[(k, j)] < d_mat[(i, j)]:
                    d_mat[(i, j)] = d_mat[(i, k)] + d_mat[(k, j)]

    # Check connectedness
    for i in nodes:
        for j in nodes:
            if d_mat[(i, j)] >= 9999:
                if status != "OUT_OF_SCOPE":
                    return False, "FAIL (C2): disconnected graph must be OUT_OF_SCOPE"
                wit = answer.get("witness")
                if not isinstance(wit, Mapping) or wit.get("kind") != "graph_disconnected":
                    return False, f"FAIL (C2): invalid disconnected_graph witness: {wit}"
                return True, "PASS (C2): valid disconnected graph witness"

    if status != "SOLVED":
        return False, f"FAIL (C2): unwarranted refusal on valid connected graph: {status}"

    act_edges = answer.get("edges")
    if not isinstance(act_edges, list) or len(act_edges) != len(edges_set):
        return False, f"FAIL (C2): edges count mismatch: expected {len(edges_set)}"

    seen_edges = set()
    for idx, e_item in enumerate(act_edges):
        if not isinstance(e_item, Mapping):
            return False, f"FAIL (C2): edge item at {idx} must be a Mapping"
        e_pair = e_item.get("edge")
        if not (isinstance(e_pair, (list, tuple)) and len(e_pair) == 2):
            return False, f"FAIL (C2): malformed edge pair at {idx}"
        u, v = e_pair[0], e_pair[1]
        if not (_c2_is_int(u) and _c2_is_int(v)):
            return False, f"FAIL (C2): edge vertices at {idx} must be strict ints"
        e_norm = (min(u, v), max(u, v))
        seen_edges.add(e_norm)

        # Verify plan schema in Checker 2
        plan = e_item.get("plan")
        if not isinstance(plan, list):
            return False, f"FAIL (C2): edge {e_norm} plan must be a list"

        # Forman check
        exp_forman = 4 - len(adj[u]) - len(adj[v])
        act_forman = e_item.get("forman")
        if not _c2_is_int(act_forman):
            return (
                False,
                f"FAIL (C2): edge {e_norm} forman must be strict int, got {type(act_forman)}",
            )
        if act_forman != exp_forman:
            return (
                False,
                f"FAIL (C2): Forman mismatch for edge {e_norm}: expected {exp_forman}, got {act_forman}",
            )

        # Calculate exact marginals
        m_u: dict[int, Fraction] = {u: alpha}
        for z in adj[u]:
            m_u[z] = m_u.get(z, Fraction(0)) + Fraction(1 - alpha, len(adj[u]))

        m_v: dict[int, Fraction] = {v: alpha}
        for z in adj[v]:
            m_v[z] = m_v.get(z, Fraction(0)) + Fraction(1 - alpha, len(adj[v]))

        # 1. Audit Kantorovich Dual Potential 1-Lipschitz condition
        potential = e_item.get("potential")
        if not isinstance(potential, Mapping):
            return False, f"FAIL (C2): edge {e_norm} potential must be a Mapping"

        phi: dict[int, Fraction] = {}
        for node in nodes:
            node_s = str(node)
            if node_s not in potential:
                return False, f"FAIL (C2): edge {e_norm} missing potential for node {node}"
            val_s = potential[node_s]
            if not _c2_is_reduced_rational_str(val_s):
                return False, f"FAIL (C2): potential value not reduced rational: {val_s}"
            phi[node] = Fraction(val_s)

        # Check 1-Lipschitz on all graph edges: |phi(x) - phi(y)| <= 1
        for x, y in edges_set:
            slope = abs(phi[x] - phi[y])
            if slope > 1:
                return (
                    False,
                    f"FAIL (C2): edge {e_norm} potential violates 1-Lipschitz on edge ({x}, {y}): slope={slope} > 1",
                )

        # 2. Compute Dual Objective: D = sum_i phi(i) * (m_u(i) - m_v(i))
        dual_obj = Fraction(0)
        for node in nodes:
            net_mass = m_u.get(node, Fraction(0)) - m_v.get(node, Fraction(0))
            dual_obj += phi[node] * net_mass

        # 3. Independent Ground Truth W1 via Successive Shortest Path Min-Cost Flow
        all_dens = [m.denominator for m in list(m_u.values()) + list(m_v.values())]
        lcm_val = 1
        for d in all_dens:
            lcm_val = (lcm_val * d) // math.gcd(lcm_val, d)

        supp_int = {node: int(m_u.get(node, 0) * lcm_val) for node in nodes}
        dem_int = {node: int(m_v.get(node, 0) * lcm_val) for node in nodes}

        sources = [node for node in nodes if supp_int.get(node, 0) > 0]
        sinks = [node for node in nodes if dem_int.get(node, 0) > 0]
        int_flow_cost = _c2_solve_integer_min_cost_flow(sources, sinks, supp_int, dem_int, d_mat)
        exact_w1 = Fraction(int_flow_cost, lcm_val)
        exact_kappa = Fraction(1) - exact_w1

        # 4. Zero Duality Gap Check: dual_obj must equal exact_w1
        if dual_obj != exact_w1:
            return (
                False,
                f"FAIL (C2): edge {e_norm} duality gap non-zero: dual_obj={dual_obj} != exact_w1={exact_w1}",
            )

        # 4b. Primal Plan Marginal Conservation and Cost Verification in Checker 2
        is_plan_valid, plan_err = _c2_verify_transport_plan(
            plan, m_u, m_v, d_mat, vertices, exact_w1
        )
        if not is_plan_valid:
            return False, f"FAIL (C2): edge {e_norm} {plan_err}"

        # 5. Ollivier Curvature Check
        act_ollivier = e_item.get("ollivier")
        if not _c2_is_reduced_rational_str(act_ollivier):
            return False, f"FAIL (C2): edge {e_norm} ollivier not reduced rational: {act_ollivier}"
        if Fraction(act_ollivier) != exact_kappa:
            return (
                False,
                f"FAIL (C2): edge {e_norm} ollivier mismatch: expected {_c2_to_reduced_str(exact_kappa)}, got {act_ollivier}",
            )

    return True, "PASS (C2): valid dual potential & zero duality gap certificate"


# -------------------------------------------------------------------------
# Checker 2 Entry Point
# -------------------------------------------------------------------------


def verify_homology_dual_potential_certificate(
    case: Mapping[str, Any], answer: Mapping[str, Any]
) -> tuple[bool, str]:
    """Top-level verification entry point for Checker 2."""
    if not isinstance(case, Mapping) or not isinstance(answer, Mapping):
        return False, "FAIL (C2): case and answer must be Mappings"

    status = answer.get("status")
    if type(status) is not str or status not in {"SOLVED", "OUT_OF_SCOPE", "UNKNOWN"}:
        return False, f"FAIL (C2): invalid status '{status}'"

    c_id = case.get("case_id") or case.get("id")
    a_id = answer.get("id") or answer.get("case_id")
    if c_id != a_id:
        return False, f"FAIL (C2): case ID mismatch: case={c_id} vs answer={a_id}"

    if status == "UNKNOWN":
        allowed_keys = {"id", "case_id", "status", "refusal_code", "refusal"}
        for k in answer.keys():
            if k not in allowed_keys:
                return False, f"FAIL (C2): unexpected key '{k}' in UNKNOWN answer"
        ref_code = answer.get("refusal_code") or answer.get("refusal")
        if not isinstance(ref_code, str):
            return False, "FAIL (C2): UNKNOWN answer missing refusal_code"
        return _c2_verify_refusal_warranted(case, ref_code)

    query = case.get("query")
    if query == "surface":
        return _c2_verify_surface_answer(case, answer)
    elif query == "graph":
        return _c2_verify_graph_answer(case, answer)
    else:
        return False, f"FAIL (C2): unknown query '{query}'"
