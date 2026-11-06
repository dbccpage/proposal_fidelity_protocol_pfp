"""Frozen reference solver for Challenge C040 (M-Theory on Tori: Cremmer-Julia Scalar Counting).

Implements the contract:
  def solve(case: Mapping[str, Any]) -> dict[str, Any]

Query types:
  1. "scalars": Scalar field breakdown by origin (internal metric, internal 3-form, dual forms) and total.
  2. "coset": E_{k(k)} noncompact group and maximal compact subgroup K names, dimensions, and difference.
  3. "branching": Adjoint representation branching decomposition under K (Adj(K) (+) p).
  4. "vectors": Vector fields in D dimensions by origin, including dualized forms.

Refusals:
  - "K_OUT_OF_BOUNDS": k < 1, k > 8, float k, bool k, or non-integer k.
  - "UNKNOWN_QUERY_TYPE": query not in {"scalars", "coset", "branching", "vectors"}.
  - "MALFORMED_CASE_STRUCTURE": non-dict case, missing ID, missing k/query, wrong types.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

try:
    from .coset_algebra import get_branching, get_coset_info
    from .ddc_tracer import DDCTracer
    from .field_reduction import (
        compute_scalars_breakdown,
        compute_undualized_fields,
        compute_vectors_breakdown,
    )
except ImportError:
    from coset_algebra import get_branching, get_coset_info  # type: ignore
    from ddc_tracer import DDCTracer  # type: ignore
    from field_reduction import (  # type: ignore
        compute_scalars_breakdown,
        compute_undualized_fields,
        compute_vectors_breakdown,
    )

SUPPORTED_QUERIES = frozenset({"scalars", "coset", "branching", "vectors"})

# Global slot for inspecting the most recent trace in tests
_LAST_TRACER: DDCTracer | None = None


def get_last_tracer() -> DDCTracer | None:
    """Returns the most recently executed DDCTracer instance."""
    return _LAST_TRACER


def is_exact_int(val: Any) -> bool:
    """Strictly checks whether val is an integer and NOT a boolean or float."""
    return type(val) is int and not isinstance(val, bool)


def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    """Frozen solver entrypoint for Challenge C040."""
    global _LAST_TRACER

    # 1. Structural case validation
    if not isinstance(case, Mapping):
        return {
            "id": "unknown_case",
            "status": "UNKNOWN",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }

    case_id = case.get("id") or case.get("case_id")
    if not isinstance(case_id, str):
        return {
            "id": "malformed_case_id",
            "status": "UNKNOWN",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }

    tracer = DDCTracer()
    _LAST_TRACER = tracer

    # 2. Key existence check
    if "k" not in case:
        tracer.record_step("M", {"reason": "missing_k"})
        tracer.record_step("T", {"verdict": "REFUSE"})
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }

    if "query" not in case:
        tracer.record_step("M", {"reason": "missing_query"})
        tracer.record_step("T", {"verdict": "REFUSE"})
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }

    query = case.get("query")
    if not isinstance(query, str):
        tracer.record_step("M", {"reason": "non_string_query"})
        tracer.record_step("T", {"verdict": "REFUSE"})
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }

    # 3. Exact integer validation on k and bounds checking
    k = case.get("k")
    if not is_exact_int(k):
        tracer.record_step("M", {"reason": "k_not_exact_int", "raw_k": str(k)})
        tracer.record_step("T", {"verdict": "REFUSE"})
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "K_OUT_OF_BOUNDS",
        }

    if k < 1 or k > 8:
        tracer.record_step("M", {"reason": "k_out_of_range", "k": k})
        tracer.record_step("T", {"verdict": "REFUSE"})
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "K_OUT_OF_BOUNDS",
        }

    # 4. Query type validation
    if query not in SUPPORTED_QUERIES:
        tracer.record_step("M", {"reason": "unsupported_query", "query": query})
        tracer.record_step("T", {"verdict": "REFUSE"})
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "UNKNOWN_QUERY_TYPE",
        }

    D = 11 - k

    # DDC Step C: Expose case parameter and field context
    tracer.record_step("C", {"case_id": case_id, "k": k, "D": D, "query": query})

    # DDC Step I: Integrate un-dualized internal field content
    undualized = compute_undualized_fields(k)
    tracer.record_step("I", {"undualized": undualized})

    # 5. Route query execution
    if query == "scalars":
        scalars_breakdown = compute_scalars_breakdown(k)
        tracer.record_step("Lambda", {"dualized_scalars": scalars_breakdown})

        coset_info = get_coset_info(k)
        residual = scalars_breakdown["total"] - coset_info["difference"]
        tracer.record_step(
            "R",
            {
                "field_total": scalars_breakdown["total"],
                "coset_diff": coset_info["difference"],
                "residual": residual,
            },
        )

        tracer.record_step("D", {"residual_zero": residual == 0})
        tracer.record_step("E", {"exact_match": True, "count": scalars_breakdown["total"]})
        tracer.record_step("T", {"verdict": "SOLVED"})

        return {
            "id": case_id,
            "status": "SOLVED",
            "k": k,
            "D": D,
            "scalars": scalars_breakdown,
        }

    elif query == "coset":
        coset_info = get_coset_info(k)
        field_total = compute_scalars_breakdown(k)["total"]
        residual = coset_info["difference"] - field_total
        tracer.record_step(
            "R",
            {
                "coset_diff": coset_info["difference"],
                "field_total": field_total,
                "residual": residual,
            },
        )
        tracer.record_step("E", {"coset": coset_info})
        tracer.record_step("T", {"verdict": "SOLVED"})

        return {
            "id": case_id,
            "status": "SOLVED",
            "k": k,
            "D": D,
            "coset": coset_info,
        }

    elif query == "branching":
        branching = get_branching(k)
        coset_info = get_coset_info(k)

        sum_dims = sum(rep[1] for rep in branching)
        dim_g = coset_info["dimG"]
        tracer.record_step(
            "D", {"sum_dimensions": sum_dims, "dimG": dim_g, "conserved": sum_dims == dim_g}
        )
        tracer.record_step("E", {"branching": branching})
        tracer.record_step("T", {"verdict": "SOLVED"})

        return {
            "id": case_id,
            "status": "SOLVED",
            "k": k,
            "D": D,
            "branching": branching,
        }

    elif query == "vectors":
        vectors_breakdown = compute_vectors_breakdown(k)
        tracer.record_step("Lambda", {"vectors_breakdown": vectors_breakdown})
        tracer.record_step("E", {"total_vectors": vectors_breakdown["total"]})
        tracer.record_step("T", {"verdict": "SOLVED"})

        return {
            "id": case_id,
            "status": "SOLVED",
            "k": k,
            "D": D,
            "vectors": vectors_breakdown,
        }

    tracer.record_step("M", {"unreachable": True})
    tracer.record_step("T", {"verdict": "REFUSE"})
    return {
        "id": case_id,
        "status": "UNKNOWN",
        "refusal_code": "UNKNOWN_QUERY_TYPE",
    }
