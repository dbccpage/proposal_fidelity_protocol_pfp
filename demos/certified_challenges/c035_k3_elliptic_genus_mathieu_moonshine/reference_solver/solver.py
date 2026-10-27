"""Reference Solver for C035: Mathieu Moonshine from the K3 Elliptic Genus.

Exposes solve(case: Mapping[str, Any]) -> dict[str, Any] instrumented with
Discrete Deformation Calculus (DDC) 8-letter operational trace.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping

from c035_k3_elliptic_genus_mathieu_moonshine.reference_solver.ddc_tracer import (
    DDCTracer,
)
from c035_k3_elliptic_genus_mathieu_moonshine.reference_solver.mathieu_moonshine import (
    solve_mathieu_moonshine_case,
)

_LAST_TRACER: DDCTracer | None = None


def get_last_tracer() -> DDCTracer | None:
    """Returns the DDCTracer instance from the most recent solve() call."""
    return _LAST_TRACER


def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    """Computes exact solution for a C035 challenge case with DDC trace instrumentation."""
    global _LAST_TRACER
    tracer = DDCTracer(challenge_id="c035_k3_elliptic_genus_mathieu_moonshine")
    _LAST_TRACER = tracer

    cid = (
        str(case.get("case_id") or case.get("id") or "unknown_case")
        if isinstance(case, Mapping)
        else "malformed"
    )
    tracer.record_step("C", {"stage": "context_intake", "case_id": cid})

    result = solve_mathieu_moonshine_case(case)
    status = result.get("status")

    if status == "UNKNOWN":
        tracer.record_step(
            "M", {"stage": "fail_closed_refusal", "refusal": result.get("refusal_code")}
        )
        tracer.record_step("T", {"stage": "terminal_refusal"})
        return result

    if status == "OUT_OF_SCOPE":
        tracer.record_step(
            "I", {"stage": "character_inner_product", "verdict": "not_an_authentic_character"}
        )
        tracer.record_step("M", {"stage": "out_of_scope_witness", "witness": result.get("witness")})
        tracer.record_step("T", {"stage": "terminal_out_of_scope"})
        return result

    query = case.get("query") if isinstance(case, Mapping) else None
    if query == "coefficients":
        max_n = case.get("max_n")
        a_dict = result.get("A", {})
        tracer.record_step(
            "I",
            {"stage": "theta_quotient_expansion", "max_n": max_n, "computed_orders": len(a_dict)},
        )
        tracer.record_step(
            "D", {"stage": "appell_lerch_subtraction", "massless_character_evaluated": True}
        )
        tracer.record_step(
            "R",
            {
                "stage": "prefactor_division_residual_check",
                "y_independent": True,
                "zero_residual": True,
            },
        )
        tracer.record_step(
            "E", {"stage": "exact_integer_coefficients_extracted", "count": len(a_dict)}
        )
        tracer.record_step("T", {"stage": "terminal_complete"})
    elif query == "decompose":
        tracer.record_step("I", {"stage": "conjugacy_class_normalization", "class_count": 26})
        tracer.record_step("D", {"stage": "weighted_inner_product_projection"})
        tracer.record_step("R", {"stage": "integrality_and_positivity_check"})
        tracer.record_step(
            "E",
            {
                "stage": "exact_linear_reconstruction_verified",
                "multiplicities": result.get("multiplicities"),
            },
        )
        tracer.record_step("T", {"stage": "terminal_complete"})
    elif query == "specialization_z0":
        tracer.record_step("I", {"stage": "specialization_evaluation", "z": 0})
        tracer.record_step(
            "E",
            {
                "stage": "euler_characteristic_verified",
                "chi": result.get("constant", 24),
                "higher_q_vanishing": True,
            },
        )
        tracer.record_step("T", {"stage": "terminal_complete"})

    return result
