import os
import sys

try:
    from .simplex import solve_lp_exact
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from simplex import solve_lp_exact


def solve(case: dict) -> dict:
    if not isinstance(case, dict):
        return {
            "status": "OUT_OF_SCOPE",
            "witness": {"field": "case", "reason": "Expected JSON object dictionary"},
        }
    cid = case.get("case_id", "unknown")
    A, b, c = case.get("A"), case.get("b"), case.get("c")
    if A is None or b is None or c is None:
        return {
            "case_id": cid,
            "status": "OUT_OF_SCOPE",
            "witness": {"field": "keys", "reason": "Missing required field A, b, or c"},
        }
    res = solve_lp_exact(A, b, c)
    res["case_id"] = cid
    return res
