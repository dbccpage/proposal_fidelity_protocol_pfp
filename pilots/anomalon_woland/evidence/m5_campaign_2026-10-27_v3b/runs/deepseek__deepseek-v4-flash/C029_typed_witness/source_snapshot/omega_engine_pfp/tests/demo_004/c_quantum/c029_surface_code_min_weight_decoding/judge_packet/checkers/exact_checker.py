# AuthorityEffect: None.
"""
Exact Checker for C029: Minimum-Weight Surface-Code Decoding.

Verifies:
(a) H_Z * c == s mod 2 over F_2.
(b) The stated weight equals sum_{q in c} w_q.
(c) The dual variables (y_v and z_S) are feasible for the matching LP on the
    defect graph (defects plus boundary copies, with exact shortest-path edge weights
    recomputed independently by the checker) and their objective equals the stated weight.
Also validates OUT_OF_SCOPE and UNKNOWN refusal witnesses.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, List, Set, Tuple

from .schema_guard import validate_certificate

try:
    from reference_solver.exact_simplex import format_fraction, parse_fraction
    from reference_solver.graph import DecodingGraph
except (ImportError, ValueError):
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from reference_solver.exact_simplex import parse_fraction
    from reference_solver.graph import DecodingGraph


def verify_exact(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Executes exact verification of C029 answer.
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

    m = len(hz)
    n = len(hz[0]) if m > 0 else 0

    # Bounds check
    if code_type == "rotated":
        if distance not in {3, 5, 7}:
            if status != "UNKNOWN":
                return (
                    False,
                    f"Expected status UNKNOWN for rotated distance {distance}, got {status}",
                    {"status": status},
                )
            if result.get("refusal_code") != "DISTANCE_OUT_OF_BOUNDS":
                return (
                    False,
                    f"Expected refusal_code DISTANCE_OUT_OF_BOUNDS, got {result.get('refusal_code')}",
                    {"refusal_code": result.get("refusal_code")},
                )
            return True, "Valid UNKNOWN refusal for distance out of bounds", {"distance": distance}
    elif code_type == "toric":
        if distance not in {3, 4, 5}:
            if status != "UNKNOWN":
                return (
                    False,
                    f"Expected status UNKNOWN for toric distance {distance}, got {status}",
                    {"status": status},
                )
            if result.get("refusal_code") != "DISTANCE_OUT_OF_BOUNDS":
                return (
                    False,
                    f"Expected refusal_code DISTANCE_OUT_OF_BOUNDS, got {result.get('refusal_code')}",
                    {"refusal_code": result.get("refusal_code")},
                )
            return True, "Valid UNKNOWN refusal for distance out of bounds", {"distance": distance}

        # Toric odd parity check
        if sum(syndrome) % 2 != 0:
            if status != "OUT_OF_SCOPE":
                return (
                    False,
                    f"Expected status OUT_OF_SCOPE for odd parity syndrome on torus, got {status}",
                    {"status": status},
                )
            witness = result.get("witness", {})
            expected_witness = {"kind": "odd_parity_on_torus", "rows": "all"}
            if witness != expected_witness:
                return (
                    False,
                    f"Expected witness {expected_witness}, got {witness}",
                    {"witness": witness},
                )
            return True, "Valid OUT_OF_SCOPE witness for odd parity on torus", {"witness": witness}

    else:
        expected_witness = {"kind": "unknown_code_type", "code": code_type}
        if status != "OUT_OF_SCOPE" or result.get("witness") != expected_witness:
            return (
                False,
                f"Unknown code type requires witness {expected_witness}",
                {"status": status},
            )
        return True, "Unknown code type witness verified", {"witness": expected_witness}

    if status != "SOLVED":
        return False, f"Expected status SOLVED, got {status}", {"status": status}

    correction = result.get("correction", [])
    stated_weight = result.get("weight")
    cert = result.get("certificate", {})

    # (a) Verify H_Z * c == s mod 2
    # Check correction qubit indices
    for q in correction:
        if not isinstance(q, int) or q < 0 or q >= n:
            return False, f"Correction qubit index out of bounds: {q}", {"q": q}

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
            f"Correction syndrome mismatch: computed {computed_s} != expected {syndrome}",
            {"computed_s": computed_s, "syndrome": syndrome},
        )

    # (b) Verify stated weight equals sum w_q c_q
    actual_weight = sum(weights[q] for q in correction)
    if stated_weight != actual_weight:
        return (
            False,
            f"Stated weight {stated_weight} != actual correction weight {actual_weight}",
            {"stated_weight": stated_weight, "actual_weight": actual_weight},
        )

    # If syndrome is all zero, correction must be weight 0
    defects = [r for r in range(m) if syndrome[r] == 1]
    if not defects:
        if actual_weight != 0 or len(correction) != 0:
            return (
                False,
                f"Expected empty correction for zero syndrome, got weight {actual_weight}",
                {"weight": actual_weight},
            )
        return True, "Zero syndrome exact check passed", {"weight": 0}

    # (c) Recompute defect graph independently and verify matching dual feasibility & objective
    graph = DecodingGraph(hz, weights)
    k = len(defects)

    # Shortest paths between defects
    dist_defects: Dict[Tuple[int, int], int] = {}
    for i in range(k):
        for j in range(i + 1, k):
            d_val, _ = graph.shortest_path(defects[i], defects[j])
            dist_defects[(i, j)] = d_val

    # Shortest paths to boundary if rotated
    dist_boundary: Dict[int, int] = {}
    if code_type == "rotated":
        for i in range(k):
            d_val, _ = graph.shortest_path(defects[i], graph.boundary_node)
            dist_boundary[i] = d_val

    # Reconstruct defect graph edges
    edges_mwpm: Dict[Tuple[int, int], int] = {}
    if code_type == "rotated":
        num_nodes = 2 * k
        for i in range(k):
            for j in range(i + 1, k):
                edges_mwpm[(i, j)] = dist_defects[(i, j)]
        for i in range(k):
            edges_mwpm[(i, k + i)] = dist_boundary[i]
        for i in range(k):
            for j in range(i + 1, k):
                edges_mwpm[(k + i, k + j)] = 0
    else:
        num_nodes = k
        for i in range(k):
            for j in range(i + 1, k):
                edges_mwpm[(i, j)] = dist_defects[(i, j)]

    # Parse dual variables
    vertex_duals_raw = cert.get("vertex_duals", [])
    if len(vertex_duals_raw) != num_nodes:
        return (
            False,
            f"Expected {num_nodes} vertex duals, got {len(vertex_duals_raw)}",
            {"num_nodes": num_nodes, "got": len(vertex_duals_raw)},
        )

    try:
        y = [parse_fraction(v) for v in vertex_duals_raw]
    except Exception as e:
        return False, f"Invalid vertex dual rational string: {e}", {"error": str(e)}

    odd_set_duals_raw = cert.get("odd_set_duals", [])
    z_blossoms: List[Tuple[Set[int], Fraction]] = []
    for item in odd_set_duals_raw:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            return False, f"Malformed odd_set_dual entry: {item}", {"item": item}
        s_nodes, z_val_str = item
        if len(s_nodes) < 3 or len(s_nodes) % 2 == 0:
            return (
                False,
                f"Odd set blossom must have odd size >= 3: {s_nodes}",
                {"s_nodes": s_nodes},
            )
        try:
            z_val = parse_fraction(z_val_str)
        except Exception as e:
            return False, f"Invalid blossom dual rational string: {z_val_str}", {"error": str(e)}
        if z_val < 0:
            return False, f"Blossom dual must be non-negative: {z_val}", {"z_val": str(z_val)}
        z_blossoms.append((set(s_nodes), z_val))

    # Check dual feasibility on all edges in defect graph
    for (u, v), w in edges_mwpm.items():
        w_frac = Fraction(w)
        blossom_sum = sum(z_val for s_set, z_val in z_blossoms if u in s_set and v in s_set)
        edge_slack = w_frac - (y[u] + y[v] + blossom_sum)
        if edge_slack < 0:
            return (
                False,
                f"Dual feasibility violated on edge ({u}, {v}): y[{u}]={y[u]} + y[{v}]={y[v]} + z_sum={blossom_sum} > {w}",
                {
                    "u": u,
                    "v": v,
                    "y_u": str(y[u]),
                    "y_v": str(y[v]),
                    "blossom_sum": str(blossom_sum),
                    "w": w,
                },
            )

    # Check dual objective equality: sum y_v + sum z_S (|S|-1)/2 == actual_weight
    dual_obj = sum(y)
    for s_set, z_val in z_blossoms:
        dual_obj += z_val * Fraction(len(s_set) - 1, 2)

    if dual_obj != Fraction(actual_weight):
        return (
            False,
            f"Duality gap non-zero: dual objective {dual_obj} != primal weight {actual_weight}",
            {"dual_obj": str(dual_obj), "actual_weight": actual_weight},
        )

    return (
        True,
        "Exact syndrome, weight, and matching LP dual certificate verified",
        {
            "actual_weight": actual_weight,
            "dual_objective": str(dual_obj),
            "defects_count": k,
            "correction_size": len(correction),
        },
    )
