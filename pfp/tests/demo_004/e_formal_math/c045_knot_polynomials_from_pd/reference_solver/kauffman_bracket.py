# AuthorityEffect: None.
"""
Kauffman Bracket and Jones Polynomial Computation from PD Code.
Pure Python standard library with exact integer and rational arithmetic.
"""

from collections import defaultdict
from math import comb
from typing import Dict, List, Tuple


def compute_kauffman_and_jones(
    pd: List[List[int]], writhe: int
) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    Computes Kauffman bracket <K> in Z[A, A^-1] and normalized Jones polynomial V(t) in Z[t, t^-1].
    For unknot (pd == []), returns <K> = 1, V(t) = 1.
    """
    n = len(pd)
    if n == 0:
        return {"0": 1}, {"0": 1}

    # State sum over 2^n states
    poly = defaultdict(int)
    for mask in range(1 << n):
        adj = defaultdict(list)
        a_cnt = 0
        b_cnt = 0
        for c in range(n):
            i, j, k, l = pd[c]
            bit = (mask >> c) & 1
            if bit == 0:
                # A-smoothing connects (i, j) and (k, l)
                a_cnt += 1
                pairs = [(i, j), (k, l)]
            else:
                # B-smoothing connects (i, l) and (j, k)
                b_cnt += 1
                pairs = [(i, l), (j, k)]
            for u, v in pairs:
                adj[u].append(v)
                adj[v].append(u)

        visited = set()
        loops = 0
        for edge in range(1, 2 * n + 1):
            if edge not in visited:
                loops += 1
                stack = [edge]
                visited.add(edge)
                while stack:
                    curr = stack.pop()
                    for nxt in adj[curr]:
                        if nxt not in visited:
                            visited.add(nxt)
                            stack.append(nxt)

        base_power = a_cnt - b_cnt
        L = loops
        # (-A^2 - A^-2)^(L - 1)
        sign = (-1) ** (L - 1)
        for k in range(L):
            coeff = sign * comb(L - 1, k)
            p = base_power + (4 * k - 2 * (L - 1))
            poly[p] += coeff

    # Kauffman bracket with string keys
    bracket = {str(p): c for p, c in sorted(poly.items()) if c != 0}

    # Jones polynomial: V(t) = (-A^3)^(-w) * <K> with A = t^(-1/4)
    # (-A^3)^(-w) = (-1)^w * A^(-3w)
    # Term c * A^p becomes c * (-1)^w * A^(p - 3w) = c * (-1)^w * t^(-(p - 3w)/4)
    jones = defaultdict(int)
    sign_w = (-1) ** (writhe % 2)
    for p_str, c in bracket.items():
        p = int(p_str)
        P = p - 3 * writhe
        t_pow = -(P // 4)
        jones[t_pow] += c * sign_w

    jones_poly = {str(p): c for p, c in sorted(jones.items()) if c != 0}
    return bracket, jones_poly
