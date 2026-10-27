# AuthorityEffect: None.
"""
Alexander Polynomial Computation from PD Code.
Pure Python standard library with exact rational evaluation and Lagrange interpolation.
Normalizes to the unique symmetric Alexander-Conway polynomial Delta(t) = Delta(t^-1) with Delta(1) = 1.
"""

from fractions import Fraction
from typing import Dict, List, Tuple


def compute_alexander_poly(pd: List[List[int]], signs: List[int]) -> Dict[str, int]:
    """
    Computes the symmetrized Alexander-Conway polynomial Delta(t) in Z[t, t^-1].
    For unknot, returns Delta(t) = 1 ({"0": 1}).
    """
    n = len(pd)
    if n == 0:
        return {"0": 1}

    # Identify arcs using union-find on overstrand edges (j ~ l)
    parent = {e: e for e in range(1, 2 * n + 1)}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for i, j, k, l in pd:
        union(j, l)

    arc_reps = sorted(list(set(find(e) for e in range(1, 2 * n + 1))))
    arc_idx = {rep: idx for idx, rep in enumerate(arc_reps)}

    # If there is only 1 crossing (unknot with kink): minor is empty, Delta(t) = 1
    if n == 1 or len(arc_reps) <= 1:
        return {"0": 1}

    # Evaluate (n-1) x (n-1) minor at num_pts distinct values of t
    num_pts = n + 2
    points: List[Tuple[Fraction, Fraction]] = []

    for t_val in range(1, num_pts + 1):
        M = [[Fraction(0)] * len(arc_reps) for _ in range(n)]
        t_f = Fraction(t_val)

        for c_idx, (i, j, k, l) in enumerate(pd):
            sign = signs[c_idx]
            u = arc_idx[find(i)]
            v = arc_idx[find(k)]
            w = arc_idx[find(j)]

            if sign == 1:
                M[c_idx][u] += t_f
                M[c_idx][v] += -1
                M[c_idx][w] += 1 - t_f
            else:
                M[c_idx][u] += 1
                M[c_idx][v] += -t_f
                M[c_idx][w] += t_f - 1

        # Minor: remove row 0 and column 0
        subM = [row[1:] for row in M[1:]]
        m_len = len(subM)

        # Determinant via Gaussian elimination with exact Fraction arithmetic
        det = Fraction(1)
        for col in range(m_len):
            piv = None
            for row in range(col, m_len):
                if subM[row][col] != 0:
                    piv = row
                    break
            if piv is None:
                det = Fraction(0)
                break
            if piv != col:
                subM[col], subM[piv] = subM[piv], subM[col]
                det = -det
            det *= subM[col][col]
            pv = subM[col][col]
            for row in range(col + 1, m_len):
                f = subM[row][col] / pv
                for k_col in range(col + 1, m_len):
                    subM[row][k_col] -= f * subM[col][k_col]

        points.append((Fraction(t_val), det))

    # Lagrange interpolation: find P(t) = sum c_i * t^i
    poly_coeffs = [Fraction(0)] * num_pts
    for i in range(num_pts):
        xi, yi = points[i]
        cur = [Fraction(1)]
        denom = Fraction(1)
        for j in range(num_pts):
            if i == j:
                continue
            xj, _ = points[j]
            denom *= xi - xj
            nxt = [Fraction(0)] * (len(cur) + 1)
            for deg, coeff in enumerate(cur):
                nxt[deg + 1] += coeff
                nxt[deg] -= coeff * xj
            cur = nxt
        scale = yi / denom
        for deg, coeff in enumerate(cur):
            poly_coeffs[deg] += coeff * scale

    poly_terms = {
        deg: int(round(float(c))) for deg, c in enumerate(poly_coeffs) if abs(c) > Fraction(1, 1000)
    }

    if not poly_terms:
        return {"0": 1}

    # Symmetrize so that Delta(t) = Delta(t^-1)
    min_p = min(poly_terms.keys())
    max_p = max(poly_terms.keys())
    span = max_p - min_p
    shift = min_p + span // 2

    alex = {}
    for deg, coeff in poly_terms.items():
        alex[str(deg - shift)] = coeff

    # Normalize so that Delta(1) > 0 (for knots, Delta(1) = 1)
    val_at_1 = sum(alex.values())
    if val_at_1 < 0:
        alex = {p: -c for p, c in alex.items()}

    return {p: c for p, c in sorted(alex.items(), key=lambda kv: int(kv[0])) if c != 0}
