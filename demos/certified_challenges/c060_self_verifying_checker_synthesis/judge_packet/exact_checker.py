"""Exact checker for Challenge C060: Checker Synthesis Scored by Mutation Kill Rate.

Evaluates a synthesized checker's verdict against the exact mathematical ground truth.
Scores both self-tolerance (zero autoimmunity) and corruption kill rate.
"""

from typing import Any, Callable, Dict, Tuple, Union

REJECTION_CODES = frozenset(
    {
        "SCHEMA",
        "NONCANONICAL_RATIONAL",
        "DIMENSION",
        "NONPOSITIVE_WEIGHT",
        "RESIDUAL_MISMATCH",
        "PRIMAL_VALUE_MISMATCH",
        "DUAL_NOT_IN_COKERNEL",
        "DUAL_BOUND_VIOLATED",
        "DUAL_VALUE_MISMATCH",
    }
)


def verify_candidate(
    case_item: Dict[str, Any],
    candidate_or_result: Union[Dict[str, Any], Callable[[Any, Any], Dict[str, Any]]],
) -> Tuple[bool, str]:
    """Verifies a candidate checker's output on a single test case.

    Args:
        case_item: Dictionary containing 'case', 'cert', 'expected_verdict', and optional 'expected_code'.
        candidate_or_result: Either the dictionary output from the candidate checker or a callable check(case, cert).

    Returns:
        (is_verified, reason_string)
    """
    if not isinstance(case_item, dict):
        return False, "INVALID_TEST_CASE_FORMAT"

    c_case = case_item.get("case")
    c_cert = case_item.get("cert")
    expected_verdict = case_item.get("expected_verdict")

    if expected_verdict not in {"ACCEPT", "REJECT"}:
        return False, "INVALID_OR_MISSING_EXPECTED_VERDICT"

    # Obtain candidate response
    if callable(candidate_or_result):
        try:
            res = candidate_or_result(c_case, c_cert)
        except Exception as e:
            return False, f"CHECKER_CRASHED_EXCEPTION: {type(e).__name__}: {str(e)}"
    elif isinstance(candidate_or_result, dict):
        res = candidate_or_result
    else:
        return False, "CANDIDATE_OUTPUT_NOT_A_DICT"

    if not isinstance(res, dict):
        return False, f"CANDIDATE_RESPONSE_NOT_DICT: got {type(res).__name__}"

    cand_verdict = res.get("verdict")
    if cand_verdict not in {"ACCEPT", "REJECT"}:
        return False, f"INVALID_VERDICT_STRING: got {cand_verdict}"

    # Verify closed rejection code formatting if rejected
    if cand_verdict == "REJECT":
        code = res.get("code")
        if code is not None and code not in REJECTION_CODES:
            return False, f"REJECTION_CODE_NOT_IN_CLOSED_LIST: {code}"

    # Verdict Comparison
    if expected_verdict == "ACCEPT":
        if cand_verdict != "ACCEPT":
            return (
                False,
                f"AUTOIMMUNITY_FALSE_REJECTION: expected ACCEPT, candidate emitted REJECT ({res.get('code')})",
            )
        return True, "SELF_CERTIFICATE_ACCEPTED"
    else:  # expected_verdict == "REJECT"
        if cand_verdict != "REJECT":
            return (
                False,
                "CORRUPTION_ESCAPE_FALSE_ACCEPTANCE: expected REJECT, candidate emitted ACCEPT",
            )
        expected_code = case_item.get("expected_code")
        if expected_code and res.get("code") != expected_code:
            return False, f"WRONG_REJECTION_CODE: expected {expected_code}, got {res.get('code')}"
        return True, "CORRUPTION_KILLED_ACCEPTED"
