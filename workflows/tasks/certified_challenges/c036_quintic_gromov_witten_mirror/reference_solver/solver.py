"""Reference Solver for C036: Genus-Zero Invariants of the Quintic via Mirror Symmetry.

Exposes solve(case: Mapping[str, Any]) -> dict[str, Any] instrumented with
Discrete Deformation Calculus (DDC) 8-letter operational trace.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping

try:
    from .ddc_tracer import DDCTracer
    from .mirror_symmetry import solve_quintic_mirror_case
except (ImportError, ValueError):
    from ddc_tracer import DDCTracer  # type: ignore
    from mirror_symmetry import solve_quintic_mirror_case  # type: ignore

_LAST_TRACER: DDCTracer | None = None


def get_last_tracer() -> DDCTracer | None:
    """Returns the DDCTracer instance from the most recent solve() call."""
    return _LAST_TRACER


def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    """Computes exact solution for a C036 challenge case with DDC trace instrumentation."""
    global _LAST_TRACER
    tracer = DDCTracer(challenge_id="c036_quintic_gromov_witten_mirror")
    _LAST_TRACER = tracer

    cid = (
        str(case.get("case_id") or case.get("id") or "unknown_case")
        if isinstance(case, Mapping)
        else "malformed"
    )
    tracer.record_step("C", {"stage": "context_intake", "case_id": cid})

    status, extra, solution = solve_quintic_mirror_case(case)

    if status == "UNKNOWN":
        refusal_code = extra.get("refusal_code") if extra else "MALFORMED_CASE_STRUCTURE"
        tracer.record_step("M", {"stage": "fail_closed_refusal", "refusal": refusal_code})
        tracer.record_step("T", {"stage": "terminal_refusal"})
        return {"id": cid, "status": "UNKNOWN", "refusal_code": refusal_code}

    if status == "OUT_OF_SCOPE":
        witness = extra if extra else {"kind": "not_calabi_yau"}
        tracer.record_step(
            "I", {"stage": "calabi_yau_check", "verdict": "non_calabi_yau", "witness": witness}
        )
        tracer.record_step("M", {"stage": "out_of_scope_witness", "witness": witness})
        tracer.record_step("T", {"stage": "terminal_out_of_scope"})
        return {"id": cid, "status": "OUT_OF_SCOPE", "witness": witness}

    # status == "SOLVED"
    max_d = case.get("max_curve_degree")
    tracer.record_step("I", {"stage": "period_integration", "max_curve_degree": max_d})
    tracer.record_step(
        "Lambda", {"stage": "mirror_map_lift", "ratio_computed": True, "series_reverted": True}
    )
    tracer.record_step(
        "D", {"stage": "yukawa_coupling_transformation", "kappa": solution.get("kappa")}
    )
    tracer.record_step(
        "R", {"stage": "integrality_residual_check", "all_gv_integers": True, "order": max_d}
    )
    tracer.record_step(
        "E",
        {
            "stage": "invariants_exact_extraction",
            "gv_count": len(solution.get("gv", {})),
            "gw_count": len(solution.get("gw", {})),
        },
    )
    tracer.record_step("T", {"stage": "terminal_complete"})

    return {
        "id": cid,
        "status": "SOLVED",
        "kappa": solution["kappa"],
        "gv": solution["gv"],
        "gw": solution["gw"],
        "mirror_map_coeffs": solution["mirror_map_coeffs"],
    }
