"""Reference Solver for C014: Exact Discrete Hodge Decomposition.

Decomposes edge flows f ∈ Q^E into gradient, curl, and harmonic parts:
    f = δ₀ φ + W₁⁻¹ δ₁ᵀ ψ + h
with exact rational orthogonality certificates under weighted inner product.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from typing import Any

try:
    from .ddc_tracer import DDCTracer
    from .discrete_hodge import compute_discrete_hodge_decomposition
    from .rational_linear_algebra import parse_fraction
except ImportError:
    from ddc_tracer import DDCTracer  # type: ignore
    from discrete_hodge import compute_discrete_hodge_decomposition  # type: ignore
    from rational_linear_algebra import parse_fraction  # type: ignore


CLOSED_REFUSAL_ENUM = frozenset(
    {
        "VERTEX_COUNT_OUT_OF_BOUNDS",
        "EDGE_COUNT_OUT_OF_BOUNDS",
        "FACE_COUNT_OUT_OF_BOUNDS",
        "COEFFICIENT_BOUND_EXCEEDED",
        "WEIGHT_DENOMINATOR_EXCEEDED",
        "WEIGHT_NON_POSITIVE",
        "MALFORMED_INPUT",
        "MALFORMED_CASE_STRUCTURE",
        "BUDGET_EXHAUSTED",
    }
)


def solve_with_trace(case: Any) -> tuple[dict[str, Any], DDCTracer]:
    """Evaluates case and records machine-verifiable DDC operational trace.

    Returns:
        (result_dict, ddc_tracer)
    """
    case_id = (
        str(case.get("id") or case.get("case_id") or "unnamed_case")
        if isinstance(case, Mapping)
        else "unnamed_case"
    )
    tracer = DDCTracer(run_id=f"c014_{case_id}")

    # Stage C: Context Exposure & Schema Validation
    if not isinstance(case, Mapping):
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "MALFORMED_CASE_STRUCTURE",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }
        tracer.record_step(
            "M",
            "refusal_case_not_mapping",
            payload=refusal,
            refusal_reason="MALFORMED_CASE_STRUCTURE",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    # Parse vertices
    raw_verts = case.get("vertices")
    if not isinstance(raw_verts, list):
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "MALFORMED_INPUT",
            "refusal_code": "MALFORMED_INPUT",
            "details": "vertices must be a list",
        }
        tracer.record_step(
            "M", "refusal_missing_vertices", payload=refusal, refusal_reason="MALFORMED_INPUT"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    vertices = [str(v) for v in raw_verts]
    if len(vertices) > 80:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "VERTEX_COUNT_OUT_OF_BOUNDS",
            "refusal_code": "VERTEX_COUNT_OUT_OF_BOUNDS",
            "count": len(vertices),
        }
        tracer.record_step(
            "M",
            "refusal_vertex_bound",
            payload=refusal,
            refusal_reason="VERTEX_COUNT_OUT_OF_BOUNDS",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    # Parse edges
    raw_edges = case.get("edges")
    if not isinstance(raw_edges, list):
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "MALFORMED_INPUT",
            "refusal_code": "MALFORMED_INPUT",
            "details": "edges must be a list",
        }
        tracer.record_step(
            "M", "refusal_missing_edges", payload=refusal, refusal_reason="MALFORMED_INPUT"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    if len(raw_edges) > 200:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "EDGE_COUNT_OUT_OF_BOUNDS",
            "refusal_code": "EDGE_COUNT_OUT_OF_BOUNDS",
            "count": len(raw_edges),
        }
        tracer.record_step(
            "M", "refusal_edge_bound", payload=refusal, refusal_reason="EDGE_COUNT_OUT_OF_BOUNDS"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    # Parse faces
    raw_faces = case.get("faces", [])
    if not isinstance(raw_faces, list):
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "MALFORMED_INPUT",
            "refusal_code": "MALFORMED_INPUT",
            "details": "faces must be a list",
        }
        tracer.record_step(
            "M", "refusal_invalid_faces", payload=refusal, refusal_reason="MALFORMED_INPUT"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    faces = [str(f) for f in raw_faces]
    if len(faces) > 150:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "FACE_COUNT_OUT_OF_BOUNDS",
            "refusal_code": "FACE_COUNT_OUT_OF_BOUNDS",
            "count": len(faces),
        }
        tracer.record_step(
            "M", "refusal_face_bound", payload=refusal, refusal_reason="FACE_COUNT_OUT_OF_BOUNDS"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    # Parse edge names and construct delta0
    edges: list[str] = []
    vert_idx_map = {v: i for i, v in enumerate(vertices)}
    n_V = len(vertices)

    # Determine if delta0 is provided explicitly as a matrix or dictionary
    delta0_explicit = case.get("d0") or case.get("delta0")
    if delta0_explicit is not None:
        if isinstance(delta0_explicit, list):
            # Matrix format: |E| x |V|
            delta0_mat: list[list[Fraction]] = []
            for row in delta0_explicit:
                if not isinstance(row, list) or len(row) != n_V:
                    refusal = {
                        "id": case_id,
                        "status": "UNKNOWN",
                        "refusal": "MALFORMED_INPUT",
                        "refusal_code": "MALFORMED_INPUT",
                        "details": "delta0 row length mismatch",
                    }
                    tracer.record_step(
                        "M", "refusal_delta0_dim", payload=refusal, refusal_reason="MALFORMED_INPUT"
                    )
                    tracer.record_step("T", "terminalize_refusal", payload=refusal)
                    return refusal, tracer
                delta0_mat.append([parse_fraction(x) for x in row])
            edges = [str(e) if isinstance(e, str) else f"e{i}" for i, e in enumerate(raw_edges)]
        elif isinstance(delta0_explicit, dict):
            # Dict format: edge_id -> {vertex_id: coeff}
            edges = [str(e) for e in raw_edges]
            delta0_mat = [[Fraction(0, 1) for _ in range(n_V)] for _ in range(len(edges))]
            for e_idx, e_id in enumerate(edges):
                e_row = delta0_explicit.get(e_id, {})
                for v_id, val in e_row.items():
                    if v_id in vert_idx_map:
                        delta0_mat[e_idx][vert_idx_map[v_id]] = parse_fraction(val)
        else:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_INPUT",
                "refusal_code": "MALFORMED_INPUT",
            }
            tracer.record_step(
                "M", "refusal_delta0_format", payload=refusal, refusal_reason="MALFORMED_INPUT"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer
    else:
        # Construct delta0 from structured edge definitions:
        # e.g. ["v0", "v1"] or {"id": "e0", "u": "v0", "v": "v1"} or "e01"
        edges = []
        delta0_mat = []
        for idx, e in enumerate(raw_edges):
            if isinstance(e, dict):
                e_id = str(e.get("id", f"e{idx}"))
                u = str(e.get("u") or e.get("tail"))
                v = str(e.get("v") or e.get("head"))
            elif isinstance(e, (list, tuple)) and len(e) >= 2:
                if len(e) == 2:
                    u, v = str(e[0]), str(e[1])
                    e_id = f"e_{u}_{v}"
                else:
                    e_id = str(e[0])
                    u, v = str(e[1]), str(e[2])
            elif isinstance(e, str):
                e_id = e
                # Attempt to extract endpoints from name like e01 -> v0, v1
                # Or check if case["edge_endpoints"] exists
                endpoints = case.get("edge_endpoints", {}).get(e)
                if endpoints:
                    u, v = str(endpoints[0]), str(endpoints[1])
                else:
                    refusal = {
                        "id": case_id,
                        "status": "UNKNOWN",
                        "refusal": "MALFORMED_INPUT",
                        "refusal_code": "MALFORMED_INPUT",
                        "details": f"Cannot infer endpoints for edge {e!r}",
                    }
                    tracer.record_step(
                        "M",
                        "refusal_edge_endpoints",
                        payload=refusal,
                        refusal_reason="MALFORMED_INPUT",
                    )
                    tracer.record_step("T", "terminalize_refusal", payload=refusal)
                    return refusal, tracer
            else:
                refusal = {
                    "id": case_id,
                    "status": "UNKNOWN",
                    "refusal": "MALFORMED_INPUT",
                    "refusal_code": "MALFORMED_INPUT",
                }
                tracer.record_step(
                    "M", "refusal_edge_type", payload=refusal, refusal_reason="MALFORMED_INPUT"
                )
                tracer.record_step("T", "terminalize_refusal", payload=refusal)
                return refusal, tracer

            if u not in vert_idx_map or v not in vert_idx_map:
                refusal = {
                    "id": case_id,
                    "status": "UNKNOWN",
                    "refusal": "MALFORMED_INPUT",
                    "refusal_code": "MALFORMED_INPUT",
                    "details": f"Edge endpoint unknown: {u} or {v}",
                }
                tracer.record_step(
                    "M", "refusal_unknown_vert", payload=refusal, refusal_reason="MALFORMED_INPUT"
                )
                tracer.record_step("T", "terminalize_refusal", payload=refusal)
                return refusal, tracer

            edges.append(e_id)
            row = [Fraction(0, 1) for _ in range(n_V)]
            # delta0: (δ₀ φ)_e = φ(head) - φ(tail)
            row[vert_idx_map[u]] = Fraction(-1, 1)
            row[vert_idx_map[v]] = Fraction(1, 1)
            delta0_mat.append(row)

    n_E = len(edges)
    if n_E > 200:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "EDGE_COUNT_OUT_OF_BOUNDS",
            "refusal_code": "EDGE_COUNT_OUT_OF_BOUNDS",
            "count": n_E,
        }
        tracer.record_step(
            "M", "refusal_edge_bound", payload=refusal, refusal_reason="EDGE_COUNT_OUT_OF_BOUNDS"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    edge_idx_map = {e: i for i, e in enumerate(edges)}

    # Parse delta1
    delta1_explicit = case.get("d1") or case.get("delta1")
    if delta1_explicit is not None:
        if isinstance(delta1_explicit, list):
            delta1_mat: list[list[Fraction]] = []
            for row in delta1_explicit:
                if not isinstance(row, list) or len(row) != n_E:
                    refusal = {
                        "id": case_id,
                        "status": "UNKNOWN",
                        "refusal": "MALFORMED_INPUT",
                        "refusal_code": "MALFORMED_INPUT",
                        "details": "delta1 row length mismatch",
                    }
                    tracer.record_step(
                        "M", "refusal_delta1_dim", payload=refusal, refusal_reason="MALFORMED_INPUT"
                    )
                    tracer.record_step("T", "terminalize_refusal", payload=refusal)
                    return refusal, tracer
                delta1_mat.append([parse_fraction(x) for x in row])
        elif isinstance(delta1_explicit, dict):
            delta1_mat = [[Fraction(0, 1) for _ in range(n_E)] for _ in range(len(faces))]
            for f_idx, f_id in enumerate(faces):
                f_row = delta1_explicit.get(f_id, {})
                for e_id, val in f_row.items():
                    if e_id in edge_idx_map:
                        delta1_mat[f_idx][edge_idx_map[e_id]] = parse_fraction(val)
        else:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_INPUT",
                "refusal_code": "MALFORMED_INPUT",
            }
            tracer.record_step(
                "M", "refusal_delta1_format", payload=refusal, refusal_reason="MALFORMED_INPUT"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer
    else:
        # Construct delta1 from face definitions:
        # e.g. case["faces"]: [{"id": "f0", "edges": {"e0": 1, "e1": 1, "e2": -1}}] or cycles
        delta1_mat = [[Fraction(0, 1) for _ in range(n_E)] for _ in range(len(faces))]
        for f_idx, f_raw in enumerate(raw_faces):
            if isinstance(f_raw, dict):
                f_bnd = f_raw.get("edges") or f_raw.get("boundary", {})
                if isinstance(f_bnd, dict):
                    for e_id, val in f_bnd.items():
                        if str(e_id) in edge_idx_map:
                            delta1_mat[f_idx][edge_idx_map[str(e_id)]] = parse_fraction(val)
                elif isinstance(f_bnd, list):
                    for item in f_bnd:
                        if isinstance(item, (list, tuple)) and len(item) == 2:
                            e_id, sign = str(item[0]), item[1]
                            if e_id in edge_idx_map:
                                delta1_mat[f_idx][edge_idx_map[e_id]] = parse_fraction(sign)
                        elif isinstance(item, str) and item in edge_idx_map:
                            delta1_mat[f_idx][edge_idx_map[item]] = Fraction(1, 1)
            elif isinstance(f_raw, str):
                # Check case["face_boundaries"]
                bnd = case.get("face_boundaries", {}).get(f_raw, {})
                for e_id, val in bnd.items():
                    if str(e_id) in edge_idx_map:
                        delta1_mat[f_idx][edge_idx_map[str(e_id)]] = parse_fraction(val)

    # Parse Flow f ∈ Q^E
    raw_flow = case.get("flow", {})
    flow_vec: list[Fraction] = []
    if isinstance(raw_flow, dict):
        for e in edges:
            val_raw = raw_flow.get(e, 0)
            try:
                frac = parse_fraction(val_raw)
            except Exception:
                refusal = {
                    "id": case_id,
                    "status": "UNKNOWN",
                    "refusal": "MALFORMED_INPUT",
                    "refusal_code": "MALFORMED_INPUT",
                    "details": f"Malformed flow entry {val_raw!r}",
                }
                tracer.record_step(
                    "M", "refusal_flow_format", payload=refusal, refusal_reason="MALFORMED_INPUT"
                )
                tracer.record_step("T", "terminalize_refusal", payload=refusal)
                return refusal, tracer

            if abs(frac.numerator) > 999 or abs(frac.denominator) > 999:
                refusal = {
                    "id": case_id,
                    "status": "UNKNOWN",
                    "refusal": "COEFFICIENT_BOUND_EXCEEDED",
                    "refusal_code": "COEFFICIENT_BOUND_EXCEEDED",
                    "flow_entry": str(frac),
                }
                tracer.record_step(
                    "M",
                    "refusal_flow_coeff",
                    payload=refusal,
                    refusal_reason="COEFFICIENT_BOUND_EXCEEDED",
                )
                tracer.record_step("T", "terminalize_refusal", payload=refusal)
                return refusal, tracer
            flow_vec.append(frac)
    elif isinstance(raw_flow, list):
        if len(raw_flow) != n_E:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_INPUT",
                "refusal_code": "MALFORMED_INPUT",
                "details": f"Flow list length {len(raw_flow)} != |E| {n_E}",
            }
            tracer.record_step(
                "M", "refusal_flow_len", payload=refusal, refusal_reason="MALFORMED_INPUT"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer
        for val_raw in raw_flow:
            frac = parse_fraction(val_raw)
            if abs(frac.numerator) > 999 or abs(frac.denominator) > 999:
                refusal = {
                    "id": case_id,
                    "status": "UNKNOWN",
                    "refusal": "COEFFICIENT_BOUND_EXCEEDED",
                    "refusal_code": "COEFFICIENT_BOUND_EXCEEDED",
                    "flow_entry": str(frac),
                }
                tracer.record_step(
                    "M",
                    "refusal_flow_coeff",
                    payload=refusal,
                    refusal_reason="COEFFICIENT_BOUND_EXCEEDED",
                )
                tracer.record_step("T", "terminalize_refusal", payload=refusal)
                return refusal, tracer
            flow_vec.append(frac)
    else:
        flow_vec = [Fraction(0, 1) for _ in range(n_E)]

    # Parse Weights W₁ = diag(w_e) > 0, default 1
    raw_weights = case.get("weights", {})
    weights_vec: list[Fraction] = []
    if isinstance(raw_weights, dict):
        for e in edges:
            w_raw = raw_weights.get(e, 1)
            try:
                w_frac = parse_fraction(w_raw)
            except Exception:
                refusal = {
                    "id": case_id,
                    "status": "UNKNOWN",
                    "refusal": "MALFORMED_INPUT",
                    "refusal_code": "MALFORMED_INPUT",
                    "details": f"Malformed weight {w_raw!r}",
                }
                tracer.record_step(
                    "M", "refusal_weight_format", payload=refusal, refusal_reason="MALFORMED_INPUT"
                )
                tracer.record_step("T", "terminalize_refusal", payload=refusal)
                return refusal, tracer

            if w_frac <= 0:
                refusal = {
                    "id": case_id,
                    "status": "UNKNOWN",
                    "refusal": "WEIGHT_NON_POSITIVE",
                    "refusal_code": "WEIGHT_NON_POSITIVE",
                    "weight": str(w_frac),
                }
                tracer.record_step(
                    "M",
                    "refusal_weight_non_positive",
                    payload=refusal,
                    refusal_reason="WEIGHT_NON_POSITIVE",
                )
                tracer.record_step("T", "terminalize_refusal", payload=refusal)
                return refusal, tracer

            if w_frac.denominator > 12:
                refusal = {
                    "id": case_id,
                    "status": "UNKNOWN",
                    "refusal": "WEIGHT_DENOMINATOR_EXCEEDED",
                    "refusal_code": "WEIGHT_DENOMINATOR_EXCEEDED",
                    "denominator": w_frac.denominator,
                }
                tracer.record_step(
                    "M",
                    "refusal_weight_denom",
                    payload=refusal,
                    refusal_reason="WEIGHT_DENOMINATOR_EXCEEDED",
                )
                tracer.record_step("T", "terminalize_refusal", payload=refusal)
                return refusal, tracer
            weights_vec.append(w_frac)
    elif isinstance(raw_weights, list):
        for w_raw in raw_weights:
            w_frac = parse_fraction(w_raw)
            if w_frac <= 0:
                refusal = {
                    "id": case_id,
                    "status": "UNKNOWN",
                    "refusal": "WEIGHT_NON_POSITIVE",
                    "refusal_code": "WEIGHT_NON_POSITIVE",
                    "weight": str(w_frac),
                }
                tracer.record_step(
                    "M",
                    "refusal_weight_non_positive",
                    payload=refusal,
                    refusal_reason="WEIGHT_NON_POSITIVE",
                )
                tracer.record_step("T", "terminalize_refusal", payload=refusal)
                return refusal, tracer
            if w_frac.denominator > 12:
                refusal = {
                    "id": case_id,
                    "status": "UNKNOWN",
                    "refusal": "WEIGHT_DENOMINATOR_EXCEEDED",
                    "refusal_code": "WEIGHT_DENOMINATOR_EXCEEDED",
                    "denominator": w_frac.denominator,
                }
                tracer.record_step(
                    "M",
                    "refusal_weight_denom",
                    payload=refusal,
                    refusal_reason="WEIGHT_DENOMINATOR_EXCEEDED",
                )
                tracer.record_step("T", "terminalize_refusal", payload=refusal)
                return refusal, tracer
            weights_vec.append(w_frac)
    else:
        weights_vec = [Fraction(1, 1) for _ in range(n_E)]

    tracer.record_step(
        "C",
        "intake_case",
        payload={
            "id": case_id,
            "n_V": n_V,
            "n_E": n_E,
            "n_F": len(faces),
        },
    )

    # Stage Lambda: Structural Lift & Coboundary Complex Invariant Check
    is_valid, witness, solution = compute_discrete_hodge_decomposition(
        vertices=vertices,
        edges=edges,
        faces=faces,
        delta0=delta0_mat,
        delta1=delta1_mat,
        flow=flow_vec,
        weights=weights_vec,
    )

    if not is_valid:
        oos = {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": witness,
        }
        tracer.record_step(
            "M", "out_of_scope_d1_d0_nonzero", payload=oos, refusal_reason="D1_D0_NONZERO"
        )
        tracer.record_step("T", "terminalize_out_of_scope", payload=oos)
        return oos, tracer

    tracer.record_step("Lambda", "lift_chain_complex", payload={"d1_d0_is_zero": True})

    # Stage D & E: Scale Descent & Exact Potentials Extraction
    tracer.record_step("D", "solve_normal_equations", payload={"L0_dim": n_V, "L2_dim": len(faces)})
    tracer.record_step(
        "E",
        "exact_potentials_and_harmonic_flow",
        payload={
            "phi_nonzero": len(solution["phi"]),
            "psi_nonzero": len(solution["psi"]),
            "h_nonzero": len(solution["h"]),
        },
    )

    # Stage R: Residual & Orthogonality
    tracer.record_step(
        "R",
        "verify_orthogonality",
        payload={
            "harmonic_dim": solution["harmonic_dim"],
            "basis_count": len(solution["harmonic_basis"]),
        },
    )

    # Stage I: Integration
    solution["id"] = case_id
    tracer.record_step("I", "integrate_hodge_certificate", payload=solution)

    # Stage T: Terminalization
    tracer.record_step("T", "terminalize_solved", payload={"status": "SOLVED"})

    return solution, tracer


def solve(case: Any) -> dict[str, Any]:
    """Participant API entrypoint."""
    res, _ = solve_with_trace(case)
    return res
