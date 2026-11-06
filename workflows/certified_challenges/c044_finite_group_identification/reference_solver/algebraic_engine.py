# AuthorityEffect: None.
"""
Algebraic Engine for C044.
Parses, validates, and normalizes permutation, matrix, and Cayley table presentations.
"""

from typing import Any, Dict, List, Optional, Tuple


def perm_mult(p1: List[int], p2: List[int]) -> List[int]:
    return [p1[x] for x in p2]


def perm_inv(p: List[int]) -> List[int]:
    inv = [0] * len(p)
    for i, x in enumerate(p):
        inv[x] = i
    return inv


def mat_mult(m1: List[List[int]], m2: List[List[int]], p: int) -> List[List[int]]:
    dim = len(m1)
    res = [[0] * dim for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            s = 0
            for k in range(dim):
                s = (s + m1[i][k] * m2[k][j]) % p
            res[i][j] = s
    return res


def mat_ident(dim: int) -> List[List[int]]:
    return [[1 if i == j else 0 for j in range(dim)] for i in range(dim)]


def mat_to_tuple(m: List[List[int]]) -> tuple:
    return tuple(tuple(row) for row in m)


def closure_perms(gens: List[List[int]], degree: int) -> Tuple[bool, Any]:
    """Generates all elements of a permutation group via BFS."""
    identity = list(range(degree))
    elements = [identity]
    elem_to_idx = {tuple(identity): 0}
    queue = [identity]
    gen_indices = []

    for g in gens:
        tup = tuple(g)
        if tup not in elem_to_idx:
            elem_to_idx[tup] = len(elements)
            elements.append(g)
            queue.append(g)
        gen_indices.append(elem_to_idx[tup])

    while queue:
        curr = queue.pop(0)
        for g in gens:
            prod = perm_mult(curr, g)
            tup = tuple(prod)
            if tup not in elem_to_idx:
                idx = len(elements)
                if idx > 64:
                    return False, {"reason": "EXCEEDS_MAX_ORDER", "order": idx, "words": ["*"] * 65}
                elem_to_idx[tup] = idx
                elements.append(prod)
                queue.append(prod)

    n = len(elements)
    table = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            prod = perm_mult(elements[i], elements[j])
            table[i][j] = elem_to_idx[tuple(prod)]

    return True, (table, gen_indices)


def closure_matrices(gens: List[List[List[int]]], dim: int, p: int) -> Tuple[bool, Any]:
    """Generates all elements of a matrix group over GF(p) via BFS."""
    identity = mat_ident(dim)
    elements = [identity]
    elem_to_idx = {mat_to_tuple(identity): 0}
    queue = [identity]
    gen_indices = []

    for g in gens:
        tup = mat_to_tuple(g)
        if tup not in elem_to_idx:
            elem_to_idx[tup] = len(elements)
            elements.append(g)
            queue.append(g)
        gen_indices.append(elem_to_idx[tup])

    while queue:
        curr = queue.pop(0)
        for g in gens:
            prod = mat_mult(curr, g, p)
            tup = mat_to_tuple(prod)
            if tup not in elem_to_idx:
                idx = len(elements)
                if idx > 64:
                    return False, {"reason": "EXCEEDS_MAX_ORDER", "order": idx, "words": ["*"] * 65}
                elem_to_idx[tup] = idx
                elements.append(prod)
                queue.append(prod)

    n = len(elements)
    table = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            prod = mat_mult(elements[i], elements[j], p)
            table[i][j] = elem_to_idx[mat_to_tuple(prod)]

    return True, (table, gen_indices)


def validate_table(table: List[List[int]]) -> Tuple[bool, Optional[Dict[str, Any]]]:
    n = len(table)
    if n == 0 or n > 64:
        return False, {"reason": "INVALID_ORDER", "order": n}

    # Element 0 must be identity
    for i in range(n):
        if len(table[i]) != n:
            return False, {"reason": "NOT_SQUARE"}
        if table[0][i] != i or table[i][0] != i:
            return False, {"reason": "MISSING_IDENTITY_OR_INVERSE", "element": 0}

    # Check inverses
    for i in range(n):
        has_inv = False
        for j in range(n):
            if table[i][j] == 0 and table[j][i] == 0:
                has_inv = True
                break
        if not has_inv:
            return False, {"reason": "MISSING_IDENTITY_OR_INVERSE", "element": i}

    # Check associativity
    for i in range(n):
        for j in range(n):
            ij = table[i][j]
            for k in range(n):
                if table[ij][k] != table[i][table[j][k]]:
                    return False, {"reason": "NOT_ASSOCIATIVE", "triple": [i, j, k]}

    return True, None


def find_generating_set(table: List[List[int]]) -> List[int]:
    """Finds a minimal generating set of size <= 6 for any group of order <= 64."""
    n = len(table)
    if n <= 1:
        return [0]
    gens = []
    generated = {0}
    while len(generated) < n:
        cand = next(x for x in range(n) if x not in generated)
        gens.append(cand)
        q = [cand]
        generated.add(cand)
        while q:
            curr = q.pop(0)
            for g in gens:
                nxt1 = table[curr][g]
                if nxt1 not in generated:
                    generated.add(nxt1)
                    q.append(nxt1)
                nxt2 = table[g][curr]
                if nxt2 not in generated:
                    generated.add(nxt2)
                    q.append(nxt2)
    return gens


def parse_presentation(pres: Dict[str, Any]) -> Tuple[bool, Any]:
    kind = pres.get("presentation")
    if kind == "table":
        table = pres.get("table", [])
        ok, wit = validate_table(table)
        if not ok:
            return False, wit
        gens = pres.get("gens")
        if gens is None:
            gens = find_generating_set(table)
        return True, (table, gens)

    elif kind == "perm":
        degree = pres.get("degree", 0)
        gens = pres.get("gens", [])
        ok, res = closure_perms(gens, degree)
        if not ok:
            return False, res
        table, gen_indices = res
        ok_t, wit = validate_table(table)
        if not ok_t:
            return False, wit
        return True, (table, gen_indices)

    elif kind == "matrix":
        p = pres.get("p", 2)
        dim = pres.get("dim", 2)
        gens = pres.get("gens", [])
        ok, res = closure_matrices(gens, dim, p)
        if not ok:
            return False, res
        table, gen_indices = res
        ok_t, wit = validate_table(table)
        if not ok_t:
            return False, wit
        return True, (table, gen_indices)

    return False, {"reason": "UNKNOWN_PRESENTATION", "kind": kind}
