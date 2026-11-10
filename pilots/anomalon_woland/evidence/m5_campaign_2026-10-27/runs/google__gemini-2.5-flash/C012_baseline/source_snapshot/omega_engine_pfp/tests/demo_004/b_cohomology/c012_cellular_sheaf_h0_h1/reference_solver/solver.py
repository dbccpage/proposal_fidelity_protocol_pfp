"""Clean Reference Solver for C012 (Cellular Sheaf Cohomology H^0 and H^1).

Standard library only. Exposes def solve(case: Mapping[str, Any]) -> dict[str, Any].
Produces exact rational H^0 basis, H^1 complement basis, and for each target cochain
a gluing section x (glues: true) or dual obstruction witness eta in ker delta^T (glues: false).
Produces structured witness for OUT_OF_SCOPE cases (restriction shape mismatch, self loop, unknown endpoint).
Produces closed-list refusal codes for UNKNOWN out-of-bounds or malformed cases.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

try:
    from .ddc_tracer import DDCTracer
    from .sheaf_cohomology import (
        CLOSED_OOS_REASONS,
        CLOSED_REFUSAL_CODES,
        eliminate_augmented,
        extract_h0_basis,
        extract_h1_complement,
        format_canonical_rational,
        parse_canonical_rational,
        solve_sheaf_targets,
    )
except (ImportError, ValueError):
    try:
        from reference_solver.ddc_tracer import DDCTracer
        from reference_solver.sheaf_cohomology import (
            CLOSED_OOS_REASONS,
            CLOSED_REFUSAL_CODES,
            eliminate_augmented,
            extract_h0_basis,
            extract_h1_complement,
            format_canonical_rational,
            parse_canonical_rational,
            solve_sheaf_targets,
        )
    except (ImportError, ValueError):
        from ddc_tracer import DDCTracer
        from sheaf_cohomology import (
            eliminate_augmented,
            extract_h0_basis,
            extract_h1_complement,
            format_canonical_rational,
            parse_canonical_rational,
            solve_sheaf_targets,
        )


def solve_with_trace(
    case: Mapping[str, Any],
    tracer: DDCTracer | None = None,
) -> tuple[dict[str, Any], DDCTracer]:
    """Solves a C012 case with machine-verifiable DDC 8-letter trace logging."""
    if tracer is None:
        case_id_raw = case.get("id") if isinstance(case, Mapping) else "unnamed_case"
        tracer = DDCTracer(run_id=f"c012_{case_id_raw}")

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

    case_id = case.get("id") or case.get("case_id") or "c012_case"
    if not isinstance(case_id, str):
        case_id = str(case_id)

    raw_vertices = case.get("vertices")
    if not isinstance(raw_vertices, list):
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "MALFORMED_CASE_STRUCTURE",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }
        tracer.record_step(
            "M",
            "refusal_vertices_not_list",
            payload=refusal,
            refusal_reason="MALFORMED_CASE_STRUCTURE",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    if len(raw_vertices) < 1 or len(raw_vertices) > 30:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "VERTEX_COUNT_OUT_OF_BOUNDS",
            "refusal_code": "VERTEX_COUNT_OUT_OF_BOUNDS",
        }
        tracer.record_step(
            "M",
            "refusal_vertex_count",
            payload=refusal,
            refusal_reason="VERTEX_COUNT_OUT_OF_BOUNDS",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    vertex_offsets: dict[str, int] = {}
    vertex_dims: dict[str, int] = {}
    dim_C0 = 0
    seen_vertices: set[str] = set()

    for idx, v_spec in enumerate(raw_vertices):
        if isinstance(v_spec, Mapping):
            vid = v_spec.get("id")
            d_v = v_spec.get("dim")
        elif isinstance(v_spec, str):
            vid = v_spec
            stalks_dict = (
                case.get("stalks", {}).get("vertices", {})
                if isinstance(case.get("stalks"), Mapping)
                else {}
            )
            d_v = stalks_dict.get(vid, 1)
        else:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_CASE_STRUCTURE",
                "refusal_code": "MALFORMED_CASE_STRUCTURE",
            }
            tracer.record_step(
                "M",
                "refusal_vertex_spec",
                payload=refusal,
                refusal_reason="MALFORMED_CASE_STRUCTURE",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        if not isinstance(vid, str) or not vid or vid in seen_vertices:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_CASE_STRUCTURE",
                "refusal_code": "MALFORMED_CASE_STRUCTURE",
            }
            tracer.record_step(
                "M",
                "refusal_duplicate_vertex",
                payload=refusal,
                refusal_reason="MALFORMED_CASE_STRUCTURE",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        if not isinstance(d_v, int) or d_v < 0 or d_v > 4:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "STALK_DIM_OUT_OF_BOUNDS",
                "refusal_code": "STALK_DIM_OUT_OF_BOUNDS",
            }
            tracer.record_step(
                "M", "refusal_stalk_dim", payload=refusal, refusal_reason="STALK_DIM_OUT_OF_BOUNDS"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        seen_vertices.add(vid)
        vertex_offsets[vid] = dim_C0
        vertex_dims[vid] = d_v
        dim_C0 += d_v

    if dim_C0 > 240:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "STALK_DIM_OUT_OF_BOUNDS",
            "refusal_code": "STALK_DIM_OUT_OF_BOUNDS",
        }
        tracer.record_step(
            "M", "refusal_total_c0_dim", payload=refusal, refusal_reason="STALK_DIM_OUT_OF_BOUNDS"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

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

    if len(raw_edges) > 60:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "EDGE_COUNT_OUT_OF_BOUNDS",
            "refusal_code": "EDGE_COUNT_OUT_OF_BOUNDS",
        }
        tracer.record_step(
            "M", "refusal_edge_count", payload=refusal, refusal_reason="EDGE_COUNT_OUT_OF_BOUNDS"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    edge_offsets: dict[str, int] = {}
    edge_dims: dict[str, int] = {}
    dim_C1 = 0
    parsed_edges: list[dict[str, Any]] = []
    seen_edge_ids: set[str] = set()

    for idx, e_spec in enumerate(raw_edges):
        if not isinstance(e_spec, Mapping):
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_CASE_STRUCTURE",
                "refusal_code": "MALFORMED_CASE_STRUCTURE",
            }
            tracer.record_step(
                "M", "refusal_edge_spec", payload=refusal, refusal_reason="MALFORMED_CASE_STRUCTURE"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        eid = e_spec.get("id") or f"e{idx}"
        u = e_spec.get("u") or e_spec.get("tail")
        v = e_spec.get("v") or e_spec.get("head")
        d_e = e_spec.get("dim")
        if d_e is None:
            stalks_dict = (
                case.get("stalks", {}).get("edges", {})
                if isinstance(case.get("stalks"), Mapping)
                else {}
            )
            d_e = stalks_dict.get(eid, 1)

        if eid in seen_edge_ids:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_CASE_STRUCTURE",
                "refusal_code": "MALFORMED_CASE_STRUCTURE",
            }
            tracer.record_step(
                "M",
                "refusal_duplicate_edge",
                payload=refusal,
                refusal_reason="MALFORMED_CASE_STRUCTURE",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer
        seen_edge_ids.add(eid)

        if not isinstance(d_e, int) or d_e < 0 or d_e > 4:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "STALK_DIM_OUT_OF_BOUNDS",
                "refusal_code": "STALK_DIM_OUT_OF_BOUNDS",
            }
            tracer.record_step(
                "M",
                "refusal_edge_stalk_dim",
                payload=refusal,
                refusal_reason="STALK_DIM_OUT_OF_BOUNDS",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        # Check for OUT_OF_SCOPE: unknown endpoint or self loop
        if u not in seen_vertices or v not in seen_vertices:
            oos = {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"edge": eid, "reason": "UNKNOWN_ENDPOINT"},
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
                "witness": {"edge": eid, "reason": "SELF_LOOP"},
            }
            tracer.record_step(
                "M", "out_of_scope_self_loop", payload=oos, refusal_reason="SELF_LOOP"
            )
            tracer.record_step("T", "terminalize_out_of_scope", payload=oos)
            return oos, tracer

        # Restrictions
        F_u_raw = e_spec.get("F_u")
        if F_u_raw is None:
            F_u_raw = e_spec.get("F_tail")
        F_v_raw = e_spec.get("F_v")
        if F_v_raw is None:
            F_v_raw = e_spec.get("F_head")
        if F_u_raw is None or F_v_raw is None:
            restr_dict = (
                case.get("restrictions", {})
                if isinstance(case.get("restrictions"), Mapping)
                else {}
            )
            e_restr = restr_dict.get(eid, {}) if isinstance(restr_dict.get(eid), Mapping) else {}
            if F_u_raw is None:
                F_u_raw = e_restr.get(u)
            if F_v_raw is None:
                F_v_raw = e_restr.get(v)

        d_u = vertex_dims[u]
        d_v = vertex_dims[v]

        # Validate restriction shapes
        if not isinstance(F_u_raw, list) or len(F_u_raw) != d_e:
            oos = {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {
                    "edge": eid,
                    "endpoint": u,
                    "expected_shape": [d_e, d_u],
                    "actual_shape": [len(F_u_raw) if isinstance(F_u_raw, list) else None, None],
                    "reason": "RESTRICTION_SHAPE_MISMATCH",
                },
            }
            tracer.record_step(
                "M",
                "out_of_scope_shape_mismatch_u",
                payload=oos,
                refusal_reason="RESTRICTION_SHAPE_MISMATCH",
            )
            tracer.record_step("T", "terminalize_out_of_scope", payload=oos)
            return oos, tracer

        for r_idx, r in enumerate(F_u_raw):
            if not isinstance(r, list) or len(r) != d_u:
                oos = {
                    "id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {
                        "edge": eid,
                        "endpoint": u,
                        "expected_shape": [d_e, d_u],
                        "actual_shape": [d_e, len(r) if isinstance(r, list) else None],
                        "reason": "RESTRICTION_SHAPE_MISMATCH",
                    },
                }
                tracer.record_step(
                    "M",
                    "out_of_scope_shape_mismatch_u_row",
                    payload=oos,
                    refusal_reason="RESTRICTION_SHAPE_MISMATCH",
                )
                tracer.record_step("T", "terminalize_out_of_scope", payload=oos)
                return oos, tracer

        if not isinstance(F_v_raw, list) or len(F_v_raw) != d_e:
            oos = {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {
                    "edge": eid,
                    "endpoint": v,
                    "expected_shape": [d_e, d_v],
                    "actual_shape": [len(F_v_raw) if isinstance(F_v_raw, list) else None, None],
                    "reason": "RESTRICTION_SHAPE_MISMATCH",
                },
            }
            tracer.record_step(
                "M",
                "out_of_scope_shape_mismatch_v",
                payload=oos,
                refusal_reason="RESTRICTION_SHAPE_MISMATCH",
            )
            tracer.record_step("T", "terminalize_out_of_scope", payload=oos)
            return oos, tracer

        for r_idx, r in enumerate(F_v_raw):
            if not isinstance(r, list) or len(r) != d_v:
                oos = {
                    "id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {
                        "edge": eid,
                        "endpoint": v,
                        "expected_shape": [d_e, d_v],
                        "actual_shape": [d_e, len(r) if isinstance(r, list) else None],
                        "reason": "RESTRICTION_SHAPE_MISMATCH",
                    },
                }
                tracer.record_step(
                    "M",
                    "out_of_scope_shape_mismatch_v_row",
                    payload=oos,
                    refusal_reason="RESTRICTION_SHAPE_MISMATCH",
                )
                tracer.record_step("T", "terminalize_out_of_scope", payload=oos)
                return oos, tracer

        # Parse restriction values
        F_u_frac: list[list[Fraction]] = []
        for row in F_u_raw:
            row_frac: list[Fraction] = []
            for item in row:
                try:
                    val = parse_canonical_rational(item)
                    if abs(val.numerator) > 99 or abs(val.denominator) > 99:
                        refusal = {
                            "id": case_id,
                            "status": "UNKNOWN",
                            "refusal": "COEFFICIENT_BOUND_EXCEEDED",
                            "refusal_code": "COEFFICIENT_BOUND_EXCEEDED",
                        }
                        tracer.record_step(
                            "M",
                            "refusal_coeff_bound",
                            payload=refusal,
                            refusal_reason="COEFFICIENT_BOUND_EXCEEDED",
                        )
                        tracer.record_step("T", "terminalize_refusal", payload=refusal)
                        return refusal, tracer
                    row_frac.append(val)
                except Exception:
                    refusal = {
                        "id": case_id,
                        "status": "UNKNOWN",
                        "refusal": "MALFORMED_RESTRICTION_MATRIX",
                        "refusal_code": "MALFORMED_RESTRICTION_MATRIX",
                    }
                    tracer.record_step(
                        "M",
                        "refusal_malformed_restr",
                        payload=refusal,
                        refusal_reason="MALFORMED_RESTRICTION_MATRIX",
                    )
                    tracer.record_step("T", "terminalize_refusal", payload=refusal)
                    return refusal, tracer
            F_u_frac.append(row_frac)

        F_v_frac: list[list[Fraction]] = []
        for row in F_v_raw:
            row_frac: list[Fraction] = []
            for item in row:
                try:
                    val = parse_canonical_rational(item)
                    if abs(val.numerator) > 99 or abs(val.denominator) > 99:
                        refusal = {
                            "id": case_id,
                            "status": "UNKNOWN",
                            "refusal": "COEFFICIENT_BOUND_EXCEEDED",
                            "refusal_code": "COEFFICIENT_BOUND_EXCEEDED",
                        }
                        tracer.record_step(
                            "M",
                            "refusal_coeff_bound",
                            payload=refusal,
                            refusal_reason="COEFFICIENT_BOUND_EXCEEDED",
                        )
                        tracer.record_step("T", "terminalize_refusal", payload=refusal)
                        return refusal, tracer
                    row_frac.append(val)
                except Exception:
                    refusal = {
                        "id": case_id,
                        "status": "UNKNOWN",
                        "refusal": "MALFORMED_RESTRICTION_MATRIX",
                        "refusal_code": "MALFORMED_RESTRICTION_MATRIX",
                    }
                    tracer.record_step(
                        "M",
                        "refusal_malformed_restr",
                        payload=refusal,
                        refusal_reason="MALFORMED_RESTRICTION_MATRIX",
                    )
                    tracer.record_step("T", "terminalize_refusal", payload=refusal)
                    return refusal, tracer
            F_v_frac.append(row_frac)

        edge_offsets[eid] = dim_C1
        edge_dims[eid] = d_e
        dim_C1 += d_e

        parsed_edges.append(
            {
                "id": eid,
                "u": u,
                "v": v,
                "dim": d_e,
                "F_u": F_u_frac,
                "F_v": F_v_frac,
            }
        )

    if dim_C1 > 240:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "STALK_DIM_OUT_OF_BOUNDS",
            "refusal_code": "STALK_DIM_OUT_OF_BOUNDS",
        }
        tracer.record_step(
            "M", "refusal_total_c1_dim", payload=refusal, refusal_reason="STALK_DIM_OUT_OF_BOUNDS"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    # Parse target cochains
    raw_targets = case.get("targets", [])
    if not isinstance(raw_targets, list) or len(raw_targets) > 3:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "MALFORMED_CASE_STRUCTURE",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }
        tracer.record_step(
            "M", "refusal_targets_count", payload=refusal, refusal_reason="MALFORMED_CASE_STRUCTURE"
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    parsed_targets: list[list[Fraction]] = []
    for t_idx, t_spec in enumerate(raw_targets):
        if not isinstance(t_spec, Mapping) or "b" not in t_spec:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_TARGET_COCHAIN",
                "refusal_code": "MALFORMED_TARGET_COCHAIN",
            }
            tracer.record_step(
                "M",
                "refusal_target_not_mapping",
                payload=refusal,
                refusal_reason="MALFORMED_TARGET_COCHAIN",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        b_raw = t_spec["b"]
        if not isinstance(b_raw, list) or len(b_raw) != dim_C1:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_TARGET_COCHAIN",
                "refusal_code": "MALFORMED_TARGET_COCHAIN",
            }
            tracer.record_step(
                "M",
                "refusal_target_len_mismatch",
                payload=refusal,
                refusal_reason="MALFORMED_TARGET_COCHAIN",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        b_frac: list[Fraction] = []
        for val_str in b_raw:
            try:
                b_frac.append(parse_canonical_rational(val_str))
            except Exception:
                refusal = {
                    "id": case_id,
                    "status": "UNKNOWN",
                    "refusal": "MALFORMED_TARGET_COCHAIN",
                    "refusal_code": "MALFORMED_TARGET_COCHAIN",
                }
                tracer.record_step(
                    "M",
                    "refusal_target_rational_parse",
                    payload=refusal,
                    refusal_reason="MALFORMED_TARGET_COCHAIN",
                )
                tracer.record_step("T", "terminalize_refusal", payload=refusal)
                return refusal, tracer
        parsed_targets.append(b_frac)

    tracer.record_step(
        "C",
        "intake_sheaf_structure",
        payload={
            "vertices_count": len(raw_vertices),
            "edges_count": len(parsed_edges),
            "dim_C0": dim_C0,
            "dim_C1": dim_C1,
            "targets_count": len(parsed_targets),
        },
    )

    # Step 2: Structural Lift (Lambda) - Assemble block coboundary matrix delta
    delta = [[Fraction(0, 1) for _ in range(dim_C0)] for _ in range(dim_C1)]
    for e in parsed_edges:
        e_row_start = edge_offsets[e["id"]]
        u_col_start = vertex_offsets[e["u"]]
        v_col_start = vertex_offsets[e["v"]]
        d_e = e["dim"]
        d_u = vertex_dims[e["u"]]
        d_v = vertex_dims[e["v"]]

        # Tail restriction (- F_u)
        for r in range(d_e):
            for c in range(d_u):
                delta[e_row_start + r][u_col_start + c] -= e["F_u"][r][c]

        # Head restriction (+ F_v)
        for r in range(d_e):
            for c in range(d_v):
                delta[e_row_start + r][v_col_start + c] += e["F_v"][r][c]

    tracer.record_step(
        "Lambda",
        "assemble_block_coboundary_matrix",
        payload={"dim_C0": dim_C0, "dim_C1": dim_C1},
    )

    # Step 3: Scale Descent (D) - Single-pass Gauss-Jordan Elimination
    rank, pivot_cols, augmented = eliminate_augmented(delta, parsed_targets)
    tracer.record_step(
        "D",
        "gauss_jordan_block_descent",
        payload={"rank": rank, "nullity": dim_C0 - rank},
    )

    # Step 4: Exact Solution Extraction (E) - H^0 basis and H^1 complement
    h0_basis = extract_h0_basis(rank, pivot_cols, augmented, dim_C0)
    h1_complement = extract_h1_complement(delta, rank)
    h0_dim = len(h0_basis)
    h1_dim = len(h1_complement)

    tracer.record_step(
        "E",
        "extract_h0_and_h1_bases",
        payload={"h0_dim": h0_dim, "h1_dim": h1_dim},
    )

    # Step 5: Residual & Obstruction Projection (R) - Target solving
    target_results = solve_sheaf_targets(
        rank=rank,
        pivot_cols=pivot_cols,
        augmented=augmented,
        delta=delta,
        targets=parsed_targets,
        N0=dim_C0,
        N1=dim_C1,
    )
    tracer.record_step(
        "R",
        "solve_target_gluing_and_obstructions",
        payload={"targets_solved": len(target_results)},
    )

    # Step 6: Integration (I) - Certificate synthesis
    result = {
        "id": case_id,
        "status": "SOLVED",
        "h0_dim": str(h0_dim),
        "h0_basis": [[format_canonical_rational(val) for val in vec] for vec in h0_basis],
        "h1_dim": str(h1_dim),
        "h1_complement": [[format_canonical_rational(val) for val in vec] for vec in h1_complement],
        "targets": target_results,
    }
    tracer.record_step("I", "integrate_certificate", payload={"id": case_id})

    # Step 7: Terminalization (T)
    tracer.record_step("T", "terminalize_solved", payload={"id": case_id})

    return result, tracer


def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    """Solves a C012 cellular sheaf challenge case and returns certificate dictionary."""
    result, _ = solve_with_trace(case)
    return result
