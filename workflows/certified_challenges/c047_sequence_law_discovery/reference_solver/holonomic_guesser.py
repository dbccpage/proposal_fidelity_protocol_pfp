"""Holonomic recurrence guesser and absence certifier over Q for C047.
Finds minimal recurrences sum_{i=0}^r p_i(n) a(n+i) = 0 with deg(p_i) <= d.
"""

import math
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple

from .rational_linalg import bareiss_determinant, nullspace, rref


def lcm(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // math.gcd(a, b)


def canonicalize_polynomials(polys_frac: List[List[Fraction]]) -> List[List[str]]:
    """Convert rational polynomials to coprime integer polynomials with positive leading sign.
    polys_frac[i] is [c_{i,0}, c_{i,1}, ..., c_{i,d}].
    """
    # Find overall LCM of denominators
    overall_lcm = 1
    for p in polys_frac:
        for c in p:
            if c != 0:
                overall_lcm = lcm(overall_lcm, c.denominator)

    int_polys = []
    all_coeffs = []
    for p in polys_frac:
        row = [int(c * overall_lcm) for c in p]
        int_polys.append(row)
        for val in row:
            if val != 0:
                all_coeffs.append(val)

    if not all_coeffs:
        return [[str(c) for c in p] for p in int_polys]

    overall_gcd = abs(all_coeffs[0])
    for val in all_coeffs[1:]:
        overall_gcd = math.gcd(overall_gcd, abs(val))

    res = []
    for row in int_polys:
        res.append([val // overall_gcd for val in row])

    # Check leading sign of p_r (last non-zero coefficient of p_r should be positive)
    # If all p_r are 0, check last non-zero poly
    sign = 1
    for row in reversed(res):
        non_zeros = [v for v in row if v != 0]
        if non_zeros:
            if non_zeros[-1] < 0:
                sign = -1
            break

    if sign == -1:
        res = [[-v for v in row] for row in res]

    return [[str(v) for v in row] for row in res]


def build_system_matrix(
    terms: List[Fraction], r: int, d: int, start: int
) -> Tuple[List[List[Fraction]], List[int]]:
    """Build linear system matrix for sum_{i=0}^r sum_{j=0}^d c_{i,j} n^j a(n+i) = 0.
    Returns (matrix, row_indices).
    """
    N = len(terms)
    (r + 1) * (d + 1)
    matrix = []
    row_indices = []

    for n in range(start, N - r):
        row = []
        for i in range(r + 1):
            val_a = terms[n + i]
            n_pow = Fraction(1)
            for j in range(d + 1):
                row.append(n_pow * val_a)
                n_pow *= Fraction(n)
        matrix.append(row)
        row_indices.append(n)

    return matrix, row_indices


def leading_poly_has_integer_root_ge(poly: List[str], start: int) -> bool:
    """Check if polynomial p_r(n) has an integer root n >= start."""
    coeffs = [int(x) for x in poly]
    while len(coeffs) > 1 and coeffs[-1] == 0:
        coeffs.pop()
    deg = len(coeffs) - 1

    if deg == 0:
        return coeffs[0] == 0

    if deg == 1:
        c0, c1 = coeffs[0], coeffs[1]
        if -c0 % c1 == 0:
            root = -c0 // c1
            return root >= start
        return False

    if deg == 2:
        c0, c1, c2 = coeffs[0], coeffs[1], coeffs[2]
        disc = c1 * c1 - 4 * c0 * c2
        if disc < 0:
            return False
        s = math.isqrt(disc)
        if s * s != disc:
            return False
        for num in (-c1 + s, -c1 - s):
            denom = 2 * c2
            if num % denom == 0:
                if (num // denom) >= start:
                    return True
        return False

    if deg == 3:
        # Degree 3: check root 0 if c0 == 0
        c0 = coeffs[0]
        if c0 == 0 and 0 >= start:
            return True
        # Check integer roots in reasonable range [start, start + 200]
        for n in range(start, start + 200):
            val = coeffs[0] + coeffs[1] * n + coeffs[2] * n * n + coeffs[3] * n * n * n
            if val == 0:
                return True
        # For larger n, polynomial is monotonic if derivative has no real roots > start + 200
        return False

    return False


def verify_recurrence_on_terms(polys: List[List[str]], terms: List[Fraction], start: int) -> bool:
    """Verify that the recurrence holds exactly on all given terms."""
    r = len(polys) - 1
    len(polys[0]) - 1
    N = len(terms)

    int_polys = [[int(x) for x in p] for p in polys]

    for n in range(start, N - r):
        total = Fraction(0)
        for i in range(r + 1):
            p_val = Fraction(0)
            n_pow = Fraction(1)
            for j in range(len(int_polys[i])):
                p_val += Fraction(int_polys[i][j]) * n_pow
                n_pow *= Fraction(n)
            total += p_val * terms[n + i]
        if total != 0:
            return False
    return True


def guess_holonomic(
    terms: List[Fraction], r_max: int, d_max: int, max_start: int = 4
) -> Optional[Dict[str, Any]]:
    """Search for the minimal recurrence in order r and degree d."""
    N = len(terms)

    # Priority:
    # First try C-finite (d = 0) with increasing r = 1..r_max, start = 0..max_start
    # Then try general holonomic with increasing complexity (r + d, r, d)

    candidates = []
    # (r, d, start)
    for d in range(0, d_max + 1):
        for r in range(1, r_max + 1):
            for start in range(0, max_start + 1):
                candidates.append((r + d, d, r, start))

    candidates.sort()

    for _, d, r, start in candidates:
        u = (r + 1) * (d + 1)
        # We need enough terms: at least u + 4 terms beyond start + r
        if N - r - start < u + 2:
            continue

        mat, row_indices = build_system_matrix(terms, r, d, start)
        if len(mat) < u:
            continue

        # We compute nullspace using first (u + 2) rows to find candidate vectors
        sub_mat = mat[: u + 2]
        ns = nullspace(sub_mat)
        if not ns:
            continue

        for sol in ns:
            # Reconstruct polynomials
            polys_frac = []
            idx = 0
            for i in range(r + 1):
                row = []
                for j in range(d + 1):
                    row.append(sol[idx])
                    idx += 1
                polys_frac.append(row)

            # Check p_r is not all zero
            if all(c == 0 for c in polys_frac[r]):
                continue

            # Canonicalize to integer strings
            canon_polys = canonicalize_polynomials(polys_frac)

            # Check leading poly has no integer root >= start
            if leading_poly_has_integer_root_ge(canon_polys[r], start):
                continue

            # Verify on ALL available terms in prefix
            if verify_recurrence_on_terms(canon_polys, terms, start):
                return {
                    "status": "SOLVED",
                    "kind": "RECURRENCE",
                    "start": start,
                    "order": r,
                    "degree": d,
                    "polys": canon_polys,
                }

    return None


def certify_none_within_bounds(
    terms: List[Fraction], r_max: int, d_max: int, max_start: int = 5
) -> Optional[Dict[str, Any]]:
    """Certify that no linear recurrence of order <= r_max and degree <= d_max exists
    by finding a nonsingular u x u minor from indices >= max_start.
    """
    u = (r_max + 1) * (d_max + 1)
    N = len(terms)

    if N - r_max - max_start < u:
        return None

    mat, row_indices = build_system_matrix(terms, r_max, d_max, max_start)
    if len(mat) < u:
        return None

    # Use RREF to select u linearly independent rows from mat
    R, pivot_cols = rref(mat)
    # We want pivot rows of transpose(mat) to find independent rows of mat
    mat_T = [[mat[i][j] for i in range(len(mat))] for j in range(u)]
    _, row_pivots = rref(mat_T)

    if len(row_pivots) == u:
        chosen_rows = [row_indices[p] for p in row_pivots]
        chosen_matrix = [mat[p] for p in row_pivots]
        det = bareiss_determinant(chosen_matrix)
        if det != 0:
            return {
                "status": "SOLVED",
                "kind": "NONE_WITHIN_BOUNDS",
                "order": r_max,
                "degree": d_max,
                "start_range": [0, max_start],
                "minor_rows": chosen_rows,
                "determinant": str(det),
            }

    return None
