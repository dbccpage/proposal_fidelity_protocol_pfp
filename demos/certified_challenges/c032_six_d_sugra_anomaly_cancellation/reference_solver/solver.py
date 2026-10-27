"""Reference Solver for C032 (Six-Dimensional Supergravity Anomaly Cancellation).

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

try:
    from .ddc_tracer import DdcTracer
    from .sugra_6d import evaluate_6d_sugra_spectrum
except (ImportError, ValueError):
    from ddc_tracer import DdcTracer
    from sugra_6d import evaluate_6d_sugra_spectrum


def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    """Pure Python reference solver for C032."""
    res, _ = solve_with_trace(case, tracer=None)
    return res


def solve_with_trace(
    case: Mapping[str, Any],
    tracer: DdcTracer | None = None,
) -> tuple[dict[str, Any], DdcTracer]:
    """Executes C032 reference solver with machine-verifiable DDC 8-letter trace logging."""
    if tracer is None:
        tracer = DdcTracer(challenge_id="c032_six_d_sugra_anomaly_cancellation")

    # Step C: Context Exposure
    if not isinstance(case, Mapping):
        tracer.emit_step("context_intake", "C", payload={"raw_type": type(case).__name__})
        tracer.emit_step("typed_refusal", "M", payload={"refusal": "MALFORMED_CASE_STRUCTURE"})
        out = {
            "id": "unknown",
            "status": "UNKNOWN",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }
        tracer.emit_step("terminalization", "T", payload={"status": "UNKNOWN"})
        return out, tracer

    case_id = str(case.get("id") or "unnamed_case")
    tracer.emit_step("context_intake", "C", payload={"id": case_id, "T": case.get("T")})

    # Step I: Integrate weight systems and evaluate conditions
    tracer.emit_step("evaluate_spectrum", "I", payload={"case_id": case_id})
    res = evaluate_6d_sugra_spectrum(case)

    # Step R/D: Record descent and residual status
    status = res.get("status")
    if status == "SOLVED":
        verdict = res.get("verdict")
        if verdict == "PASSES_NECESSARY_CONDITIONS":
            tracer.emit_step("descent_verified", "D", payload={"verdict": verdict})
        else:
            # First failing condition
            tracer.emit_step("condition_violated", "M", payload=res.get("first_failure"))
    elif status == "OUT_OF_SCOPE":
        tracer.emit_step("out_of_scope_detected", "Lambda", payload=res.get("witness"))
    elif status == "UNKNOWN":
        tracer.emit_step("typed_refusal", "M", payload={"refusal_code": res.get("refusal_code")})

    # Step T: Terminalization
    tracer.emit_step("terminalization", "T", payload={"id": case_id, "status": status})
    return res, tracer
