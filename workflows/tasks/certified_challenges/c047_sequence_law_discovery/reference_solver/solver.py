"""Reference frozen solver for C047: Recurrence and Generating-Function Discovery.
Pure standard library implementation with DDC operational trace.
"""

from fractions import Fraction
from typing import Any, Dict

from .holonomic_guesser import certify_none_within_bounds, guess_holonomic


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """Solve a C047 sequence law discovery case."""
    case_id = case.get("case_id", "seq_unknown")
    raw_terms = case.get("terms", [])
    r_max = int(case.get("r_max", 8))
    d_max = int(case.get("d_max", 3))

    trace = ["C", "I"]

    # Check for invalid / non-integer terms
    terms = []
    for idx, t_str in enumerate(raw_terms):
        try:
            val = int(t_str)
            terms.append(Fraction(val))
        except (ValueError, TypeError):
            trace.append("M")
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "NON_INTEGER_TERM", "index": idx, "raw_value": str(t_str)},
                "trace": trace,
            }

    trace.append("R")

    # Try finding holonomic recurrence
    rec_res = guess_holonomic(terms, r_max, d_max)
    if rec_res is not None:
        trace.extend(["D", "E", "T"])
        return {
            "case_id": case_id,
            "status": "SOLVED",
            "kind": "RECURRENCE",
            "start": rec_res["start"],
            "polys": rec_res["polys"],
            "trace": trace,
        }

    trace.append("D")

    # Try certifying absence via nonsingular minor
    none_res = certify_none_within_bounds(terms, r_max, d_max, max_start=5)
    if none_res is not None:
        trace.extend(["E", "T"])
        return {
            "case_id": case_id,
            "status": "SOLVED",
            "kind": "NONE_WITHIN_BOUNDS",
            "order": none_res["order"],
            "degree": none_res["degree"],
            "start_range": none_res["start_range"],
            "minor_rows": none_res["minor_rows"],
            "trace": trace,
        }

    trace.append("T")
    return {"case_id": case_id, "status": "UNKNOWN", "code": "SEARCH_LIMIT", "trace": trace}
