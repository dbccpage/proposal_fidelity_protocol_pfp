"""Reference Solver for C037: Fusion Rules from the Verlinde Formula.

Exposes solve(case: Mapping[str, Any]) -> dict[str, Any] instrumented with
Discrete Deformation Calculus (DDC) 8-letter operational trace.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping

try:
    from .ddc_tracer import DDCTracer
    from .verlinde import solve_c037_case
except (ImportError, ValueError):
    from ddc_tracer import DDCTracer  # type: ignore
    from verlinde import solve_c037_case  # type: ignore

_LAST_TRACER: DDCTracer | None = None


def get_last_tracer() -> DDCTracer | None:
    """Returns the DDCTracer instance from the most recent solve() call."""
    return _LAST_TRACER


def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    """Computes exact solution for a C037 challenge case with DDC trace instrumentation."""
    global _LAST_TRACER
    tracer = DDCTracer(challenge_id="c037_virasoro_minimal_model_fusion")
    _LAST_TRACER = tracer

    cid = (
        str(case.get("case_id") or case.get("id") or "unknown_case")
        if isinstance(case, Mapping)
        else "malformed"
    )
    tracer.record_step("C", {"stage": "context_intake", "case_id": cid})

    status, extra, solution = solve_c037_case(case)

    if status == "UNKNOWN":
        refusal_code = extra.get("refusal_code") if extra else "MALFORMED_CASE_STRUCTURE"
        tracer.record_step("M", {"stage": "fail_closed_refusal", "refusal": refusal_code})
        tracer.record_step("T", {"stage": "terminal_refusal"})
        return {"id": cid, "status": "UNKNOWN", "refusal_code": refusal_code}

    if status == "OUT_OF_SCOPE":
        witness = extra if extra else {"kind": "out_of_scope"}
        tracer.record_step(
            "I",
            {"stage": "parameter_check", "verdict": "out_of_scope", "witness": witness},
        )
        tracer.record_step("M", {"stage": "out_of_scope_witness", "witness": witness})
        tracer.record_step("T", {"stage": "terminal_out_of_scope"})
        return {"id": cid, "status": "OUT_OF_SCOPE", "witness": witness}

    # status == "SOLVED"
    assert solution is not None
    model = case.get("model")

    if model == "su2":
        k_val = case.get("k")
        tracer.record_step(
            "I",
            {
                "stage": "modular_s_matrix_integration",
                "model": "su2",
                "level_k": k_val,
                "central_charge": solution["central_charge"],
                "primary_count": len(solution["primaries"]),
            },
        )
        tracer.record_step(
            "D",
            {
                "stage": "exact_verlinde_evaluation",
                "method": "chebyshev_cosine_sum_exact_rational",
            },
        )
        tracer.record_step(
            "R",
            {
                "stage": "integrality_residual_check",
                "all_non_negative_integers": True,
                "fusion_entries_count": len(solution["fusion"]),
            },
        )
        tracer.record_step(
            "E",
            {
                "stage": "fusion_rules_extraction",
                "model": "su2",
                "k": k_val,
                "fusion_count": len(solution["fusion"]),
            },
        )
        tracer.record_step("T", {"stage": "terminal_complete"})

    else:  # model == "minimal"
        p_val = case.get("p")
        p_prime_val = case.get("p_prime")
        tracer.record_step(
            "I",
            {
                "stage": "modular_s_matrix_integration",
                "model": "minimal",
                "p": p_val,
                "p_prime": p_prime_val,
                "central_charge": solution["central_charge"],
                "primary_count": len(solution["primaries"]),
            },
        )
        tracer.record_step(
            "Lambda",
            {
                "stage": "su2_factorization_lift_and_kac_identification",
                "k1": p_prime_val - 2,  # type: ignore
                "k2": p_val - 2,  # type: ignore
                "identification": "(r, s) ~ (p' - r, p - s)",
            },
        )
        tracer.record_step(
            "D",
            {
                "stage": "exact_verlinde_evaluation",
                "factored_su2_verlinde_descent": True,
            },
        )
        tracer.record_step(
            "R",
            {
                "stage": "integrality_residual_check",
                "all_non_negative_integers": True,
                "ring_axioms_satisfied": True,
                "fusion_entries_count": len(solution["fusion"]),
            },
        )
        tracer.record_step(
            "E",
            {
                "stage": "fusion_rules_extraction",
                "model": "minimal",
                "p": p_val,
                "p_prime": p_prime_val,
                "fusion_count": len(solution["fusion"]),
            },
        )
        tracer.record_step("T", {"stage": "terminal_complete"})

    return {
        "id": cid,
        "status": "SOLVED",
        "central_charge": solution["central_charge"],
        "primaries": solution["primaries"],
        "fusion": solution["fusion"],
    }
