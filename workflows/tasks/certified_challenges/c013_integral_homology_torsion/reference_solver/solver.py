"""Reference Solver for C013: Integral Homology with Torsion and Smith Normal Form.

Computes integral homology groups H_n(K; Z) and exact unimodular Smith Normal Form
certificates U·∂_n·V = D over abstract simplicial complexes.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

try:
    from .ddc_tracer import DDCTracer
    from .simplicial_homology import (
        check_face_closure,
        compute_simplicial_integral_homology,
    )
except ImportError:
    from ddc_tracer import DDCTracer  # type: ignore
    from simplicial_homology import (  # type: ignore
        check_face_closure,
        compute_simplicial_integral_homology,
    )


def solve_with_trace(case: Any) -> tuple[dict[str, Any], DDCTracer]:
    """Evaluates case and records machine-verifiable DDC operational trace.

    Returns:
        (result_dict, ddc_tracer)
    """
    case_id = str(case.get("id") or "unnamed_case") if isinstance(case, Mapping) else "unnamed_case"
    tracer = DDCTracer(run_id=f"c013_{case_id}")

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

    raw_simplices = case.get("simplices")
    if not isinstance(raw_simplices, list):
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "MALFORMED_CASE_STRUCTURE",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }
        tracer.record_step(
            "M",
            "refusal_simplices_not_list",
            payload=refusal,
            refusal_reason="MALFORMED_CASE_STRUCTURE",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    # Check simplex count bounds: 1 <= |K| <= 1000
    if len(raw_simplices) < 1 or len(raw_simplices) > 1000:
        refusal = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal": "SIMPLEX_COUNT_OUT_OF_BOUNDS",
            "refusal_code": "SIMPLEX_COUNT_OUT_OF_BOUNDS",
            "count": len(raw_simplices),
        }
        tracer.record_step(
            "M",
            "refusal_simplex_count",
            payload=refusal,
            refusal_reason="SIMPLEX_COUNT_OUT_OF_BOUNDS",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    tracer.record_step(
        "C", "intake_case", payload={"id": case_id, "simplex_count": len(raw_simplices)}
    )

    # Validate individual simplices
    cleaned_simplices: list[list[int]] = []
    for idx, s in enumerate(raw_simplices):
        if not isinstance(s, list) or len(s) == 0:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_INPUT",
                "refusal_code": "MALFORMED_INPUT",
                "details": f"simplex at index {idx} is not a non-empty list",
            }
            tracer.record_step(
                "M", "refusal_simplex_structure", payload=refusal, refusal_reason="MALFORMED_INPUT"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        # Check dimension: dimension = len(s) - 1 <= 3
        if len(s) - 1 > 3 or len(s) - 1 < 0:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "DIMENSION_OUT_OF_BOUNDS",
                "refusal_code": "DIMENSION_OUT_OF_BOUNDS",
                "dimension": len(s) - 1,
            }
            tracer.record_step(
                "M",
                "refusal_dimension_bound",
                payload=refusal,
                refusal_reason="DIMENSION_OUT_OF_BOUNDS",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        # Check vertex label types and bounds
        s_int: list[int] = []
        for v in s:
            if not isinstance(v, int):
                # Check if it can be an integer
                if isinstance(v, str) and (v.isdigit() or (v.startswith("-") and v[1:].isdigit())):
                    v = int(v)
                else:
                    refusal = {
                        "id": case_id,
                        "status": "UNKNOWN",
                        "refusal": "MALFORMED_INPUT",
                        "refusal_code": "MALFORMED_INPUT",
                        "details": f"non-integer vertex {v!r}",
                    }
                    tracer.record_step(
                        "M",
                        "refusal_vertex_type",
                        payload=refusal,
                        refusal_reason="MALFORMED_INPUT",
                    )
                    tracer.record_step("T", "terminalize_refusal", payload=refusal)
                    return refusal, tracer

            if abs(v) > 10_000:
                refusal = {
                    "id": case_id,
                    "status": "UNKNOWN",
                    "refusal": "COEFFICIENT_BOUND_EXCEEDED",
                    "refusal_code": "COEFFICIENT_BOUND_EXCEEDED",
                    "vertex": v,
                }
                tracer.record_step(
                    "M",
                    "refusal_vertex_bound",
                    payload=refusal,
                    refusal_reason="COEFFICIENT_BOUND_EXCEEDED",
                )
                tracer.record_step("T", "terminalize_refusal", payload=refusal)
                return refusal, tracer
            s_int.append(v)

        if len(set(s_int)) != len(s_int):
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_INPUT",
                "refusal_code": "MALFORMED_INPUT",
                "details": f"duplicate vertex labels in simplex {s_int}",
            }
            tracer.record_step(
                "M", "refusal_duplicate_vertex", payload=refusal, refusal_reason="MALFORMED_INPUT"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        cleaned_simplices.append(s_int)

    # Stage Lambda: Structural Lift & Face Closure Check
    is_closed, witness, simplex_set = check_face_closure(cleaned_simplices)
    if not is_closed:
        if witness and "missing_face" in witness:
            oos = {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": witness,
            }
            tracer.record_step(
                "M",
                "out_of_scope_not_closed_under_faces",
                payload=oos,
                refusal_reason="NOT_CLOSED_UNDER_FACES",
            )
            tracer.record_step("T", "terminalize_out_of_scope", payload=oos)
            return oos, tracer
        else:
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "MALFORMED_INPUT",
                "refusal_code": "MALFORMED_INPUT",
                "details": str(witness),
            }
            tracer.record_step(
                "M", "refusal_malformed_closure", payload=refusal, refusal_reason="MALFORMED_INPUT"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

    tracer.record_step(
        "Lambda", "lift_simplicial_complex", payload={"unique_simplices": len(simplex_set)}
    )

    # Stage D & E: Scale Descent & Exact Solution via Smith Normal Form
    homology, snf_certs = compute_simplicial_integral_homology(simplex_set)
    tracer.record_step(
        "D", "smith_normal_form_descent", payload={"snf_matrices_count": len(snf_certs)}
    )
    tracer.record_step(
        "E", "exact_invariants_extracted", payload={"homology_degrees": len(homology)}
    )

    # Stage R: Residual & Torsion Projection
    total_torsion_factors = sum(len(h["torsion"]) for h in homology)
    tracer.record_step(
        "R", "torsion_projection", payload={"total_torsion_factors": total_torsion_factors}
    )

    # Stage I: Integration
    solution = {
        "id": case_id,
        "status": "SOLVED",
        "homology": homology,
        "snf": snf_certs,
    }
    tracer.record_step("I", "integrate_integral_homology_certificate", payload=solution)

    # Stage T: Terminalization
    tracer.record_step("T", "terminalize_solved", payload={"status": "SOLVED"})

    return solution, tracer


def solve(case: Any) -> dict[str, Any]:
    """Participant API entrypoint."""
    res, _ = solve_with_trace(case)
    return res
