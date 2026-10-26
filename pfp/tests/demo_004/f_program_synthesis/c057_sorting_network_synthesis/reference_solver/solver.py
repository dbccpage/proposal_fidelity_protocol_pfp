"""
Reference Solver for C057: Sorting Network Synthesis.

Implements def solve(case: dict) -> dict under SG-CP v1 protocol.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from .sorting_network import (
    INFO_THEORETIC_LOWER_BOUND,
    PROVEN_OPTIMAL_SIZE,
    synthesize_sorting_network,
    verify_01,
)


def validate_comparator(c: Any, n: int) -> Tuple[bool, Optional[str]]:
    """Validate that comparator is [i, j] with 0 <= i < j < n and integer types."""
    if not isinstance(c, (list, tuple)):
        return False, "COMPARATOR_NOT_LIST"
    if len(c) != 2:
        return False, "COMPARATOR_INVALID_LENGTH"
    i, j = c
    if isinstance(i, bool) or isinstance(j, bool):
        return False, "COMPARATOR_CHANNEL_IS_BOOLEAN"
    if not isinstance(i, int) or not isinstance(j, int):
        return False, "COMPARATOR_CHANNEL_NOT_INTEGER"
    if i < 0 or j < 0 or i >= n or j >= n:
        return False, "COMPARATOR_CHANNEL_OUT_OF_BOUNDS"
    if i == j:
        return False, "COMPARATOR_SELF_LOOP"
    if i > j:
        return False, "COMPARATOR_NOT_ORDERED"
    return True, None


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for C057 Sorting Network Synthesis.
    """
    if not isinstance(case, dict):
        return {
            "case_id": "unknown",
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "CASE_NOT_DICT"},
        }

    case_id = case.get("case_id")
    if not isinstance(case_id, str):
        return {
            "case_id": "unknown",
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "INVALID_CASE_ID"},
        }

    # Validate n
    n = case.get("n")
    if isinstance(n, bool) or not isinstance(n, int):
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "INVALID_N_TYPE"},
        }
    if n < 4 or n > 12:
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "N_OUT_OF_BOUNDS", "n": n},
        }

    # Validate k
    k = case.get("k")
    if isinstance(k, bool) or not isinstance(k, int):
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "INVALID_K_TYPE"},
        }
    if k < 0:
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "NEGATIVE_BOUND_K", "k": k},
        }

    # Validate prefix
    prefix_raw = case.get("prefix")
    if prefix_raw is None or not isinstance(prefix_raw, list):
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "INVALID_PREFIX_TYPE"},
        }
    prefix: List[Tuple[int, int]] = []
    for idx, c in enumerate(prefix_raw):
        ok, reason = validate_comparator(c, n)
        if not ok:
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": f"PREFIX_{reason}", "index": idx},
            }
        prefix.append((c[0], c[1]))

    # Validate forbidden
    forbidden_raw = case.get("forbidden")
    if forbidden_raw is None or not isinstance(forbidden_raw, list):
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "INVALID_FORBIDDEN_TYPE"},
        }
    forbidden: List[Tuple[int, int]] = []
    for idx, c in enumerate(forbidden_raw):
        ok, reason = validate_comparator(c, n)
        if not ok:
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": f"FORBIDDEN_{reason}", "index": idx},
            }
        forbidden.append((c[0], c[1]))

    # Check prefix / forbidden collision
    forbidden_set = set(forbidden)
    for idx, c in enumerate(prefix):
        if c in forbidden_set:
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {
                    "reason": "PREFIX_CONTAINS_FORBIDDEN_COMPARATOR",
                    "comparator": list(c),
                },
            }

    # Infeasible lower bound checks
    if len(prefix) > k:
        return {
            "case_id": case_id,
            "status": "UNKNOWN",
            "code": "BOUND_BELOW_PREFIX_LENGTH",
        }

    info_lb = INFO_THEORETIC_LOWER_BOUND.get(n, math.ceil(math.log2(math.factorial(n))))
    if k < info_lb:
        return {
            "case_id": case_id,
            "status": "UNKNOWN",
            "code": "BOUND_BELOW_INFORMATION_THEORETIC_LOWER_BOUND",
        }

    proven_opt = PROVEN_OPTIMAL_SIZE.get(n)
    if proven_opt is not None and k < proven_opt:
        return {
            "case_id": case_id,
            "status": "UNKNOWN",
            "code": "BOUND_BELOW_PROVEN_OPTIMAL_SIZE",
        }

    # Every sorting network contains every adjacent comparator [i, i+1].
    for c in forbidden:
        if c[1] == c[0] + 1:
            return {
                "case_id": case_id,
                "status": "UNKNOWN",
                "code": "FORBIDDEN_ADJACENT_COMPARATOR",
            }

    # Attempt synthesis
    net = synthesize_sorting_network(n, k, prefix, forbidden)
    if net is not None and len(net) <= k:
        # Final sanity check via 0-1 principle
        valid, _ = verify_01(n, net)
        if valid:
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "network": [[i, j] for i, j in net],
            }

    return {
        "case_id": case_id,
        "status": "UNKNOWN",
        "code": "NO_NETWORK_FOUND_WITHIN_BOUND",
    }
