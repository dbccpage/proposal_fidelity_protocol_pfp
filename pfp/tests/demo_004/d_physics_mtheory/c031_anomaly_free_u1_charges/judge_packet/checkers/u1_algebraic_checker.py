"""Checker 1 (Exact Algebraic & Chirality Certifier) for C031.

Validates exact arbitrary-precision integer arithmetic, primitivity, chirality,
canonical form, set equality for enumerations, and multiset extension for completions,
backed by an independent refuter for NO_COMPLETION claims.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping
from typing import Any

from omega_engine_pfp.tests.demo_004.d_physics_mtheory.c031_anomaly_free_u1_charges.reference_solver.diophantine_u1 import (
    canonical_representative,
    complete_chiral_u1,
    enumerate_chiral_u1,
    is_chiral,
    is_primitive,
)

CLOSED_REFUSAL_CODES = frozenset(
    {
        "MALFORMED_CASE_STRUCTURE",
        "MALFORMED_QUERY_TYPE",
        "N_OUT_OF_BOUNDS",
        "BOUND_OUT_OF_BOUNDS",
        "SEARCH_NOT_FINISHED",
        "INVALID_CHARGE_SPECTRUM",
        "VECTOR_LIKE_TRIVIAL",
        "NON_PRIMITIVE_SPECTRUM",
        "BOUND_EXCEEDED",
        "NO_COMPLETION",
    }
)

VALID_OOS_KINDS = frozenset(
    {
        "fixed_charge_exceeds_bound",
        "fixed_charge_zero",
        "too_many_fixed_charges",
    }
)

ENUMERATE_MAX_N = 10
ENUMERATE_MAX_BOUND = 12

ALLOWED_ENUM_KEYS = frozenset({"id", "status", "count", "solutions"})
ALLOWED_COMP_KEYS = frozenset({"id", "status", "completion"})
ALLOWED_NOCOMP_KEYS = frozenset({"id", "status", "completion", "claim"})
ALLOWED_OOS_KEYS = frozenset({"id", "status", "witness"})
ALLOWED_UNKNOWN_KEYS = frozenset({"id", "status", "refusal_code", "refusal"})
ALLOWED_WITNESS_KEYS = frozenset({"kind", "index", "charge", "bound", "count", "n"})


def _is_canonical_int_str(s: Any) -> bool:
    """Verifies canonical integer representation without leading zeros, decimals, or plus sign."""
    if not isinstance(s, str):
        return False
    if any(c.isspace() for c in s) or "." in s or "e" in s.lower() or "_" in s:
        return False
    if s == "-0" or s.startswith("+"):
        return False
    try:
        val = int(s)
        return str(val) == s
    except Exception:
        return False


def _verify_refusal_warranted(case: Mapping[str, Any], refusal: str) -> tuple[bool, str]:
    """Validates that a claimed UNKNOWN refusal code is genuinely warranted by case properties."""
    if refusal not in CLOSED_REFUSAL_CODES:
        return False, f"FAIL: unrecognized refusal code {refusal!r}"

    q = case.get("query")
    n = case.get("n")
    b = case.get("bound")
    fixed = case.get("fixed")
    case_id = case.get("id")

    if refusal == "N_OUT_OF_BOUNDS":
        if q == "enumerate" and type(n) is int and not isinstance(n, bool) and 1 <= n <= 10:
            return False, f"FAIL: refused N_OUT_OF_BOUNDS on valid enumerate n={n}"
        if q == "complete" and type(n) is int and not isinstance(n, bool) and 1 <= n <= 12:
            return False, f"FAIL: refused N_OUT_OF_BOUNDS on valid complete n={n}"
        if type(n) is int and not isinstance(n, bool) and 1 <= n <= 10:
            return False, f"FAIL: refused N_OUT_OF_BOUNDS on valid n={n}"
        return True, f"VALID_REFUSAL_{refusal}"

    if refusal == "BOUND_OUT_OF_BOUNDS":
        if q == "enumerate" and type(b) is int and not isinstance(b, bool) and 1 <= b <= 12:
            return False, f"FAIL: refused BOUND_OUT_OF_BOUNDS on valid enumerate bound={b}"
        if q == "complete" and type(b) is int and not isinstance(b, bool) and 1 <= b <= 2_000_000:
            return False, f"FAIL: refused BOUND_OUT_OF_BOUNDS on valid complete bound={b}"
        if type(b) is int and not isinstance(b, bool) and 1 <= b <= 12:
            return False, f"FAIL: refused BOUND_OUT_OF_BOUNDS on valid bound={b}"
        return True, f"VALID_REFUSAL_{refusal}"

    if refusal == "MALFORMED_QUERY_TYPE":
        if q in {"enumerate", "complete"}:
            return False, f"FAIL: refused MALFORMED_QUERY_TYPE on valid query={q!r}"
        return True, f"VALID_REFUSAL_{refusal}"

    if refusal == "MALFORMED_CASE_STRUCTURE":
        if not isinstance(case_id, str) or not case_id:
            return True, f"VALID_REFUSAL_{refusal}"
        if q not in {"enumerate", "complete"}:
            return True, f"VALID_REFUSAL_{refusal}"
        if type(n) is not int or isinstance(n, bool) or n <= 0:
            return True, f"VALID_REFUSAL_{refusal}"
        if type(b) is not int or isinstance(b, bool) or b <= 0:
            return True, f"VALID_REFUSAL_{refusal}"
        if q == "complete":
            if not isinstance(fixed, list) or len(fixed) == 0 or len(fixed) >= n:
                return True, f"VALID_REFUSAL_{refusal}"
            if not all(type(x) is int and not isinstance(x, bool) and x != 0 for x in fixed):
                return True, f"VALID_REFUSAL_{refusal}"
        return False, f"FAIL: refused MALFORMED_CASE_STRUCTURE on well-formed case {case_id}"

    if refusal == "BOUND_EXCEEDED":
        if isinstance(fixed, list) and type(b) is int and not isinstance(b, bool):
            if any(type(x) is int and not isinstance(x, bool) and abs(x) > b for x in fixed):
                return True, f"VALID_REFUSAL_{refusal}"
        return (
            False,
            f"FAIL: refused BOUND_EXCEEDED but all input fixed charges are within bound {b}",
        )

    if refusal == "NO_COMPLETION":
        return (
            False,
            "FAIL: NO_COMPLETION must be returned as status SOLVED with completion null, not UNKNOWN",
        )

    if refusal == "SEARCH_NOT_FINISHED":
        return False, f"FAIL: refused SEARCH_NOT_FINISHED on solvable judge case (bound={b})"

    if refusal == "INVALID_CHARGE_SPECTRUM":
        if isinstance(fixed, list):
            if any(type(x) is not int or isinstance(x, bool) or x == 0 for x in fixed):
                return True, f"VALID_REFUSAL_{refusal}"
        return False, "FAIL: refused INVALID_CHARGE_SPECTRUM on valid input charges"

    if refusal == "VECTOR_LIKE_TRIVIAL":
        if (
            isinstance(fixed, list)
            and type(n) is int
            and not isinstance(n, bool)
            and len(fixed) == n
            and n > 0
        ):
            if Counter(fixed) == Counter(-x for x in fixed):
                return True, f"VALID_REFUSAL_{refusal}"
        return False, f"FAIL: unwarranted refusal {refusal!r} on valid solvable case"

    if refusal == "NON_PRIMITIVE_SPECTRUM":
        if (
            isinstance(fixed, list)
            and type(n) is int
            and not isinstance(n, bool)
            and len(fixed) == n
            and n > 0
        ):
            if all(type(x) is int and not isinstance(x, bool) and x != 0 for x in fixed):
                if math.gcd(*[abs(x) for x in fixed]) > 1:
                    return True, f"VALID_REFUSAL_{refusal}"
        return False, f"FAIL: unwarranted refusal {refusal!r} on valid solvable case"

    return False, f"FAIL: unwarranted refusal {refusal!r} on valid solvable case"


def _verify_out_of_scope_warranted(case: Mapping[str, Any], witness: Any) -> tuple[bool, str]:
    """Audits OUT_OF_SCOPE witness against case parameters."""
    if not isinstance(witness, Mapping):
        return False, "FAIL: OUT_OF_SCOPE witness must be a mapping"

    extra_w = set(witness.keys()) - ALLOWED_WITNESS_KEYS
    if extra_w:
        return False, f"FAIL: illegal phantom keys in witness: {sorted(extra_w)}"

    kind = witness.get("kind")
    if kind not in VALID_OOS_KINDS:
        return False, f"FAIL: unrecognized out-of-scope kind {kind!r}"

    fixed = case.get("fixed", [])
    bound = case.get("bound", 0)
    n = case.get("n", 0)

    if kind == "fixed_charge_exceeds_bound":
        if not any(isinstance(x, int) and abs(x) > bound for x in fixed):
            return (
                False,
                "FAIL: witness claimed fixed_charge_exceeds_bound but all fixed charges are within bound",
            )
        return True, "VALID_OUT_OF_SCOPE"

    if kind == "fixed_charge_zero":
        if not any(x == 0 for x in fixed):
            return False, "FAIL: witness claimed fixed_charge_zero but no fixed charge is zero"
        return True, "VALID_OUT_OF_SCOPE"

    if kind == "too_many_fixed_charges":
        if len(fixed) < n:
            return (
                False,
                f"FAIL: witness claimed too_many_fixed_charges but len(fixed)={len(fixed)} < n={n}",
            )
        return True, "VALID_OUT_OF_SCOPE"

    return False, f"FAIL: unverified out-of-scope witness {kind!r}"


def verify_chiral_u1_certificate(
    case: Any,
    result: Any,
    ground_truth: Any = None,
) -> tuple[bool, str]:
    """Exact algebraic and chirality certifier for C031 (Checker 1).

    Total parsing contract: never raises unhandled exceptions.
    Returns (True, "PASS: ...") or (False, "FAIL: ...").
    """
    try:
        if not isinstance(case, Mapping):
            return False, "FAIL: case must be a mapping"
        if not isinstance(result, Mapping):
            return False, "FAIL: result must be a mapping"

        status = result.get("status")
        if status not in {"SOLVED", "OUT_OF_SCOPE", "UNKNOWN"}:
            return False, f"FAIL: invalid status {status!r}"

        # Status: UNKNOWN
        if status == "UNKNOWN":
            extra = set(result.keys()) - ALLOWED_UNKNOWN_KEYS
            if extra:
                return False, f"FAIL: illegal extra/phantom keys in UNKNOWN result: {sorted(extra)}"
            refusal = str(result.get("refusal_code") or result.get("refusal") or "")
            if not refusal:
                return False, "FAIL: UNKNOWN status missing refusal_code"
            return _verify_refusal_warranted(case, refusal)

        # Status: OUT_OF_SCOPE
        if status == "OUT_OF_SCOPE":
            extra = set(result.keys()) - ALLOWED_OOS_KEYS
            if extra:
                return (
                    False,
                    f"FAIL: illegal extra/phantom keys in OUT_OF_SCOPE result: {sorted(extra)}",
                )
            if "witness" not in result:
                return False, "FAIL: OUT_OF_SCOPE status missing witness"
            return _verify_out_of_scope_warranted(case, result["witness"])

        # Status: SOLVED
        query = case.get("query")
        n = case.get("n")
        bound = case.get("bound")
        if type(n) is not int or type(bound) is not int:
            return False, "FAIL: case n and bound must be integers"

        if query == "enumerate":
            extra = set(result.keys()) - ALLOWED_ENUM_KEYS
            if extra:
                return (
                    False,
                    f"FAIL: illegal extra/phantom keys in enumerate result: {sorted(extra)}",
                )

            count = result.get("count")
            solutions = result.get("solutions")

            if type(count) is not int or count < 0:
                return False, f"FAIL: count must be a non-negative integer, got {count!r}"
            if not isinstance(solutions, list):
                return False, f"FAIL: solutions must be a list, got {type(solutions).__name__}"
            if count != len(solutions):
                return (
                    False,
                    f"FAIL: count mismatch: declared {count} != len(solutions) {len(solutions)}",
                )

            seen_canonical: set[tuple[int, ...]] = set()
            prev_sol: list[int] | None = None

            for idx, sol in enumerate(solutions):
                if not isinstance(sol, list):
                    return False, f"FAIL: solution {idx} must be a list of integers"
                if len(sol) != n:
                    return False, f"FAIL: solution {idx} length {len(sol)} != n={n}"

                # Strict integer check (zero float tolerance)
                for q in sol:
                    if type(q) is not int or isinstance(q, bool):
                        return False, f"FAIL: solution {idx} contains non-integer charge {q!r}"
                    if q == 0:
                        return False, f"FAIL: solution {idx} contains zero charge"
                    if abs(q) > bound:
                        return (
                            False,
                            f"FAIL: solution {idx} contains charge {q} exceeding bound {bound}",
                        )

                # Inner sorting check: charges within solution must be ascending
                if sol != sorted(sol):
                    return False, f"FAIL: solution {idx} charges are not sorted ascending: {sol}"

                # Linear anomaly: sum(q) == 0
                if sum(sol) != 0:
                    return False, f"FAIL: solution {idx} linear sum != 0: sum={sum(sol)}"

                # Cubic anomaly: sum(q^3) == 0
                if sum(x * x * x for x in sol) != 0:
                    return (
                        False,
                        f"FAIL: solution {idx} cubic sum != 0: sum3={sum(x * x * x for x in sol)}",
                    )

                # Primitivity: gcd == 1
                if not is_primitive(sol):
                    return False, f"FAIL: solution {idx} is non-primitive (gcd > 1): {sol}"

                # Chirality: Counter(q) != Counter(-q)
                if not is_chiral(sol):
                    return (
                        False,
                        f"FAIL: solution {idx} is vector-like (Counter(q) == Counter(-q)): {sol}",
                    )

                # Canonical form: min(sort(q), sort(-q))
                canon = canonical_representative(sol)
                if sol != canon:
                    return (
                        False,
                        f"FAIL: solution {idx} is not in canonical form: expected {canon}, got {sol}",
                    )

                sol_tuple = tuple(sol)
                if sol_tuple in seen_canonical:
                    return False, f"FAIL: duplicate solution in enumeration: {sol}"
                seen_canonical.add(sol_tuple)

                # Outer list must be strictly sorted lexicographically
                if prev_sol is not None and sol <= prev_sol:
                    return (
                        False,
                        f"FAIL: solutions list is not strictly sorted ascending at index {idx}",
                    )
                prev_sol = sol

            # Set equality with ground truth if provided, otherwise with the exhaustive
            # enumeration inside the declared bounds; anything else fails closed.
            if ground_truth is not None:
                gt_solutions = (
                    ground_truth.get("solutions") if isinstance(ground_truth, Mapping) else None
                )
                if not isinstance(gt_solutions, list):
                    return False, "FAIL: ground_truth supplied without a solutions list"
                expected_set = {tuple(s) for s in gt_solutions}
            elif 1 <= n <= ENUMERATE_MAX_N and 1 <= bound <= ENUMERATE_MAX_BOUND:
                expected_set = {tuple(s) for s in enumerate_chiral_u1(n, bound)}
            else:
                return False, (
                    f"FAIL: enumeration for n={n}, bound={bound} is outside the declared bounds "
                    f"(n <= {ENUMERATE_MAX_N}, bound <= {ENUMERATE_MAX_BOUND}) and cannot be checked for completeness"
                )

            if seen_canonical != expected_set:
                return False, (
                    f"FAIL: enumeration mismatch: "
                    f"missing {len(expected_set - seen_canonical)}, spurious {len(seen_canonical - expected_set)}"
                )

            return (
                True,
                f"PASS: verified {count} chiral canonical solutions for n={n}, bound={bound}",
            )

        elif query == "complete":
            fixed = case.get("fixed")
            if not isinstance(fixed, list):
                return False, "FAIL: complete case fixed must be a list"

            completion = result.get("completion")
            claim = result.get("claim")

            # Branch A: claim == "NO_COMPLETION"
            if completion is None:
                extra = set(result.keys()) - ALLOWED_NOCOMP_KEYS
                if extra:
                    return (
                        False,
                        f"FAIL: illegal extra/phantom keys in NO_COMPLETION result: {sorted(extra)}",
                    )
                if claim != "NO_COMPLETION":
                    return (
                        False,
                        f"FAIL: completion is None but claim is {claim!r} (expected 'NO_COMPLETION')",
                    )

                # Verify that NO completion exists using pruned search
                refuter_sol = complete_chiral_u1(n, bound, fixed)
                if refuter_sol is not None:
                    return False, (
                        f"FAIL: false NO_COMPLETION claim; refuter found valid completion: {refuter_sol}"
                    )
                return True, "PASS: certified NO_COMPLETION verified"

            # Branch B: completion found
            extra = set(result.keys()) - ALLOWED_COMP_KEYS
            if extra:
                return (
                    False,
                    f"FAIL: illegal extra/phantom keys in SOLVED completion result: {sorted(extra)}",
                )
            if not isinstance(completion, list):
                return (
                    False,
                    f"FAIL: completion must be a list of integers, got {type(completion).__name__}",
                )

            expected_len = n - len(fixed)
            if len(completion) != expected_len:
                return (
                    False,
                    f"FAIL: completion length {len(completion)} != expected {expected_len}",
                )

            for c_val in completion:
                if type(c_val) is not int or isinstance(c_val, bool):
                    return False, f"FAIL: completion contains non-integer charge {c_val!r}"
                if c_val == 0:
                    return False, "FAIL: completion contains zero charge"
                if abs(c_val) > bound:
                    return False, f"FAIL: completion charge {c_val} exceeds bound {bound}"

            # Verify combined full spectrum
            full_spectrum = list(fixed) + completion
            if len(full_spectrum) != n:
                return False, f"FAIL: full spectrum length {len(full_spectrum)} != n={n}"

            # Linear anomaly
            if sum(full_spectrum) != 0:
                return False, f"FAIL: full spectrum linear sum != 0: sum={sum(full_spectrum)}"

            # Cubic anomaly
            if sum(x * x * x for x in full_spectrum) != 0:
                return (
                    False,
                    f"FAIL: full spectrum cubic sum != 0: sum3={sum(x * x * x for x in full_spectrum)}",
                )

            # Primitivity
            if not is_primitive(full_spectrum):
                return False, f"FAIL: full spectrum is non-primitive (gcd > 1): {full_spectrum}"

            # Chirality
            if not is_chiral(full_spectrum):
                return (
                    False,
                    f"FAIL: full spectrum is vector-like (Counter(q) == Counter(-q)): {full_spectrum}",
                )

            return True, f"PASS: verified chiral completion for n={n}, bound={bound}"

        else:
            return False, f"FAIL: unhandled query {query!r}"

    except Exception as exc:
        return False, f"FAIL: unhandled parsing exception: {type(exc).__name__}: {exc}"
