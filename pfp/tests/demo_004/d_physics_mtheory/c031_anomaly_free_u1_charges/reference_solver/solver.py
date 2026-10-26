"""Reference Solver for C031 (Anomaly-Free Chiral U(1) Charge Assignments).

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

try:
    from .ddc_tracer import DDCTracer
    from .diophantine_u1 import (
        complete_chiral_u1,
        enumerate_chiral_u1,
    )
except (ImportError, ValueError):
    from ddc_tracer import DDCTracer
    from diophantine_u1 import (
        complete_chiral_u1,
        enumerate_chiral_u1,
    )


def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    """Pure Python reference solver for C031."""
    res, _ = solve_with_trace(case, tracer=None)
    return res


def solve_with_trace(
    case: Mapping[str, Any],
    tracer: DDCTracer | None = None,
) -> tuple[dict[str, Any], DDCTracer]:
    """Executes C031 reference solver with machine-verifiable DDC 8-letter trace logging."""
    if tracer is None:
        tracer = DDCTracer(run_id="c031_solver_run")

    # Step C: Context Exposure
    if not isinstance(case, Mapping):
        tracer.record_step("C", "context_intake", payload={"raw_type": type(case).__name__})
        tracer.record_step("M", "typed_refusal", refusal_reason="MALFORMED_CASE_STRUCTURE")
        out = {
            "id": "unknown",
            "status": "UNKNOWN",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }
        tracer.record_step("T", "terminalization", payload={"status": "UNKNOWN"})
        return out, tracer

    case_id = str(case.get("id") or case.get("case_id") or "unnamed_case")
    query = case.get("query")
    n = case.get("n")
    bound = case.get("bound")

    tracer.record_step(
        "C",
        "context_intake",
        payload={"case_id": case_id, "query": query, "n": n, "bound": bound},
    )

    # Validate structure and query
    if query not in {"enumerate", "complete"}:
        tracer.record_step("M", "typed_refusal", refusal_reason="MALFORMED_QUERY_TYPE")
        out = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "MALFORMED_QUERY_TYPE",
        }
        tracer.record_step("T", "terminalization", payload={"status": "UNKNOWN"})
        return out, tracer

    if type(n) is not int or type(bound) is not int:
        tracer.record_step("M", "typed_refusal", refusal_reason="MALFORMED_CASE_STRUCTURE")
        out = {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }
        tracer.record_step("T", "terminalization", payload={"status": "UNKNOWN"})
        return out, tracer

    # Query: enumerate bounds
    if query == "enumerate":
        if n < 1 or n > 10:
            tracer.record_step("M", "typed_refusal", refusal_reason="N_OUT_OF_BOUNDS")
            out = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal_code": "N_OUT_OF_BOUNDS",
            }
            tracer.record_step("T", "terminalization", payload={"status": "UNKNOWN"})
            return out, tracer

        if bound < 1 or bound > 12:
            tracer.record_step("M", "typed_refusal", refusal_reason="BOUND_OUT_OF_BOUNDS")
            out = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal_code": "BOUND_OUT_OF_BOUNDS",
            }
            tracer.record_step("T", "terminalization", payload={"status": "UNKNOWN"})
            return out, tracer

        # Execute enumeration
        tracer.record_step("Lambda", "structural_lift", payload={"quotient": "canonical_symmetry"})
        tracer.record_step("D", "dimension_descent", payload={"target_n": n, "bound": bound})
        solutions = enumerate_chiral_u1(n, bound)
        tracer.record_step("E", "exact_solution_certified", payload={"count": len(solutions)})

        out = {
            "id": case_id,
            "status": "SOLVED",
            "count": len(solutions),
            "solutions": solutions,
        }
        tracer.record_step("T", "terminalization", payload={"status": "SOLVED"})
        return out, tracer

    # Query: complete
    if query == "complete":
        if n < 1 or n > 12:
            tracer.record_step("M", "typed_refusal", refusal_reason="N_OUT_OF_BOUNDS")
            out = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal_code": "N_OUT_OF_BOUNDS",
            }
            tracer.record_step("T", "terminalization", payload={"status": "UNKNOWN"})
            return out, tracer

        if bound < 1 or bound > 2_000_000:
            tracer.record_step("M", "typed_refusal", refusal_reason="BOUND_OUT_OF_BOUNDS")
            out = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal_code": "BOUND_OUT_OF_BOUNDS",
            }
            tracer.record_step("T", "terminalization", payload={"status": "UNKNOWN"})
            return out, tracer

        fixed = case.get("fixed")
        if not isinstance(fixed, list) or not all(type(x) is int for x in fixed):
            tracer.record_step("M", "typed_refusal", refusal_reason="MALFORMED_CASE_STRUCTURE")
            out = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal_code": "MALFORMED_CASE_STRUCTURE",
            }
            tracer.record_step("T", "terminalization", payload={"status": "UNKNOWN"})
            return out, tracer

        # Check OUT_OF_SCOPE conditions
        # 1. Any fixed charge is zero
        for idx, q_val in enumerate(fixed):
            if q_val == 0:
                tracer.record_step(
                    "M",
                    "typed_refusal",
                    refusal_reason="fixed_charge_zero",
                    payload={"index": idx, "charge": 0},
                )
                out = {
                    "id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {
                        "kind": "fixed_charge_zero",
                        "index": idx,
                        "charge": 0,
                    },
                }
                tracer.record_step("T", "terminalization", payload={"status": "OUT_OF_SCOPE"})
                return out, tracer

        # 2. Any fixed charge exceeds bound
        for idx, q_val in enumerate(fixed):
            if abs(q_val) > bound:
                tracer.record_step(
                    "M",
                    "typed_refusal",
                    refusal_reason="fixed_charge_exceeds_bound",
                    payload={"index": idx, "charge": q_val, "bound": bound},
                )
                out = {
                    "id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {
                        "kind": "fixed_charge_exceeds_bound",
                        "index": idx,
                        "charge": q_val,
                        "bound": bound,
                    },
                }
                tracer.record_step("T", "terminalization", payload={"status": "OUT_OF_SCOPE"})
                return out, tracer

        # 3. Too many fixed charges (len(fixed) >= n)
        if len(fixed) >= n:
            tracer.record_step(
                "M",
                "typed_refusal",
                refusal_reason="too_many_fixed_charges",
                payload={"count": len(fixed), "n": n},
            )
            out = {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {
                    "kind": "too_many_fixed_charges",
                    "count": len(fixed),
                    "n": n,
                },
            }
            tracer.record_step("T", "terminalization", payload={"status": "OUT_OF_SCOPE"})
            return out, tracer

        # Integrate fixed charges
        s_fixed = sum(fixed)
        c_fixed = sum(x * x * x for x in fixed)
        tracer.record_step(
            "I",
            "integrate_fixed",
            payload={
                "k": len(fixed),
                "s_fixed": s_fixed,
                "c_fixed": c_fixed,
            },
        )
        tracer.record_step(
            "R",
            "residual_projection",
            payload={"target_s": -s_fixed, "target_c": -c_fixed},
        )
        tracer.record_step("D", "dimension_descent", payload={"remaining_dim": n - len(fixed)})

        completion = complete_chiral_u1(n, bound, fixed)
        if completion is not None:
            tracer.record_step("E", "exact_solution_certified", payload={"completion": completion})
            out = {
                "id": case_id,
                "status": "SOLVED",
                "completion": completion,
            }
        else:
            tracer.record_step("M", "typed_refusal", refusal_reason="NO_COMPLETION_EXISTS")
            out = {
                "id": case_id,
                "status": "SOLVED",
                "completion": None,
                "claim": "NO_COMPLETION",
            }
        tracer.record_step("T", "terminalization", payload={"status": "SOLVED"})
        return out, tracer

    # Fallthrough (unreachable)
    return {"id": case_id, "status": "UNKNOWN", "refusal_code": "MALFORMED_QUERY_TYPE"}, tracer
