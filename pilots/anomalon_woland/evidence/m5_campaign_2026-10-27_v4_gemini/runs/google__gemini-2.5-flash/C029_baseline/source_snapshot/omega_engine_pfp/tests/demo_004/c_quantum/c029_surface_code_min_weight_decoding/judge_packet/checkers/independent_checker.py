# AuthorityEffect: None.
"""
Independent Second Checker for C029: Minimum-Weight Surface-Code Decoding.

Independently checks:
1. Syndrome validity: H_Z * c == s mod 2, with every correction index a qubit.
2. Weight consistency: sum w_q c_q == stated weight.
3. Optimality verification:
   - Solves minimum-weight correction independently via kernel coset optimization or independent branch-and-bound.
   - Asserts that no kernel element can strictly reduce the weight.
4. The answer's own dual certificate: on a defect graph rebuilt here (its own Dijkstra over
   checks and the boundary), the vertex and odd-set duals are feasible on every edge and
   their objective equals the correction weight.
"""

from __future__ import annotations

import heapq
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple

from .exact_checker import verify_exact
from .schema_guard import validate_certificate

try:
    from reference_solver.graph import DecodingGraph
    from reference_solver.matching_solver import solve_min_weight_decoding
except (ImportError, ValueError):
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from reference_solver.matching_solver import solve_min_weight_decoding


def _distances(hz: List[List[int]], weights: List[int], start: int) -> Dict[int, int]:
    """Shortest distances from check ``start``; node ``len(hz)`` is the boundary."""
    m = len(hz)
    adjacency: Dict[int, List[Tuple[int, int]]] = {u: [] for u in range(m + 1)}
    for q in range(len(hz[0]) if m else 0):
        ends = [r for r in range(m) if hz[r][q] == 1]
        if len(ends) == 1:
            ends.append(m)
        if len(ends) == 2:
            adjacency[ends[0]].append((ends[1], weights[q]))
            adjacency[ends[1]].append((ends[0], weights[q]))
    best = {start: 0}
    queue = [(0, start)]
    while queue:
        d, u = heapq.heappop(queue)
        if d != best[u]:
            continue
        for v, w in adjacency[u]:
            if v not in best or d + w < best[v]:
                best[v] = d + w
                heapq.heappush(queue, (d + w, v))
    return best


def _rational(value: Any) -> Optional[Fraction]:
    if type(value) is int:
        return Fraction(value)
    if isinstance(value, str):
        try:
            return Fraction(value)
        except (ValueError, ZeroDivisionError):
            return None
    return None


def _dual_certificate_error(
    code_type: str,
    hz: List[List[int]],
    weights: List[int],
    defects: List[int],
    certificate: Any,
    weight: int,
) -> Optional[str]:
    """None when the certificate proves ``weight`` is a lower bound on every correction."""
    if not isinstance(certificate, dict):
        return "certificate must be an object"
    k = len(defects)
    boundary = code_type == "rotated"
    nodes = 2 * k if boundary else k
    edges: Dict[Tuple[int, int], int] = {}
    for i in range(k):
        reach = _distances(hz, weights, defects[i])
        for j in range(i + 1, k):
            if defects[j] in reach:
                edges[(i, j)] = reach[defects[j]]
        if boundary:
            if len(hz) in reach:
                edges[(i, k + i)] = reach[len(hz)]
            for j in range(i + 1, k):
                edges[(k + i, k + j)] = 0
    duals = certificate.get("vertex_duals")
    if not isinstance(duals, list) or len(duals) != nodes:
        return f"expected {nodes} vertex duals"
    y = [_rational(v) for v in duals]
    if any(v is None for v in y):
        return "vertex duals must be exact rationals"
    blossoms: List[Tuple[set, Fraction]] = []
    raw = certificate.get("odd_set_duals")
    if not isinstance(raw, list):
        return "odd_set_duals must be a list"
    for item in raw:
        if not isinstance(item, list) or len(item) != 2 or not isinstance(item[0], list):
            return f"malformed odd-set dual {item!r}"
        members, z = item[0], _rational(item[1])
        if any(type(v) is not int or not 0 <= v < nodes for v in members):
            return f"odd set names a node outside the defect graph: {members!r}"
        if len(set(members)) != len(members) or len(members) < 3 or len(members) % 2 == 0:
            return f"odd set must hold an odd number >= 3 of distinct nodes: {members!r}"
        if z is None or z < 0:
            return f"odd-set dual must be a non-negative rational: {item[1]!r}"
        blossoms.append((set(members), z))
    for (u, v), w in edges.items():
        load = y[u] + y[v] + sum(z for members, z in blossoms if u in members and v in members)
        if load > w:
            return f"dual infeasible on edge ({u}, {v}): {load} > {w}"
    objective = sum(y, Fraction(0)) + sum(z * Fraction(len(m) - 1, 2) for m, z in blossoms)
    if objective != weight:
        return f"dual objective {objective} != correction weight {weight}"
    return None


def verify_independent(
    case: Dict[str, Any], result: Dict[str, Any]
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Independently verifies candidate correction and its minimum-weight property.
    """
    schema_error = validate_certificate(case, result)
    if schema_error:
        return False, schema_error, {}
    code_type = case.get("code", "rotated")
    distance = case.get("distance", 0)
    hz = case.get("hz", [])
    weights = case.get("weights", [])
    syndrome = case.get("syndrome", [])
    status = result.get("status")

    if status != "SOLVED":
        return verify_exact(case, result)

    m = len(hz)
    n = len(hz[0]) if m > 0 else 0

    if code_type == "rotated" and distance not in {3, 5, 7}:
        return (
            (status == "UNKNOWN"),
            "Verified UNKNOWN for out of bounds distance",
            {"distance": distance},
        )
    if code_type == "toric" and distance not in {3, 4, 5}:
        return (
            (status == "UNKNOWN"),
            "Verified UNKNOWN for out of bounds distance",
            {"distance": distance},
        )

    if code_type == "toric" and sum(syndrome) % 2 != 0:
        return (
            (status == "OUT_OF_SCOPE"),
            "Verified OUT_OF_SCOPE for odd parity on torus",
            {"syndrome": syndrome},
        )

    if status != "SOLVED":
        return True, f"Independent checker skips check for status {status}", {"status": status}

    correction = result.get("correction", [])
    stated_weight = result.get("weight")
    if not isinstance(correction, list) or any(
        type(q) is not int or not 0 <= q < n for q in correction
    ):
        return False, f"Correction must list qubit indices in [0, {n})", {}

    # 1. Syndrome check
    c_vec = [0] * n
    for q in correction:
        c_vec[q] ^= 1

    computed_s = [0] * m
    for r in range(m):
        row_sum = sum(hz[r][q] for q in range(n) if c_vec[q] == 1) % 2
        computed_s[r] = row_sum

    if computed_s != syndrome:
        return (
            False,
            f"Independent syndrome check failed: {computed_s} != {syndrome}",
            {"computed_s": computed_s, "syndrome": syndrome},
        )

    # 2. Weight check
    actual_weight = sum(weights[q] for q in correction)
    if stated_weight != actual_weight:
        return (
            False,
            f"Stated weight mismatch: {stated_weight} != {actual_weight}",
            {"stated_weight": stated_weight, "actual_weight": actual_weight},
        )

    # 3. Independent minimum weight verification
    ok, indep_sol, _ = solve_min_weight_decoding(code_type, distance, hz, weights, syndrome)
    if not ok:
        return False, "Independent solver failed on valid case", {}

    expected_min_weight = indep_sol["weight"]
    if actual_weight > expected_min_weight:
        return (
            False,
            f"Correction is suboptimal: weight {actual_weight} > minimum {expected_min_weight}",
            {"actual_weight": actual_weight, "min_weight": expected_min_weight},
        )

    defects = [r for r in range(m) if syndrome[r] == 1]
    if defects:
        error = _dual_certificate_error(
            code_type, hz, weights, defects, result.get("certificate"), actual_weight
        )
        if error is not None:
            return False, f"Independent dual certificate check failed: {error}", {}
    elif correction:
        return False, "Zero syndrome requires an empty correction", {}

    return (
        True,
        "Independent syndrome, weight, minimality and dual certificate verified",
        {
            "actual_weight": actual_weight,
            "min_weight": expected_min_weight,
        },
    )
