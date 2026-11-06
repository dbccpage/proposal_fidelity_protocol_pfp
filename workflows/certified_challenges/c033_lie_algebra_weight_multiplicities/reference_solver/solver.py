"""Frozen reference solver for C033 (Lie Algebra Weight Multiplicities).

Implements the contract:
  def solve(case: dict) -> dict

Supports:
  - 'character' query: returns dominant highest weight, total dimension, and dominant multiplicities
  - 'tensor' query: returns tensor product decomposition into irreducible representations
  - Canonical OUT_OF_SCOPE for non-integral labels and unsupported algebras
  - Canonical UNKNOWN refusals for dimension bounds, malformed cases, and length mismatches
  - Full DDC 8-letter operational trace logging

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from c033_lie_algebra_weight_multiplicities.reference_solver.ddc_tracer import (
    DDCTracer,
)
from c033_lie_algebra_weight_multiplicities.reference_solver.lie_algebra import (
    freudenthal_multiplicities,
    get_rank,
    is_algebra_supported,
    reflect_to_dominant,
    tensor_product_decomposition,
    weyl_dimension,
)

MAX_DIMENSION = 1_000_000


def solve(case: dict[str, Any]) -> dict[str, Any]:
    """Frozen solver entrypoint for C033."""
    if not isinstance(case, Mapping):
        return {
            "id": "unknown_case",
            "status": "UNKNOWN",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }

    case_id = case.get("case_id") or case.get("id") or "unnamed_case"
    if not isinstance(case_id, str):
        return {
            "id": "malformed_case_id",
            "status": "UNKNOWN",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }

    tracer = DDCTracer()

    # 1. Algebra validation
    algebra = case.get("algebra")
    if not isinstance(algebra, str):
        tracer.record_step("M", {"reason": "malformed_algebra_type"})
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "MALFORMED_CASE_STRUCTURE",
        }

    if not is_algebra_supported(algebra):
        tracer.record_step("M", {"unsupported_algebra": algebra})
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {
                "kind": "unsupported_algebra",
                "algebra": algebra,
            },
        }

    rank = get_rank(algebra)

    # 2. Query validation
    query = case.get("query")
    if query not in ("character", "tensor"):
        tracer.record_step("M", {"invalid_query": query})
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "INVALID_QUERY_TYPE",
        }

    tracer.record_step("C", {"case_id": case_id, "algebra": algebra, "query": query})

    # 3. Handle 'character' query
    if query == "character":
        weight_raw = case.get("weight")
        if not isinstance(weight_raw, list) or len(weight_raw) != rank:
            tracer.record_step(
                "M",
                {"bad_weight_length": len(weight_raw) if isinstance(weight_raw, list) else None},
            )
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal_code": "WEIGHT_DIMENSION_MISMATCH",
            }

        # Check for non-integral labels (floats, strings, fractions)
        for idx, val in enumerate(weight_raw):
            if type(val) is not int or isinstance(val, bool):
                tracer.record_step("M", {"non_integral_label_idx": idx, "val": str(val)})
                return {
                    "id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {
                        "kind": "non_integral_label",
                        "index": idx,
                    },
                }

        # Reflect input weight into dominant chamber
        tracer.record_step("D", {"input_weight": weight_raw})
        dom_weight = reflect_to_dominant(algebra, tuple(weight_raw))
        tracer.record_step("D", {"dominant_highest_weight": list(dom_weight)})

        # Pre-compute Weyl dimension to verify bounds
        dim = weyl_dimension(algebra, dom_weight)
        tracer.record_step("R", {"dimension": dim})
        if dim > MAX_DIMENSION:
            tracer.record_step("M", {"dimension_exceeded": dim})
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal_code": "DIMENSION_OUT_OF_BOUNDS",
            }

        # Freudenthal multiplicity integration
        tracer.record_step("I", {"algorithm": "freudenthal"})
        mults_dict = freudenthal_multiplicities(algebra, dom_weight, max_dimension=MAX_DIMENSION)

        # Format dominant multiplicities as sorted list of [[labels], mult]
        # Sorted lexicographically descending by weight labels
        dominant_mults = [
            [list(w), m]
            for w, m in sorted(mults_dict.items(), key=lambda item: item[0], reverse=True)
        ]

        tracer.record_step("E", {"dominant_weights_count": len(dominant_mults)})
        tracer.record_step("T", {"verdict": "SOLVED"})

        return {
            "id": case_id,
            "status": "SOLVED",
            "highest_weight": list(dom_weight),
            "dimension": dim,
            "dominant_multiplicities": dominant_mults,
        }

    # 4. Handle 'tensor' query
    if query == "tensor":
        left_raw = case.get("left")
        right_raw = case.get("right")

        if not isinstance(left_raw, list) or not isinstance(right_raw, list):
            tracer.record_step("M", {"malformed_tensor_factors": True})
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal_code": "MALFORMED_CASE_STRUCTURE",
            }

        if len(left_raw) != rank or len(right_raw) != rank:
            tracer.record_step("M", {"tensor_factor_length_mismatch": True})
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal_code": "WEIGHT_DIMENSION_MISMATCH",
            }

        # Check for non-integral labels in left factor
        for idx, val in enumerate(left_raw):
            if type(val) is not int or isinstance(val, bool):
                tracer.record_step("M", {"non_integral_left_idx": idx})
                return {
                    "id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {
                        "kind": "non_integral_label",
                        "index": idx,
                    },
                }

        # Check for non-integral labels in right factor
        for idx, val in enumerate(right_raw):
            if type(val) is not int or isinstance(val, bool):
                tracer.record_step("M", {"non_integral_right_idx": idx})
                return {
                    "id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {
                        "kind": "non_integral_label",
                        "index": idx,
                    },
                }

        # Reflect factors into dominant chamber
        tracer.record_step("D", {"left_input": left_raw, "right_input": right_raw})
        dom_left = reflect_to_dominant(algebra, tuple(left_raw))
        dom_right = reflect_to_dominant(algebra, tuple(right_raw))

        dim_left = weyl_dimension(algebra, dom_left)
        dim_right = weyl_dimension(algebra, dom_right)
        prod_dim = dim_left * dim_right

        tracer.record_step(
            "R", {"dim_left": dim_left, "dim_right": dim_right, "product_dim": prod_dim}
        )
        if prod_dim > MAX_DIMENSION:
            tracer.record_step("M", {"product_dim_exceeded": prod_dim})
            return {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal_code": "DIMENSION_OUT_OF_BOUNDS",
            }

        tracer.record_step("I", {"algorithm": "brauer_klimyk"})
        decomp_dict = tensor_product_decomposition(
            algebra,
            dom_left,
            dom_right,
            max_product_dimension=MAX_DIMENSION,
        )

        decomposition = [
            [list(w), m]
            for w, m in sorted(decomp_dict.items(), key=lambda item: item[0], reverse=True)
        ]

        tracer.record_step("E", {"components_count": len(decomposition)})
        tracer.record_step("T", {"verdict": "SOLVED"})

        return {
            "id": case_id,
            "status": "SOLVED",
            "decomposition": decomposition,
        }

    return {
        "id": case_id,
        "status": "UNKNOWN",
        "refusal_code": "INVALID_QUERY_TYPE",
    }
