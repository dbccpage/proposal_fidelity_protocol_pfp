"""
Exact Checker for C057: Sorting Network Synthesis.

Verifies sorting networks using the 0-1 principle via bit-parallel simulation,
prefix adherence, forbidden set avoidance, comparator bounds, and scope classification.

UNKNOWN is accepted only when the case is proven infeasible by one of:

1. ``k`` below the length of the mandatory prefix;
2. ``k`` below the information-theoretic bound ``ceil(log2(n!))``, computed
   exactly with integers;
3. ``k`` below the proven optimal size in ``PROVEN_OPTIMAL_SIZE`` (a trusted
   literature table, see ``PROVEN_OPTIMAL_SIZE_SOURCE``);
4. a forbidden comparator ``[i, i + 1]``: every sorting network contains every
   adjacent comparator, because the input that is sorted except for swapped
   values on channels ``i`` and ``i + 1`` is left unchanged by every other
   comparator.

The presence of a prefix or a forbidden list is not by itself a proof of
infeasibility. The answer's ``code`` must name a proof that holds on the case
(one of ``INFEASIBILITY_CODES``); a generic or wrong code is an unwarranted
refusal, so a constant UNKNOWN cannot pass the infeasible cases.

``classify`` reports the outcome: ACCEPTED (a verified network),
WARRANTED_REFUSAL (UNKNOWN with a proof code that holds, or OUT_OF_SCOPE on an
out-of-scope case), UNWARRANTED_REFUSAL or REJECTED, so constructive solutions
and warranted refusals can be counted apart. ``check`` returns
``(accepted, "<OUTCOME>: <reason>")``.
"""

from typing import Any, Dict, List, Optional, Tuple

INFO_THEORETIC_LOWER_BOUND: Dict[int, int] = {
    4: 5,
    5: 7,
    6: 10,
    7: 13,
    8: 16,
    9: 19,
    10: 22,
    11: 26,
    12: 29,
}

PROVEN_OPTIMAL_SIZE: Dict[int, int] = {
    4: 5,
    5: 9,
    6: 12,
    7: 16,
    8: 19,
    9: 25,
    10: 29,
    11: 35,
    12: 39,
}

PROVEN_OPTIMAL_SIZE_SOURCE = (
    "Trusted literature table, not verified by this checker. "
    "n <= 8: R. W. Floyd and D. E. Knuth, 'The Bose-Nelson sorting problem' (1966; published in "
    "A Survey of Combinatorial Theory, 1973); see D. E. Knuth, The Art of Computer Programming, "
    "Vol. 3, section 5.3.4. "
    "n = 9 and n = 10: M. Codish, L. Cruz-Filipe, M. Frank and P. Schneider-Kamp, 'Sorting nine "
    "inputs requires twenty-five comparisons' (2014; J. Comput. Syst. Sci., 2016). "
    "n = 11 and n = 12: J. Harder, 'An answer to the Bose-Nelson sorting problem for 11 and 12 "
    "channels' (arXiv preprint, 2020)."
)


def information_theoretic_lower_bound(n: int) -> int:
    """Return ceil(log2(n!)) exactly: the least m with 2**m >= n!."""
    factorial = 1
    for value in range(2, n + 1):
        factorial *= value
    return (factorial - 1).bit_length()


def is_valid_case_input(case: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Determine if input case is structurally sound and in scope."""
    if not isinstance(case, dict):
        return False, "CASE_NOT_DICT"
    if not isinstance(case.get("case_id"), str):
        return False, "INVALID_CASE_ID"

    n = case.get("n")
    if isinstance(n, bool) or not isinstance(n, int):
        return False, "INVALID_N_TYPE"
    if n < 4 or n > 12:
        return False, "N_OUT_OF_BOUNDS"

    k = case.get("k")
    if isinstance(k, bool) or not isinstance(k, int):
        return False, "INVALID_K_TYPE"
    if k < 0:
        return False, "NEGATIVE_BOUND_K"

    prefix = case.get("prefix")
    if prefix is None or not isinstance(prefix, list):
        return False, "INVALID_PREFIX_TYPE"
    for c in prefix:
        if not isinstance(c, (list, tuple)) or len(c) != 2:
            return False, "PREFIX_COMPARATOR_INVALID"
        i, j = c
        if isinstance(i, bool) or isinstance(j, bool):
            return False, "PREFIX_COMPARATOR_CHANNEL_IS_BOOLEAN"
        if not isinstance(i, int) or not isinstance(j, int):
            return False, "PREFIX_COMPARATOR_NOT_INT"
        if i < 0 or j < 0 or i >= n or j >= n or i >= j:
            return False, "PREFIX_COMPARATOR_INVALID_BOUNDS"

    forbidden = case.get("forbidden")
    if forbidden is None or not isinstance(forbidden, list):
        return False, "INVALID_FORBIDDEN_TYPE"
    for c in forbidden:
        if not isinstance(c, (list, tuple)) or len(c) != 2:
            return False, "FORBIDDEN_COMPARATOR_INVALID"
        i, j = c
        if isinstance(i, bool) or isinstance(j, bool):
            return False, "FORBIDDEN_COMPARATOR_CHANNEL_IS_BOOLEAN"
        if not isinstance(i, int) or not isinstance(j, int):
            return False, "FORBIDDEN_COMPARATOR_NOT_INT"
        if i < 0 or j < 0 or i >= n or j >= n or i >= j:
            return False, "FORBIDDEN_COMPARATOR_INVALID_BOUNDS"

    forbidden_set = set(tuple(c) for c in forbidden)
    for c in prefix:
        if tuple(c) in forbidden_set:
            return False, "PREFIX_CONTAINS_FORBIDDEN_COMPARATOR"

    return True, None


INFEASIBILITY_CODES = (
    "BOUND_BELOW_PREFIX_LENGTH",
    "BOUND_BELOW_INFORMATION_THEORETIC_LOWER_BOUND",
    "BOUND_BELOW_PROVEN_OPTIMAL_SIZE",
    "FORBIDDEN_ADJACENT_COMPARATOR",
)
REFUSAL_STATUSES = ("UNKNOWN", "OUT_OF_SCOPE")


def admissible_infeasibility_codes(case: Dict[str, Any]) -> frozenset:
    """Proof codes whose condition holds on this valid case (empty: no proof available)."""
    n = case["n"]
    k = case["k"]
    codes = set()
    if len(case["prefix"]) > k:
        codes.add("BOUND_BELOW_PREFIX_LENGTH")
    if k < information_theoretic_lower_bound(n):
        codes.add("BOUND_BELOW_INFORMATION_THEORETIC_LOWER_BOUND")
    proven_opt = PROVEN_OPTIMAL_SIZE.get(n)
    if proven_opt is not None and k < proven_opt:
        codes.add("BOUND_BELOW_PROVEN_OPTIMAL_SIZE")
    if any(c[1] == c[0] + 1 for c in case["forbidden"]):
        codes.add("FORBIDDEN_ADJACENT_COMPARATOR")
    return frozenset(codes)


def is_infeasible_case(case: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Determine if a valid case is provably infeasible (first proof code in enum order)."""
    codes = admissible_infeasibility_codes(case)
    for code in INFEASIBILITY_CODES:
        if code in codes:
            return True, code
    return False, None


def verify_01_bitparallel(n: int, network: List[Tuple[int, int]]) -> Tuple[bool, Optional[int]]:
    """Run bit-parallel 0-1 principle verification over all 2^n inputs."""
    num_cases = 1 << n
    mask = (1 << num_cases) - 1
    w = [0] * n
    for c in range(n):
        val = 0
        for m in range(num_cases):
            if (m >> c) & 1:
                val |= 1 << m
        w[c] = val

    for i, j in network:
        wi, wj = w[i], w[j]
        w[i] = wi & wj
        w[j] = wi | wj

    for c in range(n - 1):
        unsorted = (w[c] & ~w[c + 1]) & mask
        if unsorted:
            failing_m = (unsorted & -unsorted).bit_length() - 1
            return False, failing_m

    return True, None


def classify(case: Dict[str, Any], solution: Any) -> Dict[str, Any]:
    """Outcome record: accepted, outcome (ACCEPTED, WARRANTED_REFUSAL, UNWARRANTED_REFUSAL, REJECTED), reason."""
    accepted, reason = _verdict(case, solution)
    status = solution.get("status") if isinstance(solution, dict) else None
    if status in REFUSAL_STATUSES:
        outcome = "WARRANTED_REFUSAL" if accepted else "UNWARRANTED_REFUSAL"
    else:
        outcome = "ACCEPTED" if accepted else "REJECTED"
    return {"accepted": accepted, "outcome": outcome, "reason": reason}


def check(case: Dict[str, Any], solution: Any) -> Tuple[bool, str]:
    """Exact check. Returns (accepted, "<OUTCOME>: <reason>")."""
    result = classify(case, solution)
    return result["accepted"], f"{result['outcome']}: {result['reason']}"


def _verdict(case: Dict[str, Any], solution: Any) -> Tuple[bool, str]:
    if not isinstance(solution, dict):
        return False, "SOLUTION_NOT_A_DICT"

    if solution.get("case_id") != case.get("case_id"):
        return False, "CASE_ID_MISMATCH"

    status = solution.get("status")
    if status not in {"SOLVED", "OUT_OF_SCOPE", "UNKNOWN"}:
        return False, f"INVALID_STATUS: {status}"

    case_valid, case_err = is_valid_case_input(case)

    # 1. OUT_OF_SCOPE check
    if status == "OUT_OF_SCOPE":
        if case_valid:
            return False, "FALSE_OUT_OF_SCOPE: case is valid and in scope"
        return True, "VALID_OUT_OF_SCOPE_DECISION"

    # If case was not valid, status must be OUT_OF_SCOPE
    if not case_valid:
        return False, f"FALSE_{status}_ON_INVALID_CASE: expected OUT_OF_SCOPE ({case_err})"

    # 2. UNKNOWN check: the code must name a proof that holds on this case
    admissible = admissible_infeasibility_codes(case)
    is_infeas, infeas_reason = is_infeasible_case(case)
    if status == "UNKNOWN":
        code = solution.get("code")
        if not admissible:
            return False, "UNKNOWN_WITHOUT_PROVEN_INFEASIBILITY"
        if type(code) is not str or code not in INFEASIBILITY_CODES:
            return False, f"UNKNOWN_CODE_NOT_A_PROOF_CODE: {code!r}"
        if code not in admissible:
            return False, f"UNKNOWN_CODE_DOES_NOT_HOLD: {code} (holding: {sorted(admissible)})"
        return True, f"PROVEN_INFEASIBLE: {code}"

    # 3. SOLVED check
    if status == "SOLVED":
        if is_infeas:
            return False, f"SOLVED_CLAIMED_ON_INFEASIBLE_CASE: {infeas_reason}"

        network_raw = solution.get("network")
        if not isinstance(network_raw, list):
            return False, "NETWORK_NOT_A_LIST"

        n = case["n"]
        k = case["k"]
        prefix = [tuple(c) for c in case["prefix"]]
        forbidden_set = set(tuple(c) for c in case["forbidden"])

        if len(network_raw) > k:
            return False, f"NETWORK_SIZE_EXCEEDS_BOUND: {len(network_raw)} > {k}"

        if len(network_raw) < len(prefix):
            return False, f"NETWORK_SHORTER_THAN_PREFIX: {len(network_raw)} < {len(prefix)}"

        network: List[Tuple[int, int]] = []
        for idx, c in enumerate(network_raw):
            if not isinstance(c, (list, tuple)) or len(c) != 2:
                return False, f"COMPARATOR_AT_INDEX_{idx}_INVALID_STRUCTURE"
            i, j = c
            if isinstance(i, bool) or isinstance(j, bool):
                return False, f"COMPARATOR_AT_INDEX_{idx}_CONTAINS_BOOLEAN"
            if not isinstance(i, int) or not isinstance(j, int):
                return False, f"COMPARATOR_AT_INDEX_{idx}_NON_INTEGER"
            if i < 0 or j < 0 or i >= n or j >= n:
                return False, f"COMPARATOR_AT_INDEX_{idx}_CHANNEL_OUT_OF_BOUNDS: [{i}, {j}]"
            if i == j:
                return False, f"COMPARATOR_AT_INDEX_{idx}_SELF_LOOP: [{i}, {j}]"
            if i > j:
                return False, f"COMPARATOR_AT_INDEX_{idx}_NOT_ORDERED: [{i}, {j}]"

            pair = (i, j)
            if pair in forbidden_set:
                return False, f"NETWORK_CONTAINS_FORBIDDEN_COMPARATOR: {pair} at index {idx}"

            network.append(pair)

        # Verify prefix matches
        for idx, p in enumerate(prefix):
            if network[idx] != p:
                return False, f"PREFIX_MISMATCH_AT_INDEX_{idx}: expected {p}, got {network[idx]}"

        # Verify 0-1 principle
        sorted_all, failing_vec = verify_01_bitparallel(n, network)
        if not sorted_all:
            # Reconstruct binary string of failing vector
            bits = [(failing_vec >> c) & 1 for c in range(n)]
            return False, f"0_1_PRINCIPLE_FAILED: unsorted on input {bits}"

        return True, "CERTIFICATE_VERIFIED_VALID"

    return False, f"UNHANDLED_STATUS: {status}"
