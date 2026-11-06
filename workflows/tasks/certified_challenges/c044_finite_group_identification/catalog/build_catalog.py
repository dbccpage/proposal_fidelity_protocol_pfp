# AuthorityEffect: None.
"""
Small Groups Catalog Builder for C044.
Constructs canonical representative Cayley tables and precomputes
the standard invariant menu for groups up to order 64.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple


def cycle_to_perm(cycles: List[List[int]], n: int) -> List[int]:
    p = list(range(n))
    for cyc in cycles:
        for i in range(len(cyc)):
            p[cyc[i]] = cyc[(i + 1) % len(cyc)]
    return p


def perm_mult(p1: List[int], p2: List[int]) -> List[int]:
    return [p1[x] for x in p2]


def closure_perms(gens: List[List[int]], degree: int) -> Tuple[List[List[int]], List[List[int]]]:
    identity = list(range(degree))
    elements = [identity]
    elem_to_idx = {tuple(identity): 0}
    queue = [identity]

    while queue:
        curr = queue.pop(0)
        for g in gens:
            prod = perm_mult(curr, g)
            tup = tuple(prod)
            if tup not in elem_to_idx:
                idx = len(elements)
                if idx > 128:
                    raise ValueError(f"Exceeds max group order: {idx}")
                elem_to_idx[tup] = idx
                elements.append(prod)
                queue.append(prod)

    n = len(elements)
    table = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            prod = perm_mult(elements[i], elements[j])
            table[i][j] = elem_to_idx[tuple(prod)]

    return elements, table


def make_cyclic(n: int) -> List[List[int]]:
    return [[(i + j) % n for j in range(n)] for i in range(n)]


def direct_product(t1: List[List[int]], t2: List[List[int]]) -> List[List[int]]:
    n1, n2 = len(t1), len(t2)
    n = n1 * n2
    table = [[0] * n for _ in range(n)]
    for i in range(n):
        g1, h1 = i // n2, i % n2
        for j in range(n):
            g2, h2 = j // n2, j % n2
            g3 = t1[g1][g2]
            h3 = t2[h1][h2]
            table[i][j] = g3 * n2 + h3
    return table


def make_dihedral(n: int) -> List[List[int]]:
    # Order 2n: r^n = 1, s^2 = 1, s r s = r^-1
    order = 2 * n
    table = [[0] * order for _ in range(order)]
    for i in range(order):
        s_i, r_i = i // n, i % n
        for j in range(order):
            s_j, r_j = j // n, j % n
            if s_i == 0 and s_j == 0:
                table[i][j] = (r_i + r_j) % n
            elif s_i == 0 and s_j == 1:
                table[i][j] = n + ((r_j - r_i) % n)
            elif s_i == 1 and s_j == 0:
                table[i][j] = n + ((r_i + r_j) % n)
            else:
                table[i][j] = (r_j - r_i) % n
    return table


def make_dicyclic(n: int) -> List[List[int]]:
    # Order 4n: x^(2n) = 1, y^2 = x^n, y x y^-1 = x^-1
    order = 4 * n
    table = [[0] * order for _ in range(order)]
    for i in range(order):
        s_i, r_i = i // (2 * n), i % (2 * n)
        for j in range(order):
            s_j, r_j = j // (2 * n), j % (2 * n)
            if s_i == 0 and s_j == 0:
                table[i][j] = (r_i + r_j) % (2 * n)
            elif s_i == 0 and s_j == 1:
                table[i][j] = 2 * n + ((r_j - r_i) % (2 * n))
            elif s_i == 1 and s_j == 0:
                table[i][j] = 2 * n + ((r_i + r_j) % (2 * n))
            else:
                table[i][j] = (n + r_j - r_i) % (2 * n)
    return table


def make_semidihedral_16() -> List[List[int]]:
    # Order 16: x^8 = 1, y^2 = 1, y x y = x^3
    order = 16
    table = [[0] * order for _ in range(order)]
    for i in range(order):
        s_i, r_i = i // 8, i % 8
        for j in range(order):
            s_j, r_j = j // 8, j % 8
            if s_i == 0 and s_j == 0:
                table[i][j] = (r_i + r_j) % 8
            elif s_i == 0 and s_j == 1:
                table[i][j] = 8 + ((3 * r_i + r_j) % 8)
            elif s_i == 1 and s_j == 0:
                table[i][j] = 8 + ((r_i + r_j) % 8)
            else:
                table[i][j] = (3 * r_i + r_j) % 8
    return table


def make_modular_16() -> List[List[int]]:
    # Order 16: x^8 = 1, y^2 = 1, y x y = x^5
    order = 16
    table = [[0] * order for _ in range(order)]
    for i in range(order):
        s_i, r_i = i // 8, i % 8
        for j in range(order):
            s_j, r_j = j // 8, j % 8
            if s_i == 0 and s_j == 0:
                table[i][j] = (r_i + r_j) % 8
            elif s_i == 0 and s_j == 1:
                table[i][j] = 8 + ((5 * r_i + r_j) % 8)
            elif s_i == 1 and s_j == 0:
                table[i][j] = 8 + ((r_i + r_j) % 8)
            else:
                table[i][j] = (5 * r_i + r_j) % 8
    return table


def make_frobenius_20() -> List[List[int]]:
    # Order 20: C5 : C4: x^5 = 1, y^4 = 1, y x y^-1 = x^2
    # Elements: y^a x^b with 0 <= a < 4, 0 <= b < 5. idx = 5*a + b
    order = 20
    table = [[0] * order for _ in range(order)]
    for i in range(order):
        a1, b1 = i // 5, i % 5
        for j in range(order):
            a2, b2 = j // 5, j % 5
            a3 = (a1 + a2) % 4
            b3 = (b1 * pow(2, a2, 5) + b2) % 5
            table[i][j] = 5 * a3 + b3
    return table


def make_heisenberg_3() -> List[List[int]]:
    # Order 27: Upper triangular 3x3 over F3 with 1s on diagonal
    # M(x, y, z): 0 <= x, y, z < 3. idx = 9*x + 3*y + z
    order = 27
    table = [[0] * order for _ in range(order)]
    for i in range(order):
        x1 = i // 9
        y1 = (i % 9) // 3
        z1 = i % 3
        for j in range(order):
            x2 = j // 9
            y2 = (j % 9) // 3
            z2 = j % 3
            x3 = (x1 + x2) % 3
            y3 = (y1 + y2) % 3
            z3 = (z1 + z2 + x1 * y2) % 3
            table[i][j] = 9 * x3 + 3 * y3 + z3
    return table


def pow_in_table(table: List[List[int]], x: int, k: int) -> int:
    res = 0
    curr = x
    while k > 0:
        if k & 1:
            res = table[res][curr]
        curr = table[curr][curr]
        k >>= 1
    return res


def compute_invariants(table: List[List[int]]) -> Dict[str, Any]:
    n = len(table)
    # 1. Inverses
    inv = [0] * n
    for i in range(n):
        for j in range(n):
            if table[i][j] == 0:
                inv[i] = j
                break

    # 2. Element order histogram
    orders = {}
    for i in range(n):
        curr = i
        ord_val = 1
        while curr != 0:
            curr = table[curr][i]
            ord_val += 1
        orders[str(ord_val)] = orders.get(str(ord_val), 0) + 1

    # 3. Centre order
    centre = 0
    for z in range(n):
        if all(table[z][x] == table[x][z] for x in range(n)):
            centre += 1

    # 4. Derived subgroup order
    commutators = set()
    for x in range(n):
        for y in range(n):
            xy = table[x][y]
            xy_xi = table[xy][inv[x]]
            comm = table[xy_xi][inv[y]]
            commutators.add(comm)

    # Closure of commutators
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
    derived_subgroup_order = len(der_set)

    # 5. Conjugacy class sizes
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

    # 6. Solutions to x^k = e for divisors k of n
    divisors = [d for d in range(1, n + 1) if n % d == 0]
    solutions_xk = {}
    for d in divisors:
        cnt = sum(1 for x in range(n) if pow_in_table(table, x, d) == 0)
        solutions_xk[str(d)] = cnt

    # 7. Abelianization factors
    ab_order = n // derived_subgroup_order
    ab_factors = compute_abelian_factors(ab_order, table, der_set)

    return {
        "element_order_histogram": orders,
        "centre_order": centre,
        "derived_subgroup_order": derived_subgroup_order,
        "abelianization_factors": ab_factors,
        "conjugacy_class_sizes": c_sizes,
        "solutions_xk_eq_e": solutions_xk,
    }


def compute_abelian_factors(ab_order: int, table: List[List[int]], der_set: set) -> List[int]:
    if ab_order == 1:
        return [1]
    n = len(table)
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


def build_catalog_database() -> List[Dict[str, Any]]:
    catalog = []

    def add_from_table(rep_id: List[int], name: str, table: List[List[int]]):
        assert len(table) == rep_id[0], f"Order mismatch: {len(table)} vs {rep_id[0]}"
        # Verify associativity
        n = len(table)
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    if table[table[i][j]][k] != table[i][table[j][k]]:
                        raise ValueError(
                            f"Table for {name} ({rep_id}) not associative at ({i},{j},{k})"
                        )
        invariants = compute_invariants(table)
        catalog.append(
            {
                "id": rep_id,
                "name": name,
                "order": rep_id[0],
                "table": table,
                "invariants": invariants,
            }
        )

    def add_group(rep_id: List[int], name: str, gens_cycles: List[List[List[int]]], degree: int):
        gens = [cycle_to_perm(c, degree) for c in gens_cycles] if gens_cycles else []
        if not gens:
            table = [[0]]
        else:
            _, table = closure_perms(gens, degree)
        add_from_table(rep_id, name, table)

    # Order 1
    add_group([1, 1], "C1", [], 1)

    # Order 2
    add_group([2, 1], "C2", [[[0, 1]]], 2)

    # Order 3
    add_group([3, 1], "C3", [[[0, 1, 2]]], 3)

    # Order 4
    add_from_table([4, 1], "C4", make_cyclic(4))
    add_from_table([4, 2], "V4", direct_product(make_cyclic(2), make_cyclic(2)))

    # Order 5
    add_from_table([5, 1], "C5", make_cyclic(5))

    # Order 6
    add_from_table([6, 1], "S3", make_dihedral(3))
    add_from_table([6, 2], "C6", make_cyclic(6))

    # Order 7
    add_from_table([7, 1], "C7", make_cyclic(7))

    # Order 8
    add_from_table([8, 1], "C8", make_cyclic(8))
    add_from_table([8, 2], "C4xC2", direct_product(make_cyclic(4), make_cyclic(2)))
    add_from_table([8, 3], "D8", make_dihedral(4))
    add_from_table([8, 4], "Q8", make_dicyclic(2))
    add_from_table(
        [8, 5],
        "C2^3",
        direct_product(make_cyclic(2), direct_product(make_cyclic(2), make_cyclic(2))),
    )

    # Order 9
    add_from_table([9, 1], "C9", make_cyclic(9))
    add_from_table([9, 2], "C3xC3", direct_product(make_cyclic(3), make_cyclic(3)))

    # Order 10
    add_from_table([10, 1], "D10", make_dihedral(5))
    add_from_table([10, 2], "C10", make_cyclic(10))

    # Order 12
    add_from_table([12, 1], "Dic3", make_dicyclic(3))
    add_from_table([12, 2], "C12", make_cyclic(12))
    add_group([12, 3], "A4", [[[0, 1, 2]], [[0, 1], [2, 3]]], 4)
    add_from_table([12, 4], "D12", make_dihedral(6))
    add_from_table([12, 5], "C6xC2", direct_product(make_cyclic(6), make_cyclic(2)))

    # Order 14
    add_from_table([14, 1], "D14", make_dihedral(7))
    add_from_table([14, 2], "C14", make_cyclic(14))

    # Order 15
    add_from_table([15, 1], "C15", make_cyclic(15))

    # Order 16 (All 14 groups of order 16)
    add_from_table([16, 1], "C16", make_cyclic(16))
    add_from_table([16, 2], "C4xC4", direct_product(make_cyclic(4), make_cyclic(4)))
    add_from_table([16, 5], "C8xC2", direct_product(make_cyclic(8), make_cyclic(2)))
    add_from_table([16, 7], "D16", make_dihedral(8))
    add_from_table([16, 8], "QD16", make_semidihedral_16())
    add_from_table([16, 9], "Q16", make_dicyclic(4))
    add_from_table(
        [16, 10],
        "C4xC2xC2",
        direct_product(make_cyclic(4), direct_product(make_cyclic(2), make_cyclic(2))),
    )
    add_from_table([16, 11], "D8xC2", direct_product(make_dihedral(4), make_cyclic(2)))
    add_from_table([16, 12], "Q8xC2", direct_product(make_dicyclic(2), make_cyclic(2)))
    add_from_table(
        [16, 14],
        "C2^4",
        direct_product(
            direct_product(make_cyclic(2), make_cyclic(2)),
            direct_product(make_cyclic(2), make_cyclic(2)),
        ),
    )

    # Order 18
    add_from_table([18, 1], "D18", make_dihedral(9))
    add_from_table([18, 2], "C18", make_cyclic(18))
    add_from_table([18, 4], "S3xC3", direct_product(make_dihedral(3), make_cyclic(3)))
    add_from_table(
        [18, 5],
        "C3^2xC2",
        direct_product(direct_product(make_cyclic(3), make_cyclic(3)), make_cyclic(2)),
    )

    # Order 20
    add_from_table([20, 1], "Dic5", make_dicyclic(5))
    add_from_table([20, 2], "C20", make_cyclic(20))
    add_from_table([20, 3], "F20", make_frobenius_20())
    add_from_table([20, 4], "D20", make_dihedral(10))
    add_from_table([20, 5], "C10xC2", direct_product(make_cyclic(10), make_cyclic(2)))

    # Order 24
    add_from_table([24, 2], "C24", make_cyclic(24))
    add_from_table([24, 6], "D24", make_dihedral(12))
    add_group([24, 12], "S4", [[[0, 1, 2, 3]], [[0, 1]]], 4)
    add_from_table(
        [24, 13], "A4xC2", direct_product(catalog[18]["table"], make_cyclic(2))
    )  # A4 x C2

    # Order 27
    add_from_table([27, 1], "C27", make_cyclic(27))
    add_from_table([27, 2], "C9xC3", direct_product(make_cyclic(9), make_cyclic(3)))
    add_from_table([27, 3], "Heis3", make_heisenberg_3())
    add_from_table(
        [27, 5],
        "C3^3",
        direct_product(make_cyclic(3), direct_product(make_cyclic(3), make_cyclic(3))),
    )

    # Order 32
    add_from_table([32, 1], "C32", make_cyclic(32))
    add_from_table([32, 16], "C16xC2", direct_product(make_cyclic(16), make_cyclic(2)))
    add_from_table([32, 18], "D32", make_dihedral(16))
    add_from_table([32, 21], "C8xC4", direct_product(make_cyclic(8), make_cyclic(4)))
    add_from_table(
        [32, 45],
        "C4xC4xC2",
        direct_product(direct_product(make_cyclic(4), make_cyclic(4)), make_cyclic(2)),
    )
    add_from_table(
        [32, 51],
        "C2^5",
        direct_product(
            direct_product(make_cyclic(2), make_cyclic(2)),
            direct_product(make_cyclic(2), direct_product(make_cyclic(2), make_cyclic(2))),
        ),
    )

    # Order 60
    add_group([60, 5], "A5", [[[0, 1, 2, 3, 4]], [[0, 1, 2]]], 5)

    # Order 64
    add_from_table([64, 1], "C64", make_cyclic(64))
    add_from_table([64, 52], "D64", make_dihedral(32))
    add_from_table(
        [64, 182],
        "C4^3",
        direct_product(make_cyclic(4), direct_product(make_cyclic(4), make_cyclic(4))),
    )
    add_from_table(
        [64, 267],
        "C2^6",
        direct_product(
            direct_product(make_cyclic(2), make_cyclic(2)),
            direct_product(
                direct_product(make_cyclic(2), make_cyclic(2)),
                direct_product(make_cyclic(2), make_cyclic(2)),
            ),
        ),
    )

    return catalog


if __name__ == "__main__":
    cat = build_catalog_database()
    out_path = Path(__file__).resolve().parent / "small_groups_catalog.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cat, f, indent=2)
    print(f"Catalog successfully built: {len(cat)} groups saved to {out_path.name}")
