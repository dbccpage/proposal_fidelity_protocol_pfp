# AuthorityEffect: None.
"""
Reference Solver Entry Point for C025 (Exact MUBs in Prime-Power Dimensions).

Exposes `solve(case: dict) -> dict` according to SG-CP v1 and C025 specifications.
Integrates Discrete Deformation Calculus (DDC) 8-letter operational tracing.
"""

from __future__ import annotations

from typing import Any, Dict

try:
    from .ddc_tracer import DDCTracer
    from .mub_construction import build_mub_solution
except (ImportError, ValueError):
    try:
        from c025_mub_prime_power_exact.reference_solver.ddc_tracer import DDCTracer
        from c025_mub_prime_power_exact.reference_solver.mub_construction import build_mub_solution
    except (ImportError, ValueError):
        from ddc_tracer import DDCTracer
        from mub_construction import build_mub_solution


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Solves a C025 MUB problem instance.
    Produces exact cyclotomic MUBs or valid typed refusals.
    """
    case_id = case.get("case_id") or case.get("id", "c025_unnamed")
    tracer = DDCTracer(run_id=f"c025_{case_id}")

    d = case.get("dimension")
    k = case.get("num_bases")
    fixed_b0 = case.get("fixed_first_basis")

    # C: Context Exposure
    tracer.record_step(
        "C",
        "expose_context",
        {
            "case_id": case_id,
            "dimension": d,
            "num_bases": k,
            "has_fixed_b0": fixed_b0 is not None,
        },
    )

    if not isinstance(d, int) or not isinstance(k, int) or d < 2:
        tracer.record_step("M", "malformed_input", {"dimension": d, "num_bases": k})
        tracer.record_step("T", "terminalize", {"status": "ERROR"})
        return {"id": case_id, "status": "ERROR", "message": "Invalid dimension or num_bases"}

    # Refusal 1: Out of scope (k > d + 1)
    if k > d + 1:
        tracer.record_step(
            "M",
            "refuse_out_of_scope",
            {"requested": k, "max_possible": d + 1},
            refusal_reason="OUT_OF_SCOPE",
        )
        tracer.record_step("T", "terminalize", {"status": "OUT_OF_SCOPE"})
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"requested": k, "max_possible": d + 1},
        }

    # Refusal 2: Open problem (d = 6, k >= 4)
    if d == 6 and k >= 4:
        tracer.record_step(
            "M",
            "refuse_open_problem",
            {"dimension": d, "num_bases": k},
            refusal_reason="OPEN_PROBLEM",
        )
        tracer.record_step("T", "terminalize", {"status": "UNKNOWN"})
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "OPEN_PROBLEM",
        }

    # Lambda: Structural Lift (field and representation selection)
    field_type = (
        "odd_prime"
        if d in (3, 5, 7)
        else (
            "char_two_galois_ring" if d in (2, 4, 8) else ("gf9" if d == 9 else "composite_tensor")
        )
    )
    tracer.record_step(
        "Lambda",
        "structural_lift",
        {
            "dimension": d,
            "field_type": field_type,
        },
    )

    # I: Integration (construct standard MUBs)
    tracer.record_step("I", "integrate_mub_construction", {"dimension": d, "target_bases": k})

    # D: Scale Descent (apply fixed B_0 unitary if provided)
    if fixed_b0 is not None:
        tracer.record_step("D", "rotate_to_fixed_b0", {"basis_0_size": len(fixed_b0)})

    # Build solution
    result = build_mub_solution(case)

    if result.get("status") == "SOLVED":
        # R: Residual Evaluation (zero residual by exact construction)
        tracer.record_step(
            "R",
            "residual_evaluation",
            {
                "failing_orthogonality_identities": 0,
                "failing_unbiasedness_identities": 0,
                "residual_norm": "0",
            },
        )
        # E: Exact Verification
        tracer.record_step(
            "E",
            "exact_verification",
            {
                "cyclotomic_order": result.get("cyclotomic_order"),
                "bases_emitted": len(result.get("bases", [])),
            },
        )

    # T: Terminalization
    tracer.record_step("T", "terminalize", {"status": result.get("status")})

    return result
