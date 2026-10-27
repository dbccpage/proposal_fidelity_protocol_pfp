# AuthorityEffect: None.
"""
Reference Solver for C029: Minimum-Weight Surface-Code Decoding.

Exposes:
    def solve(case: dict) -> dict
"""

from __future__ import annotations

from typing import Any, Dict

try:
    from .ddc_tracer import DDCTracer
    from .matching_solver import solve_min_weight_decoding
except (ImportError, ValueError):
    from ddc_tracer import DDCTracer
    from matching_solver import solve_min_weight_decoding


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decodes surface code or toric code syndrome with minimum-weight correction and dual certificate.
    """
    case_id = str(case.get("id") or case.get("case_id", "unknown"))
    tracer = DDCTracer(case_id)

    code_type = case.get("code", "rotated")
    distance = case.get("distance", 0)
    hz = case.get("hz", [])
    weights = case.get("weights", [])
    syndrome = case.get("syndrome", [])

    tracer.emit(
        "C",
        {
            "code_type": code_type,
            "distance": distance,
            "num_checks": len(hz),
            "num_qubits": len(hz[0]) if hz else 0,
            "syndrome_weight": sum(syndrome),
        },
    )

    # Execute decoding
    tracer.emit("I", {"step": "build_defect_graph"})
    ok, sol_data, witness = solve_min_weight_decoding(
        code_type=code_type,
        distance=distance,
        hz=hz,
        weights=weights,
        syndrome=syndrome,
    )

    if not ok:
        if "refusal_code" in witness:
            tracer.emit("M", {"refusal_code": witness["refusal_code"], "details": witness})
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal_code": witness["refusal_code"],
            }
        else:
            tracer.emit("R", {"kind": witness.get("kind"), "details": witness})
            tracer.emit("M", {"status": "OUT_OF_SCOPE", "witness": witness})
            return {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": witness,
            }

    tracer.emit("D", {"matched_defects": True, "correction_qubits": sol_data["correction"]})
    tracer.emit("E", {"weight": sol_data["weight"], "certificate": sol_data["certificate"]})
    tracer.emit("T", {"terminal_status": "SOLVED"})

    return {
        "id": case_id,
        "status": "SOLVED",
        "correction": sol_data["correction"],
        "weight": sol_data["weight"],
        "certificate": sol_data["certificate"],
    }
