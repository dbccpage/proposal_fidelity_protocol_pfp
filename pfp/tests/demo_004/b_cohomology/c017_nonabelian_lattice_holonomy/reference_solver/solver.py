"""Reference Solver for C017: Nonabelian Lattice Holonomy and Flatness.

Outputs:
- NOT_FLAT with plaquette and nontrivial holonomy
- PURE_GAUGE with gauge g: V -> G
- FLAT_NONTRIVIAL with base, loop_a, hol_a, loop_b, hol_b
- OUT_OF_SCOPE with witness for invalid input or inverse mismatch
- UNKNOWN refusal
"""

from __future__ import annotations

from typing import Any

from .ddc_tracer import DDCTracer
from .lattice_holonomy import (
    check_is_pure_gauge,
    compute_all_plaquettes,
    compute_torus_global_loops,
    fix_spanning_tree_gauge,
    multiply_path,
)


def solve(case: dict[str, Any]) -> tuple[dict[str, Any], DDCTracer]:
    tracer = DDCTracer()
    case_id = str(case.get("id", "c017_unknown"))
    tracer.record_step("E", "init_solver", payload={"case_id": case_id})

    # Validate lattice size
    L = case.get("L")
    M = case.get("M")
    boundary = case.get("boundary", "open")
    if not isinstance(L, int) or not isinstance(M, int) or L < 2 or L > 12 or M < 2 or M > 12:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "LATTICE_SIZE_OUT_OF_BOUNDS",
            "refusal_code": "LATTICE_SIZE_OUT_OF_BOUNDS",
            "details": f"L={L}, M={M} must satisfy 2 <= L, M <= 12",
        }
        tracer.record_step(
            "M",
            "refusal_lattice_size",
            payload=refusal,
            refusal_reason="LATTICE_SIZE_OUT_OF_BOUNDS",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    if boundary not in ("open", "periodic"):
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "MALFORMED_INPUT",
            "refusal_code": "MALFORMED_INPUT",
            "details": "boundary must be 'open' or 'periodic'",
        }
        tracer.record_step(
            "M", "refusal_boundary", payload=refusal, refusal_reason="MALFORMED_INPUT"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    # Validate group
    group = case.get("group", {})
    elements = group.get("elements", [])
    identity = group.get("identity", "e")
    table = group.get("table", {})
    inverses = group.get("inverses", {})

    if (
        not isinstance(elements, list)
        or not isinstance(table, dict)
        or not isinstance(inverses, dict)
    ):
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "MALFORMED_INPUT",
            "refusal_code": "MALFORMED_INPUT",
            "details": "group must specify elements, table, and inverses",
        }
        tracer.record_step(
            "M", "refusal_group_format", payload=refusal, refusal_reason="MALFORMED_INPUT"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    # Check table consistency: identity and inverse checks
    if identity not in table:
        out_of_scope = {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "INVALID_GROUP", "details": "identity missing from table"},
        }
        tracer.record_step("I", "invalid_group", payload=out_of_scope)
        tracer.record_step("T", "terminalize_out_of_scope", payload=out_of_scope)
        return out_of_scope, tracer

    # Validate edge connections
    edges = case.get("edges", {})
    if not isinstance(edges, dict):
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "MALFORMED_INPUT",
            "refusal_code": "MALFORMED_INPUT",
            "details": "edges must be a dict",
        }
        tracer.record_step(
            "M", "refusal_edges_type", payload=refusal, refusal_reason="MALFORMED_INPUT"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    # Check inverse symmetry on all edges: U_{vu} == U_{uv}^{-1}
    for e_key, u_elem in edges.items():
        if "->" not in e_key:
            continue
        u, v = e_key.split("->")
        rev_key = f"{v}->{u}"
        if rev_key not in edges:
            out_of_scope = {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"edge": e_key, "reason": "MISSING_REVERSE_EDGE"},
            }
            tracer.record_step("I", "missing_rev_edge", payload=out_of_scope)
            tracer.record_step("T", "terminalize_out_of_scope", payload=out_of_scope)
            return out_of_scope, tracer

        rev_elem = edges[rev_key]
        expected_rev = inverses.get(u_elem)
        if rev_elem != expected_rev:
            out_of_scope = {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {
                    "edge": e_key,
                    "reason": "INVERSE_MISMATCH",
                    "u_elem": u_elem,
                    "rev_elem": rev_elem,
                },
            }
            tracer.record_step("I", "inverse_mismatch", payload=out_of_scope)
            tracer.record_step("T", "terminalize_out_of_scope", payload=out_of_scope)
            return out_of_scope, tracer

    tracer.record_step("C", "connection_validated", payload={"edge_count": len(edges)})

    # 1. Compute plaquette holonomies
    all_plaquettes = compute_all_plaquettes(L, M, boundary)
    for p in all_plaquettes:
        loop = p + [p[0]]
        hol = multiply_path(loop, edges, table, identity)
        if hol != identity:
            # Found non-flat plaquette!
            result = {
                "id": case_id,
                "status": "SOLVED",
                "verdict": "NOT_FLAT",
                "plaquette": p,
                "holonomy": hol,
            }
            tracer.record_step("D", "non_flat_plaquette_found", payload=result, defect_count=1)
            tracer.record_step("T", "terminal_pass", payload=result)
            return result, tracer

    tracer.record_step(
        "I", "all_plaquettes_flat", payload={"plaquettes_checked": len(all_plaquettes)}
    )

    # 2. Connection is flat: check pure gauge via spanning tree gauge fixing
    gauge = fix_spanning_tree_gauge(L, M, edges, table, inverses, identity)
    is_pure = check_is_pure_gauge(gauge, edges, table, inverses, identity)

    if is_pure or boundary == "open":
        result = {
            "id": case_id,
            "status": "SOLVED",
            "verdict": "PURE_GAUGE",
            "gauge": gauge,
        }
        tracer.record_step("R", "pure_gauge_certified", payload={"gauge_size": len(gauge)})
        tracer.record_step("T", "terminal_pass", payload=result)
        return result, tracer

    # 3. Periodic boundary and not pure gauge: FLAT_NONTRIVIAL
    loop_a, hol_a, loop_b, hol_b = compute_torus_global_loops(L, M, edges, table, identity)
    result = {
        "id": case_id,
        "status": "SOLVED",
        "verdict": "FLAT_NONTRIVIAL",
        "base": "0,0",
        "loop_a": loop_a,
        "hol_a": hol_a,
        "loop_b": loop_b,
        "hol_b": hol_b,
    }
    tracer.record_step("Lambda", "flat_nontrivial_holonomy_found", payload=result)
    tracer.record_step("T", "terminal_pass", payload=result)
    return result, tracer
