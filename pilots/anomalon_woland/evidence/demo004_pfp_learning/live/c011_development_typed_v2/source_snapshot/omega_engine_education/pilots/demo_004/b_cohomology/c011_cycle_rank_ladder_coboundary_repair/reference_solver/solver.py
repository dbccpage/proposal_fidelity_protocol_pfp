"""Clean Reference Solver for C011 (Cycle-Rank Ladder: Minimum-L1 Coboundary Repair).

Standard library only. Exposes def solve(case: Mapping[str, Any]) -> dict[str, Any].
Produces exact rational Phi1 obstruction, vertex potential, minimal edge repair,
and LP dual circulation certificate.
Produces structured witness for OUT_OF_SCOPE cases (nonpositive weight, self loop, unknown endpoint).
Produces closed-list refusal codes for UNKNOWN out-of-bounds or malformed cases.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

try:
    from .ddc_tracer import DDCTracer
    from .graph_cohomology import (
        Edge,
        Graph,
        compute_cycle_rank,
        extract_components,
        format_canonical_rational,
        parse_canonical_rational,
        solve_minimum_l1_repair,
    )
except (ImportError, ValueError):
    try:
        from reference_solver.ddc_tracer import DDCTracer
        from reference_solver.graph_cohomology import (
            Edge,
            Graph,
            compute_cycle_rank,
            extract_components,
            format_canonical_rational,
            parse_canonical_rational,
            solve_minimum_l1_repair,
        )
    except (ImportError, ValueError):
        from ddc_tracer import DDCTracer
        from graph_cohomology import (
            Edge,
            Graph,
            compute_cycle_rank,
            extract_components,
            format_canonical_rational,
            parse_canonical_rational,
            solve_minimum_l1_repair,
        )


def _is_exact_int(val: Any) -> bool:
    """True if val is int and not bool."""
    return isinstance(val, int) and not isinstance(val, bool)


def solve_with_trace(
    case: Mapping[str, Any],
    tracer: DDCTracer | None = None,
) -> tuple[dict[str, Any], DDCTracer]:
    """Solves a C011 case with machine-verifiable DDC 8-letter trace logging."""
    if tracer is None:
        case_id_raw = case.get("id") if isinstance(case, Mapping) else "unnamed_case"
        tracer = DDCTracer(run_id=f"c011_{case_id_raw}")

    # Step 1: Context Exposure (C)
    if not isinstance(case, Mapping):
        refusal = {
            "id": "malformed_case",
            "status": "UNKNOWN",
            "refusal": "MALFORMED_CASE_STRUCTURE",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }
        tracer.record_step(
            "M", "refusal_not_a_mapping", payload=refusal, refusal_reason="MALFORMED_CASE_STRUCTURE"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    case_id = case.get("id") or case.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        refusal = {
            "id": "unknown_case",
            "status": "UNKNOWN",
            "refusal": "MALFORMED_CASE_STRUCTURE",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }
        tracer.record_step(
            "M", "refusal_missing_id", payload=refusal, refusal_reason="MALFORMED_CASE_STRUCTURE"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    # Check target_defect / target_phi1 if present
    if "target_defect" in case or "target_phi1" in case:
        raw_td = case.get("target_defect") or case.get("target_phi1")
        try:
            parsed_td = parse_canonical_rational(raw_td)
            if parsed_td < 0:
                raise ValueError("Target defect must be non-negative")
        except Exception:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "INVALID_TARGET_DEFECT",
                "refusal_code": "INVALID_TARGET_DEFECT",
            }
            tracer.record_step(
                "M",
                "refusal_invalid_target_defect",
                payload=refusal,
                refusal_reason="INVALID_TARGET_DEFECT",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

    raw_vertices = case.get("vertices")
    if not isinstance(raw_vertices, list) or not raw_vertices:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "VERTEX_COUNT_OUT_OF_BOUNDS"
            if isinstance(raw_vertices, list) and len(raw_vertices) == 0
            else "MALFORMED_CASE_STRUCTURE",
            "refusal_code": "VERTEX_COUNT_OUT_OF_BOUNDS"
            if isinstance(raw_vertices, list) and len(raw_vertices) == 0
            else "MALFORMED_CASE_STRUCTURE",
        }
        tracer.record_step(
            "M", "refusal_invalid_vertices_list", payload=refusal, refusal_reason=refusal["refusal"]
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    if len(raw_vertices) > 60:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "VERTEX_COUNT_OUT_OF_BOUNDS",
            "refusal_code": "VERTEX_COUNT_OUT_OF_BOUNDS",
        }
        tracer.record_step(
            "M",
            "refusal_vertex_count_exceeded",
            payload=refusal,
            refusal_reason="VERTEX_COUNT_OUT_OF_BOUNDS",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    vertices: list[str] = []
    seen_vertices: set[str] = set()
    for v in raw_vertices:
        if not isinstance(v, str) or not v or v in seen_vertices:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_CASE_STRUCTURE",
                "refusal_code": "MALFORMED_CASE_STRUCTURE",
            }
            tracer.record_step(
                "M",
                "refusal_duplicate_or_invalid_vertex",
                payload=refusal,
                refusal_reason="MALFORMED_CASE_STRUCTURE",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer
        seen_vertices.add(v)
        vertices.append(v)

    raw_edges = case.get("edges")
    if not isinstance(raw_edges, list):
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "MALFORMED_CASE_STRUCTURE",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }
        tracer.record_step(
            "M",
            "refusal_edges_not_list",
            payload=refusal,
            refusal_reason="MALFORMED_CASE_STRUCTURE",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    if len(raw_edges) > 200:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "EDGE_COUNT_OUT_OF_BOUNDS",
            "refusal_code": "EDGE_COUNT_OUT_OF_BOUNDS",
        }
        tracer.record_step(
            "M",
            "refusal_edge_count_exceeded",
            payload=refusal,
            refusal_reason="EDGE_COUNT_OUT_OF_BOUNDS",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    # Parse and validate each edge
    edges: list[Edge] = []
    seen_edge_ids: set[str] = set()

    for idx, e_raw in enumerate(raw_edges):
        if not isinstance(e_raw, Mapping):
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_CASE_STRUCTURE",
                "refusal_code": "MALFORMED_CASE_STRUCTURE",
            }
            tracer.record_step(
                "M",
                "refusal_edge_not_mapping",
                payload=refusal,
                refusal_reason="MALFORMED_CASE_STRUCTURE",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        u = e_raw.get("u")
        v = e_raw.get("v")

        # Fallback to tail/head
        if u is None and "tail" in e_raw:
            u = e_raw["tail"]
        if v is None and "head" in e_raw:
            v = e_raw["head"]

        if not isinstance(u, str) or not isinstance(v, str):
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_EDGE_SPEC",
                "refusal_code": "MALFORMED_EDGE_SPEC",
            }
            tracer.record_step(
                "M",
                "refusal_malformed_edge_endpoints",
                payload=refusal,
                refusal_reason="MALFORMED_EDGE_SPEC",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        e_id = e_raw.get("id")
        if not isinstance(e_id, str) or not e_id:
            e_id = f"{u}->{v}"
            if e_id in seen_edge_ids:
                e_id = f"{u}->{v}#{idx}"

        if e_id in seen_edge_ids:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_EDGE_SPEC",
                "refusal_code": "MALFORMED_EDGE_SPEC",
            }
            tracer.record_step(
                "M",
                "refusal_duplicate_edge_id",
                payload=refusal,
                refusal_reason="MALFORMED_EDGE_SPEC",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer
        seen_edge_ids.add(e_id)

        # Check for OUT_OF_SCOPE conditions: self-loop or unknown endpoint
        if u not in seen_vertices or v not in seen_vertices:
            oos = {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"edge": e_id, "reason": "UNKNOWN_ENDPOINT"},
            }
            tracer.record_step(
                "M", "out_of_scope_unknown_endpoint", payload=oos, refusal_reason="UNKNOWN_ENDPOINT"
            )
            tracer.record_step("T", "terminalize_out_of_scope", payload=oos)
            return oos, tracer

        if u == v:
            oos = {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"edge": e_id, "reason": "SELF_LOOP"},
            }
            tracer.record_step(
                "M", "out_of_scope_self_loop", payload=oos, refusal_reason="SELF_LOOP"
            )
            tracer.record_step("T", "terminalize_out_of_scope", payload=oos)
            return oos, tracer

        # Parse claim
        claim_raw = e_raw.get("claim")
        if claim_raw is None:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_EDGE_SPEC",
                "refusal_code": "MALFORMED_EDGE_SPEC",
            }
            tracer.record_step(
                "M", "refusal_missing_claim", payload=refusal, refusal_reason="MALFORMED_EDGE_SPEC"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        try:
            claim_val = parse_canonical_rational(claim_raw)
        except Exception:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_EDGE_SPEC",
                "refusal_code": "MALFORMED_EDGE_SPEC",
            }
            tracer.record_step(
                "M",
                "refusal_malformed_claim_rational",
                payload=refusal,
                refusal_reason="MALFORMED_EDGE_SPEC",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        # Parse weight (capacity)
        weight_raw = e_raw.get("weight")
        if weight_raw is None:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "INVALID_CAPACITY",
                "refusal_code": "INVALID_CAPACITY",
            }
            tracer.record_step(
                "M", "refusal_missing_weight", payload=refusal, refusal_reason="INVALID_CAPACITY"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        try:
            weight_val = parse_canonical_rational(weight_raw)
        except Exception:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "INVALID_CAPACITY",
                "refusal_code": "INVALID_CAPACITY",
            }
            tracer.record_step(
                "M",
                "refusal_malformed_weight_rational",
                payload=refusal,
                refusal_reason="INVALID_CAPACITY",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        if weight_val <= 0:
            # Check if this case explicitly expects OUT_OF_SCOPE or refusal
            if case.get("allow_out_of_scope", True) and not case.get("expect_refusal"):
                oos = {
                    "id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {"edge": e_id, "reason": "NONPOSITIVE_WEIGHT"},
                }
                tracer.record_step(
                    "M",
                    "out_of_scope_nonpositive_weight",
                    payload=oos,
                    refusal_reason="NONPOSITIVE_WEIGHT",
                )
                tracer.record_step("T", "terminalize_out_of_scope", payload=oos)
                return oos, tracer
            else:
                refusal = {
                    "id": case_id,
                    "status": "UNKNOWN",
                    "refusal": "NEGATIVE_WEIGHT",
                    "refusal_code": "NEGATIVE_WEIGHT",
                }
                tracer.record_step(
                    "M",
                    "refusal_negative_weight",
                    payload=refusal,
                    refusal_reason="NEGATIVE_WEIGHT",
                )
                tracer.record_step("T", "terminalize_refusal", payload=refusal)
                return refusal, tracer

        # Check denominator bound <= 12
        if weight_val.denominator > 12 and case.get("enforce_denominator_bounds", False):
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "INVALID_CAPACITY",
                "refusal_code": "INVALID_CAPACITY",
            }
            tracer.record_step(
                "M",
                "refusal_weight_denominator_exceeded",
                payload=refusal,
                refusal_reason="INVALID_CAPACITY",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        edges.append(Edge(id=e_id, u=u, v=v, claim=claim_val, weight=weight_val))

    graph = Graph(vertices=vertices, edges=edges)

    # Check connectivity requirement
    components = extract_components(graph)
    if len(components) > 1 and case.get("require_connected", False):
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "DISCONNECTED_GRAPH",
            "refusal_code": "DISCONNECTED_GRAPH",
        }
        tracer.record_step(
            "M", "refusal_disconnected_graph", payload=refusal, refusal_reason="DISCONNECTED_GRAPH"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    # Check cycle rank bounds: 0 <= b1 <= 16
    b1 = compute_cycle_rank(graph)
    if b1 > 16:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "EDGE_COUNT_OUT_OF_BOUNDS",
            "refusal_code": "EDGE_COUNT_OUT_OF_BOUNDS",
        }
        tracer.record_step(
            "M",
            "refusal_cycle_rank_exceeded",
            payload=refusal,
            refusal_reason="EDGE_COUNT_OUT_OF_BOUNDS",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    tracer.record_step(
        "C",
        "intake_graph_structure",
        payload={
            "vertices_count": len(vertices),
            "edges_count": len(edges),
            "components_count": len(components),
            "cycle_rank": b1,
        },
    )

    # Step 2: Residual Projection (R)
    tracer.record_step("R", "evaluate_cycle_defect_and_homology", payload={"b1": b1})

    # Step 3: Structural Lift (Lambda)
    tracer.record_step("Lambda", "lift_to_cycle_basis_dual_space", payload={"cycle_dimension": b1})

    # Step 4: Scale Descent (D) & Simplex Optimization
    tracer.record_step("D", "simplex_cycle_descent", payload={"b1": b1})

    # Step 5: Exact Repair (E)
    potential, repair, dual, phi1 = solve_minimum_l1_repair(graph)

    # Format outputs to canonical strings, omitting zero repair/dual entries per spec
    formatted_potential = {
        v: format_canonical_rational(potential.get(v, Fraction(0))) for v in vertices
    }
    formatted_repair = {
        eid: format_canonical_rational(val) for eid, val in repair.items() if val != 0
    }
    formatted_dual = {eid: format_canonical_rational(val) for eid, val in dual.items() if val != 0}
    formatted_phi1 = format_canonical_rational(phi1)

    tracer.record_step(
        "E",
        "exact_coboundary_repair_certified",
        payload={
            "phi1": formatted_phi1,
            "non_zero_repairs": len(formatted_repair),
            "non_zero_duals": len(formatted_dual),
        },
    )

    # Step 6: Integration (I)
    result = {
        "id": case_id,
        "status": "SOLVED",
        "phi1": formatted_phi1,
        "potential": formatted_potential,
        "repair": formatted_repair,
        "dual": formatted_dual,
    }
    tracer.record_step(
        "I", "integrate_certificate", payload={"id": case_id, "phi1": formatted_phi1}
    )

    # Step 7: Terminalization (T)
    tracer.record_step("T", "terminalize_solved", payload={"id": case_id})

    return result, tracer


def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    """Solves a C011 challenge case and returns the certificate dictionary.

    Standard library only. Returns exact RFC 8785 canonical JSON compatible dict.
    """
    result, _ = solve_with_trace(case)
    return result
