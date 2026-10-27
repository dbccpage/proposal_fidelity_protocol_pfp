"""Diophantine Anomaly Equation Solver for C031 (Anomaly-Free Chiral U(1) Charges).

Solves the Diophantine system:
    sum(q_i) = 0  and  sum(q_i^3) = 0
for integer charges q_i in [-Q, Q] \\ {0}, subject to:
1. Primitivity: gcd(|q_1|, ..., |q_n|) = 1
2. Chirality: Counter(q) != Counter(-q) (strictly non-vector-like)
3. Canonical representative: min(sort(q), sort(-q)) in lexicographical order.

Supports:
- enumerate (n <= 10, Q <= 12): Exhaustive canonical chiral enumeration
- complete (n <= 12, Q <= 2*10^6): Spectrum completion with Diophantine resolvents

AuthorityEffect: None.
"""

from __future__ import annotations

import itertools
import math
from collections import Counter
from collections.abc import Sequence


def is_primitive(charges: Sequence[int]) -> bool:
    """Verifies that the charges share no common integer factor > 1."""
    if not charges:
        return False
    g = 0
    for q in charges:
        g = math.gcd(g, abs(q))
        if g == 1:
            return True
    return g == 1


def is_chiral(charges: Sequence[int]) -> bool:
    """Verifies that the charge multiset is chiral (does not equal its negation)."""
    if not charges:
        return False
    return Counter(charges) != Counter(-x for x in charges)


def canonical_representative(charges: Sequence[int]) -> list[int]:
    """Returns the canonical representative: min(sort(q), sort(-q))."""
    s1 = sorted(charges)
    s2 = sorted(-x for x in charges)
    return s1 if s1 <= s2 else s2


def solve_pair(s: int, c: int, min_val: int, max_val: int) -> list[tuple[int, int]]:
    """Exact algebraic quadratic resolvent for x + y = s, x^3 + y^3 = c.

    Finds all integer pairs (x, y) such that:
        x + y = s
        x^3 + y^3 = c
        min_val <= x <= y <= max_val
        x != 0, y != 0

    Executes in O(1) arbitrary-precision integer arithmetic without float rounding.
    """
    if min_val > max_val:
        return []

    # Case 1: s == 0 (x + y = 0 => y = -x)
    if s == 0:
        if c != 0:
            return []
        # y = -x, x <= y => x <= -x => x <= 0
        # Charges cannot be 0 => x < 0
        # min_val <= x and -x <= max_val => x >= -max_val
        lower = max(min_val, -max_val)
        upper = min(-1, max_val)
        if lower > upper:
            return []
        results: list[tuple[int, int]] = []
        for x in range(lower, upper + 1):
            results.append((x, -x))
        return results

    # Case 2: s != 0
    # x^3 + y^3 = s * (s^2 - 3xy) = c
    if c % s != 0:
        return []

    d = c // s
    rem_3 = s * s - d
    if rem_3 % 3 != 0:
        return []

    p = rem_3 // 3  # xy = p
    # Discriminant of T^2 - sT + P = 0 is delta = s^2 - 4P
    delta = s * s - 4 * p
    if delta < 0:
        return []

    r = math.isqrt(delta)
    if r * r != delta:
        return []

    # Parity check: (s - r) must be even
    if (s - r) % 2 != 0:
        return []

    x = (s - r) // 2
    y = (s + r) // 2

    if x != 0 and y != 0 and min_val <= x <= y <= max_val:
        return [(x, y)]
    return []


def enumerate_chiral_u1(n: int, bound: int) -> list[list[int]]:
    """Enumerates all canonical chiral primitive charge assignments for (n, bound).

    For n <= 4, provably returns [] by the cube-sum factorization identity.
    """
    if n <= 4 or bound <= 0:
        return []

    solutions: list[list[int]] = []

    def _search(
        depth: int, current_charges: list[int], current_sum: int, current_sum3: int, q_eff: int
    ) -> None:
        remaining = n - depth
        if remaining == 2:
            s_rem = -current_sum
            c_rem = -current_sum3
            last_q = current_charges[-1]
            pairs = solve_pair(s_rem, c_rem, min_val=last_q, max_val=q_eff)
            for x, y in pairs:
                cand = current_charges + [x, y]
                # Filter canonical representative
                if canonical_representative(cand) != cand:
                    continue
                # Filter primitivity
                if not is_primitive(cand):
                    continue
                # Filter chirality
                if not is_chiral(cand):
                    continue
                solutions.append(cand)
            return

        last_val = current_charges[-1]
        for v in range(last_val, q_eff + 1):
            if v == 0:
                continue
            next_sum = current_sum + v
            next_sum3 = current_sum3 + v * v * v
            rem_after = remaining - 1
            # Step-ahead linear sum pruning
            if -(next_sum) < rem_after * v or -(next_sum) > rem_after * q_eff:
                continue
            current_charges.append(v)
            _search(depth + 1, current_charges, next_sum, next_sum3, q_eff)
            current_charges.pop()

    # Iterate q1 in [-bound, -1]
    # For canonical solutions, q1 must be negative and q_n <= -q1
    for q1 in range(-bound, 0):
        q_eff = min(bound, -q1)
        _search(1, [q1], q1, q1 * q1 * q1, q_eff)

    solutions.sort()
    return solutions


def complete_chiral_u1(n: int, bound: int, fixed: Sequence[int]) -> list[int] | None:
    """Finds a completion of fixed charges to form an anomaly-free chiral primitive spectrum.

    Returns the list of completion charges if found, or None if certified NO_COMPLETION.
    """
    k = len(fixed)
    m = n - k
    if m <= 0:
        if m == 0 and sum(fixed) == 0 and sum(x * x * x for x in fixed) == 0:
            if is_primitive(fixed) and is_chiral(fixed):
                return []
        return None

    target_s = -sum(fixed)
    target_c = -sum(x * x * x for x in fixed)

    # Fast path: m == 1
    if m == 1:
        c1 = target_s
        if c1 != 0 and abs(c1) <= bound and c1 * c1 * c1 == target_c:
            cand = list(fixed) + [c1]
            if is_primitive(cand) and is_chiral(cand):
                return [c1]
        return None

    # Fast path: m == 2
    if m == 2:
        pairs = solve_pair(target_s, target_c, min_val=-bound, max_val=bound)
        for x, y in pairs:
            cand = list(fixed) + [x, y]
            if is_primitive(cand) and is_chiral(cand):
                return [x, y]
        return None

    # Fast path: m == 3
    if m == 3:
        for c1 in range(-bound, bound + 1):
            if c1 == 0:
                continue
            s_rem = target_s - c1
            c_rem = target_c - c1 * c1 * c1
            pairs = solve_pair(s_rem, c_rem, min_val=-bound, max_val=bound)
            for x, y in pairs:
                cand = list(fixed) + [c1, x, y]
                if is_primitive(cand) and is_chiral(cand):
                    return [c1, x, y]
        return None

    # Strategy for m >= 4
    # If bound is small (<= 50), use Meet-in-the-Middle
    if bound <= 50:
        m1 = m // 2
        m2 = m - m1
        valid_range = [v for v in range(-bound, bound + 1) if v != 0]

        # Build Half 1 table: (s, c) -> tuple
        table: dict[tuple[int, int], tuple[int, ...]] = {}
        for combo in itertools.combinations_with_replacement(valid_range, m1):
            s1 = sum(combo)
            c1 = sum(x * x * x for x in combo)
            key = (s1, c1)
            if key not in table:
                table[key] = combo

        # Probe Half 2
        for combo in itertools.combinations_with_replacement(valid_range, m2):
            s2 = sum(combo)
            c2 = sum(y * y * y for y in combo)
            need_s = target_s - s2
            need_c = target_c - c2
            match = table.get((need_s, need_c))
            if match is not None:
                completion = list(match) + list(combo)
                cand = list(fixed) + completion
                if is_primitive(cand) and is_chiral(cand):
                    return completion
        return None

    # Large bound (bound > 50, m >= 4): Branch-and-bound with linear interval pruning down to m=2
    def _search_complete(
        depth: int, current_charges: list[int], cur_s: int, cur_c: int
    ) -> list[int] | None:
        rem = m - depth
        if rem == 2:
            s_rem = target_s - cur_s
            c_rem = target_c - cur_c
            min_q = current_charges[-1] if current_charges else -bound
            pairs = solve_pair(s_rem, c_rem, min_val=min_q, max_val=bound)
            for x, y in pairs:
                cand = list(fixed) + current_charges + [x, y]
                if is_primitive(cand) and is_chiral(cand):
                    return current_charges + [x, y]
            return None

        last_val = current_charges[-1] if current_charges else -bound
        rem_target = target_s - cur_s
        # Linear bounds for rem variables
        low_v = max(last_val, -bound)
        high_v = min(bound, rem_target - (rem - 1) * last_val)

        for v in range(low_v, high_v + 1):
            if v == 0:
                continue
            next_s = cur_s + v
            next_c = cur_c + v * v * v
            rem_after = rem - 1
            diff = target_s - next_s
            if diff < rem_after * v or diff > rem_after * bound:
                continue
            current_charges.append(v)
            res = _search_complete(depth + 1, current_charges, next_s, next_c)
            if res is not None:
                return res
            current_charges.pop()
        return None

    return _search_complete(0, [], 0, 0)
