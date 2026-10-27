"""Reference Solver for C034: Calabi-Yau Hodge Numbers from Reflexive Polytopes.

Exposes solve(case: Mapping[str, Any]) -> dict[str, Any] instrumented with
Discrete Deformation Calculus (DDC) 8-letter operational trace.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping

from pfp.tests.demo_004.d_physics_mtheory.c034_calabi_yau_hodge_numbers.reference_solver.calabi_yau import (
    solve_calabi_yau_polytope,
)
from pfp.tests.demo_004.d_physics_mtheory.c034_calabi_yau_hodge_numbers.reference_solver.ddc_tracer import (
    DDCTracer,
)


def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    """Computes reflexivity, face data, and Batyrev Hodge numbers for 4D lattice polytope."""
    tracer = DDCTracer(challenge_id="c034_calabi_yau_hodge_numbers")

    # Step 1: C (Expose / Context)
    cid = (
        str(case.get("case_id") or case.get("id") or "unknown_case")
        if isinstance(case, Mapping)
        else "malformed"
    )
    tracer.record_step("C", {"stage": "context_intake", "case_id": cid})

    # Execute math solver
    result = solve_calabi_yau_polytope(case)
    status = result.get("status")

    if status == "UNKNOWN":
        tracer.record_step(
            "M", {"stage": "fail_closed_refusal", "refusal": result.get("refusal_code")}
        )
        tracer.record_step("T", {"stage": "terminal_refusal"})
        return result

    if status == "OUT_OF_SCOPE":
        tracer.record_step("I", {"stage": "facet_inspection", "verdict": "non_reflexive"})
        tracer.record_step("M", {"stage": "out_of_scope_witness", "witness": result.get("witness")})
        tracer.record_step("T", {"stage": "terminal_out_of_scope"})
        return result

    # SOLVED: Trace full Batyrev pipeline
    tracer.record_step(
        "I",
        {
            "stage": "facets_and_polar_dual",
            "l_delta": result.get("face_data", {}).get("l_delta"),
            "l_delta_star": result.get("face_data", {}).get("l_delta_star"),
        },
    )
    tracer.record_step(
        "Lambda",
        {
            "stage": "face_lattice_and_codim2",
            "codim2_count": len(result.get("face_data", {}).get("codim2_products", [])),
        },
    )
    tracer.record_step(
        "R",
        {
            "stage": "residual_mirror_check",
            "h11": result.get("h11"),
            "h21": result.get("h21"),
        },
    )
    tracer.record_step(
        "D",
        {
            "stage": "batyrev_descent",
            "euler": result.get("euler"),
        },
    )
    tracer.record_step(
        "E",
        {
            "stage": "exact_closure",
            "reflexive": True,
        },
    )
    tracer.record_step(
        "T",
        {
            "stage": "terminal_complete",
        },
    )

    return result
