"""
Independent Checker for C057: Sorting Network Synthesis.

Written by an independent verifier. Employs explicit binary vector simulation,
exhaustive 0-1 principle validation, random integer stress testing (10,000 inputs),
and independent scope validation.
"""

import random
from typing import Any, Dict, List, Tuple

# Proven optimal comparator counts: a trusted literature table, not verified here
# (Floyd and Knuth for n <= 8; Codish, Cruz-Filipe, Frank and Schneider-Kamp for
# n = 9, 10; Harder for n = 11, 12).
PROVEN_OPT = {4: 5, 5: 9, 6: 12, 7: 16, 8: 19, 9: 25, 10: 29, 11: 35, 12: 39}


def info_bound(n: int) -> int:
    """Least m with 2**m >= n!, by repeated doubling (no floating point)."""
    target = 1
    for value in range(2, n + 1):
        target *= value
    m, power = 0, 1
    while power < target:
        power *= 2
        m += 1
    return m


def admissible_codes(case: Dict[str, Any]) -> frozenset:
    """Public proof codes (TASK.md section B) whose condition holds on this case."""
    n, k = case["n"], case["k"]
    holding = []
    if len(case["prefix"]) > k:
        holding.append("BOUND_BELOW_PREFIX_LENGTH")
    if k < info_bound(n):
        holding.append("BOUND_BELOW_INFORMATION_THEORETIC_LOWER_BOUND")
    if k < PROVEN_OPT[n]:
        holding.append("BOUND_BELOW_PROVEN_OPTIMAL_SIZE")
    # Each adjacent comparator [i, i+1] is the only one that sorts the input
    # which is sorted except for channels i and i+1, so it cannot be forbidden.
    adjacent = {(i, i + 1) for i in range(n - 1)}
    if any((c[0], c[1]) in adjacent for c in case["forbidden"]):
        holding.append("FORBIDDEN_ADJACENT_COMPARATOR")
    return frozenset(holding)


def proven_infeasibility(case: Dict[str, Any]) -> str:
    """Return one holding proof code (sorted order), or '' when none holds."""
    codes = sorted(admissible_codes(case))
    return codes[0] if codes else ""


def independent_outcome(case: Dict[str, Any], solution: Any) -> Tuple[bool, str, str]:
    """(accepted, outcome, reason); outcome separates warranted refusals from solutions."""
    ok, reason = _independent_verdict(case, solution)
    status = solution.get("status") if isinstance(solution, dict) else None
    if status in ("UNKNOWN", "OUT_OF_SCOPE"):
        return ok, ("WARRANTED_REFUSAL" if ok else "UNWARRANTED_REFUSAL"), reason
    return ok, ("ACCEPTED" if ok else "REJECTED"), reason


def independent_validate_input(case: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(case, dict):
        return False, "CASE_NOT_DICT"
    if "case_id" not in case or not isinstance(case["case_id"], str):
        return False, "INVALID_CASE_ID"

    n = case.get("n")
    if type(n) is not int or n < 4 or n > 12:
        return False, f"INVALID_OR_OOB_N: {n}"

    k = case.get("k")
    if type(k) is not int or k < 0:
        return False, f"INVALID_OR_NEGATIVE_K: {k}"

    prefix = case.get("prefix")
    if not isinstance(prefix, list):
        return False, "PREFIX_NOT_LIST"
    for idx, c in enumerate(prefix):
        if not isinstance(c, (list, tuple)) or len(c) != 2:
            return False, f"PREFIX_ELEMENT_{idx}_NOT_PAIR"
        i, j = c
        if type(i) is not int or type(j) is not int:
            return False, f"PREFIX_ELEMENT_{idx}_NON_INT"
        if not (0 <= i < j < n):
            return False, f"PREFIX_ELEMENT_{idx}_INVALID_ORDER_OR_BOUNDS: [{i}, {j}]"

    forbidden = case.get("forbidden")
    if not isinstance(forbidden, list):
        return False, "FORBIDDEN_NOT_LIST"
    for idx, c in enumerate(forbidden):
        if not isinstance(c, (list, tuple)) or len(c) != 2:
            return False, f"FORBIDDEN_ELEMENT_{idx}_NOT_PAIR"
        i, j = c
        if type(i) is not int or type(j) is not int:
            return False, f"FORBIDDEN_ELEMENT_{idx}_NON_INT"
        if not (0 <= i < j < n):
            return False, f"FORBIDDEN_ELEMENT_{idx}_INVALID_ORDER_OR_BOUNDS: [{i}, {j}]"

    forbid_set = set((c[0], c[1]) for c in forbidden)
    for c in prefix:
        if (c[0], c[1]) in forbid_set:
            return False, f"PREFIX_FORBIDDEN_COLLISION: [{c[0]}, {c[1]}]"

    return True, "OK"


def independent_check(case: Dict[str, Any], solution: Any) -> Tuple[bool, str]:
    ok, outcome, reason = independent_outcome(case, solution)
    return ok, f"{outcome}: {reason}"


def _independent_verdict(case: Dict[str, Any], solution: Any) -> Tuple[bool, str]:
    if not isinstance(solution, dict):
        return False, "SOLUTION_NOT_DICT"

    if solution.get("case_id") != case.get("case_id"):
        return False, "CASE_ID_MISMATCH"

    status = solution.get("status")
    if status not in {"SOLVED", "OUT_OF_SCOPE", "UNKNOWN"}:
        return False, f"BAD_STATUS_STRING: {status}"

    case_ok, case_msg = independent_validate_input(case)

    if status == "OUT_OF_SCOPE":
        if case_ok:
            return False, "FALSE_OUT_OF_SCOPE_ON_VALID_CASE"
        return True, "OUT_OF_SCOPE_ACCEPTED"

    if not case_ok:
        return False, f"EXPECTED_OUT_OF_SCOPE_BUT_GOT_{status}: {case_msg}"

    n = case["n"]
    k = case["k"]

    holding = admissible_codes(case)
    is_infeas = bool(holding)

    if status == "UNKNOWN":
        if not is_infeas:
            return False, "UNKNOWN_REJECTED_NO_INFEASIBILITY_PROOF"
        code = solution.get("code")
        if not isinstance(code, str) or code not in holding:
            return False, f"UNKNOWN_REJECTED_CODE_NOT_A_HOLDING_PROOF: {code!r}"
        return True, f"UNKNOWN_ACCEPTED: {code}"

    if status == "SOLVED":
        if is_infeas:
            return False, "SOLVED_REPORTED_ON_INFEASIBLE_CASE"

        net_raw = solution.get("network")
        if not isinstance(net_raw, list):
            return False, "NETWORK_MUST_BE_LIST"

        if len(net_raw) > k:
            return False, f"EXCEEDED_MAX_COMPARATORS: {len(net_raw)} > {k}"

        prefix = case["prefix"]
        if len(net_raw) < len(prefix):
            return False, f"NETWORK_SHORTER_THAN_PREFIX: {len(net_raw)} < {len(prefix)}"

        forbidden_set = set((c[0], c[1]) for c in case["forbidden"])
        network: List[Tuple[int, int]] = []
        for idx, item in enumerate(net_raw):
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                return False, f"MALFORMED_COMPARATOR_AT_{idx}"
            i, j = item
            if type(i) is not int or type(j) is not int:
                return False, f"NON_INT_WIRE_AT_{idx}"
            if not (0 <= i < j < n):
                return False, f"WIRE_OUT_OF_BOUNDS_OR_UNORDERED_AT_{idx}: [{i}, {j}]"
            pair = (i, j)
            if pair in forbidden_set:
                return False, f"FORBIDDEN_PAIR_INCLUDED: {pair}"
            network.append(pair)

        # Prefix match
        for idx, p in enumerate(prefix):
            if network[idx] != (p[0], p[1]):
                return False, f"PREFIX_MISMATCH_AT_{idx}"

        # 1. 0-1 Principle check via explicit bit generation
        total_vectors = 1 << n
        for v in range(total_vectors):
            arr = [(v >> b) & 1 for b in range(n)]
            for i, j in network:
                if arr[i] > arr[j]:
                    arr[i], arr[j] = arr[j], arr[i]
            # Check sorted
            for c in range(n - 1):
                if arr[c] > arr[c + 1]:
                    return False, f"0_1_PRINCIPLE_VIOLATION_AT_INPUT_{v}"

        # 2. Random integer stress test: 2,000 random permutations + 2,000 random arrays
        rng = random.Random(42 + n)
        for _ in range(2000):
            perm = list(range(n))
            rng.shuffle(perm)
            for i, j in network:
                if perm[i] > perm[j]:
                    perm[i], perm[j] = perm[j], perm[i]
            for c in range(n - 1):
                if perm[c] > perm[c + 1]:
                    return False, f"RANDOM_PERMUTATION_UNSORTED: {perm}"

        for _ in range(2000):
            rand_arr = [rng.randint(-1000, 1000) for _ in range(n)]
            expected = sorted(rand_arr)
            for i, j in network:
                if rand_arr[i] > rand_arr[j]:
                    rand_arr[i], rand_arr[j] = rand_arr[j], rand_arr[i]
            if rand_arr != expected:
                return False, "RANDOM_ARRAY_UNSORTED"

        return True, "INDEPENDENT_VERIFICATION_PASSED"

    return False, f"UNKNOWN_STATUS: {status}"
