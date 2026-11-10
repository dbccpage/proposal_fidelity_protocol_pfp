# AuthorityEffect: None.
"""
Reference Solver for C026 (Frustration-Free Projector Hamiltonians).

Solves problem instances by deciding whether K = bigcap_i ker(P_i (x) I) is nonzero.
Returns either the full exact ground space kernel basis or a certified left inverse.
"""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from .ddc_tracer import DDCTracer
    from .gaussian_rational import GaussianRat
    from .kronecker import extend_local_matrix
    from .linear_algebra import (
        compute_left_inverse,
        compute_rref_and_kernel,
    )
    from .projector_validator import validate_projector
except (ImportError, ValueError):
    try:
        from reference_solver.ddc_tracer import DDCTracer
        from reference_solver.gaussian_rational import GaussianRat
        from reference_solver.kronecker import extend_local_matrix
        from reference_solver.linear_algebra import (
            compute_left_inverse,
            compute_rref_and_kernel,
        )
        from reference_solver.projector_validator import validate_projector
    except (ImportError, ValueError):
        from ddc_tracer import DDCTracer
        from gaussian_rational import GaussianRat
        from kronecker import extend_local_matrix
        from linear_algebra import (
            compute_left_inverse,
            compute_rref_and_kernel,
        )
        from projector_validator import validate_projector


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Solves a C026 Frustration-Free Projector Hamiltonian instance.
    """
    case_id = case.get("case_id", "ff_case")
    tracer = DDCTracer(run_id=f"c026_{case_id}")

    local_dims = case.get("local_dims")
    terms_raw = case.get("terms")

    # C: Context Exposure
    tracer.record_step(
        "C",
        "expose_context",
        {
            "case_id": case_id,
            "local_dims": local_dims,
            "num_terms": len(terms_raw) if isinstance(terms_raw, list) else None,
        },
    )

    if not isinstance(local_dims, list) or not isinstance(terms_raw, list):
        tracer.record_step("M", "malformed_case", {"reason": "missing_required_fields"})
        tracer.record_step("T", "terminalize", {"status": "OUT_OF_SCOPE"})
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"kind": "malformed_case", "field": "local_dims_or_terms"},
        }

    n_sites = len(local_dims)
    total_d = 1
    for d in local_dims:
        if type(d) is not int or d not in (2, 3):
            tracer.record_step(
                "M",
                "invalid_local_dimension",
                {"site_dim": d},
                refusal_reason="INVALID_LOCAL_DIMENSION",
            )
            tracer.record_step("T", "terminalize", {"status": "UNKNOWN"})
            return {"id": case_id, "status": "UNKNOWN", "refusal_code": "INVALID_LOCAL_DIMENSION"}
        total_d *= d

    if total_d > 64:
        tracer.record_step(
            "M",
            "dimension_out_of_bounds",
            {"total_dimension": total_d},
            refusal_reason="DIMENSION_OUT_OF_BOUNDS",
        )
        tracer.record_step("T", "terminalize", {"status": "UNKNOWN"})
        return {"id": case_id, "status": "UNKNOWN", "refusal_code": "DIMENSION_OUT_OF_BOUNDS"}

    # Parse and validate terms
    parsed_terms: List[Dict[str, Any]] = []
    for term_idx, term in enumerate(terms_raw):
        if not isinstance(term, dict):
            tracer.record_step("M", "malformed_term", {"term_idx": term_idx})
            tracer.record_step("T", "terminalize", {"status": "OUT_OF_SCOPE"})
            return {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"kind": "malformed_term", "term": term_idx},
            }

        support = term.get("support")
        if not isinstance(support, list) or len(support) > 3:
            tracer.record_step(
                "M", "invalid_support", {"support": support}, refusal_reason="INVALID_SUPPORT"
            )
            tracer.record_step("T", "terminalize", {"status": "UNKNOWN"})
            return {"id": case_id, "status": "UNKNOWN", "refusal_code": "INVALID_SUPPORT"}

        for s in support:
            if type(s) is not int or s < 0 or s >= n_sites:
                tracer.record_step(
                    "M",
                    "site_index_out_of_bounds",
                    {"site": s, "n_sites": n_sites},
                    refusal_reason="SITE_OUT_OF_BOUNDS",
                )
                tracer.record_step("T", "terminalize", {"status": "UNKNOWN"})
                return {"id": case_id, "status": "UNKNOWN", "refusal_code": "SITE_OUT_OF_BOUNDS"}

        mat_raw = term.get("matrix")
        if not isinstance(mat_raw, list):
            tracer.record_step("M", "missing_matrix", {"term_idx": term_idx})
            tracer.record_step("T", "terminalize", {"status": "OUT_OF_SCOPE"})
            return {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"kind": "malformed_matrix", "term": term_idx},
            }

        # Parse matrix elements
        try:
            mat: List[List[GaussianRat]] = [
                [GaussianRat.from_wire(elem) for elem in row] for row in mat_raw
            ]
        except Exception as ex:
            tracer.record_step("M", "unparseable_matrix", {"term_idx": term_idx, "error": str(ex)})
            tracer.record_step("T", "terminalize", {"status": "OUT_OF_SCOPE"})
            return {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"kind": "unparseable_matrix", "term": term_idx},
            }

        # Validate projector: P^2 = P and P^\dagger = P
        is_proj, reason, offending_entry = validate_projector(mat)
        if not is_proj:
            tracer.record_step(
                "M",
                "malformed_projector",
                {"term": term_idx, "reason": reason, "entry": offending_entry},
                refusal_reason="NOT_A_PROJECTOR",
            )
            tracer.record_step("T", "terminalize", {"status": "OUT_OF_SCOPE"})
            return {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {
                    "term": term_idx,
                    "reason": reason,
                    "entry": offending_entry,
                },
            }

        parsed_terms.append(
            {
                "term_idx": term_idx,
                "support": support,
                "weight": term.get("weight", "1"),
                "matrix": mat,
            }
        )

    # Lambda: Structural Lift (Kronecker extension of each local term)
    tracer.record_step(
        "Lambda",
        "kronecker_extension",
        {
            "n_sites": n_sites,
            "total_dimension": total_d,
            "terms_count": len(parsed_terms),
        },
    )

    extended_matrices: List[List[List[GaussianRat]]] = []
    stacked_rows: List[List[GaussianRat]] = []

    for pt in parsed_terms:
        ext_p = extend_local_matrix(local_dims, pt["support"], pt["matrix"])
        extended_matrices.append(ext_p)
        stacked_rows.extend(ext_p)

    # I: Integration & D: Scale Descent (running kernel reduction)
    tracer.record_step(
        "I", "begin_kernel_intersection", {"stacked_rows": len(stacked_rows), "cols": total_d}
    )

    _, rank, kernel_basis = compute_rref_and_kernel(stacked_rows)
    kernel_dim = len(kernel_basis)

    tracer.record_step(
        "D",
        "intersect_kernels",
        {
            "stacked_rank": rank,
            "kernel_dimension": kernel_dim,
        },
    )

    if kernel_dim > 0:
        # Frustration-free: non-zero common kernel
        tracer.record_step("E", "exact_kernel_certified", {"kernel_dim": kernel_dim})
        tracer.record_step("T", "terminalize", {"status": "SOLVED", "frustration_free": True})

        wire_basis = [[v.to_wire() for v in vec] for vec in kernel_basis]
        return {
            "id": case_id,
            "status": "SOLVED",
            "frustration_free": True,
            "kernel_dim": kernel_dim,
            "kernel_basis": wire_basis,
        }
    else:
        # Frustrated: kernel is {0}, full column rank => construct left inverse L * M = I_D
        tracer.record_step("R", "frustration_detected", {"kernel_dim": 0})
        L = compute_left_inverse(stacked_rows)
        tracer.record_step("E", "left_inverse_certified", {"rows": len(L), "cols": len(L[0])})
        tracer.record_step("T", "terminalize", {"status": "SOLVED", "frustration_free": False})

        wire_L = [[elem.to_wire() for elem in row] for row in L]
        return {
            "id": case_id,
            "status": "SOLVED",
            "frustration_free": False,
            "certificate": {
                "kind": "left_inverse",
                "matrix": wire_L,
            },
        }
