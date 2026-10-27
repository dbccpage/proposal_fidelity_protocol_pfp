# AuthorityEffect: None.
"""
Exact Group Invariant Menu for C044.
Computes recomputable group invariants from Cayley tables:
- element_order_histogram
- centre_order
- derived_subgroup_order
- abelianization_factors
- conjugacy_class_sizes
- solutions_xk_eq_e
"""

import math
from typing import Any, Dict, List, Tuple


def pow_in_table(table: List[List[int]], x: int, k: int) -> int:
    res = 0
    curr = x
    while k > 0:
        if k & 1:
            res = table[res][curr]
        curr = table[curr][curr]
        k >>= 1
    return res


def compute_element_order_histogram(table: List[List[int]]) -> Dict[str, int]:
    n = len(table)
    orders = {}
    for i in range(n):
        curr = i
        ord_val = 1
        while curr != 0:
            curr = table[curr][i]
            ord_val += 1
        orders[str(ord_val)] = orders.get(str(ord_val), 0) + 1
    return orders


def compute_centre_order(table: List[List[int]]) -> int:
    n = len(table)
    centre = 0
    for z in range(n):
        if all(table[z][x] == table[x][z] for x in range(n)):
            centre += 1
    return centre


def compute_derived_subgroup(table: List[List[int]]) -> Tuple[int, set]:
    n = len(table)
    inv = [0] * n
    for i in range(n):
        for j in range(n):
            if table[i][j] == 0:
                inv[i] = j
                break

    commutators = set()
    for x in range(n):
        for y in range(n):
            xy = table[x][y]
            xy_xi = table[xy][inv[x]]
            comm = table[xy_xi][inv[y]]
            commutators.add(comm)

    der_sub = sorted(list(commutators))
    q = list(der_sub)
    der_set = set(der_sub)
    while q:
        curr = q.pop(0)
        for c in commutators:
            prod = table[curr][c]
            if prod not in der_set:
                der_set.add(prod)
                q.append(prod)
    return len(der_set), der_set


def compute_conjugacy_class_sizes(table: List[List[int]]) -> List[int]:
    n = len(table)
    inv = [0] * n
    for i in range(n):
        for j in range(n):
            if table[i][j] == 0:
                inv[i] = j
                break

    visited = [False] * n
    c_sizes = []
    for x in range(n):
        if not visited[x]:
            cls = set()
            for g in range(n):
                gx = table[g][x]
                gxg_inv = table[gx][inv[g]]
                cls.add(gxg_inv)
            for y in cls:
                visited[y] = True
            c_sizes.append(len(cls))
    c_sizes.sort()
    return c_sizes


def compute_solutions_xk_eq_e(table: List[List[int]]) -> Dict[str, int]:
    n = len(table)
    divisors = [d for d in range(1, n + 1) if n % d == 0]
    solutions = {}
    for d in divisors:
        cnt = sum(1 for x in range(n) if pow_in_table(table, x, d) == 0)
        solutions[str(d)] = cnt
    return solutions


def compute_abelianization_factors(table: List[List[int]], der_set: set) -> List[int]:
    n = len(table)
    der_order = len(der_set)
    ab_order = n // der_order
    if ab_order == 1:
        return [1]

    cosets = []
    elem_to_coset = {}
    for x in range(n):
        if x not in elem_to_coset:
            coset = sorted(list({table[x][d] for d in der_set}))
            c_idx = len(cosets)
            cosets.append(coset)
            for y in coset:
                elem_to_coset[y] = c_idx

    m = len(cosets)
    coset_table = [[0] * m for _ in range(m)]
    for i in range(m):
        rep_i = cosets[i][0]
        for j in range(m):
            rep_j = cosets[j][0]
            prod = table[rep_i][rep_j]
            coset_table[i][j] = elem_to_coset[prod]

    temp = m
    p_factors = {}
    d = 2
    while d * d <= temp:
        while temp % d == 0:
            p_factors[d] = p_factors.get(d, 0) + 1
            temp //= d
        d += 1
    if temp > 1:
        p_factors[temp] = p_factors.get(temp, 0) + 1

    prime_powers = {}
    for p, _ in p_factors.items():
        counts = []
        val = p
        while val <= m:
            cnt = sum(1 for x in range(m) if pow_in_table(coset_table, x, val) == 0)
            counts.append(cnt)
            if val == m or cnt == m:
                break
            val *= p
        log_counts = [int(round(math.log(c, p))) for c in counts]
        diffs = []
        prev = 0
        for lc in log_counts:
            diffs.append(lc - prev)
            prev = lc
        num_parts = diffs[0]
        p_parts = [0] * num_parts
        for m_idx, num_ge in enumerate(diffs):
            m_val = m_idx + 1
            for i in range(num_ge):
                p_parts[i] = m_val
        prime_powers[p] = [p**e for e in p_parts]

    max_k = max(len(v) for v in prime_powers.values()) if prime_powers else 1
    inv_factors = [1] * max_k
    for p, pows in prime_powers.items():
        pows.sort()
        offset = max_k - len(pows)
        for i, pw in enumerate(pows):
            inv_factors[offset + i] *= pw
    return inv_factors


def compute_all_invariants(table: List[List[int]]) -> Dict[str, Any]:
    der_order, der_set = compute_derived_subgroup(table)
    return {
        "element_order_histogram": compute_element_order_histogram(table),
        "centre_order": compute_centre_order(table),
        "derived_subgroup_order": der_order,
        "abelianization_factors": compute_abelianization_factors(table, der_set),
        "conjugacy_class_sizes": compute_conjugacy_class_sizes(table),
        "solutions_xk_eq_e": compute_solutions_xk_eq_e(table),
    }
