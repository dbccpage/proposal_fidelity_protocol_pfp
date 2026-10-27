# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Exact linear algebra over Q: determinant, leading minors, positive
definiteness, rank, characteristic polynomial.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence

from ..errors import ExactError
from .poly import Poly, trim
from .q import ONE, ZERO, Q

Matrix = tuple[tuple[Q, ...], ...]


def as_matrix(m: Sequence[Sequence[Q]]) -> Matrix:
    rows = tuple(tuple(r) for r in m)
    for r in rows:
        for x in r:
            if not isinstance(x, Q):
                raise ExactError("RR-FLOAT", "matrix entries must be exact rationals")
    if rows and any(len(r) != len(rows[0]) for r in rows):
        raise ExactError("RR-SHAPE", "ragged matrix")
    return rows


def _square(m: Matrix) -> int:
    n = len(m)
    if any(len(r) != n for r in m):
        raise ExactError("RR-SHAPE", "matrix is not square")
    return n


def det(m: Sequence[Sequence[Q]]) -> Q:
    a = [list(r) for r in as_matrix(m)]
    n = _square(tuple(tuple(r) for r in a))
    sign = ONE
    acc = ONE
    for col in range(n):
        piv = next((r for r in range(col, n) if not a[r][col].is_zero()), None)
        if piv is None:
            return ZERO
        if piv != col:
            a[col], a[piv] = a[piv], a[col]
            sign = -sign
        p = a[col][col]
        acc = acc * p
        for r in range(col + 1, n):
            f = a[r][col] / p
            if not f.is_zero():
                a[r] = [a[r][k] - f * a[col][k] for k in range(n)]
    return sign * acc


def leading_minors(m: Sequence[Sequence[Q]]) -> tuple[Q, ...]:
    mm = as_matrix(m)
    n = _square(mm)
    return tuple(det([row[:k] for row in mm[:k]]) for k in range(1, n + 1))


def is_symmetric(m: Sequence[Sequence[Q]]) -> bool:
    mm = as_matrix(m)
    n = _square(mm)
    return all(mm[i][j] == mm[j][i] for i in range(n) for j in range(n))


def first_nonpositive_minor(m: Sequence[Sequence[Q]]) -> int | None:
    """1-based index of the first leading minor that is not positive, or
    ``None`` when every one is (Sylvester: positive definite)."""
    if not is_symmetric(m):
        raise ExactError("RR-SHAPE", "positive definiteness needs a symmetric matrix")
    for k, v in enumerate(leading_minors(m), start=1):
        if v.sign() <= 0:
            return k
    return None


def is_positive_definite(m: Sequence[Sequence[Q]]) -> bool:
    return first_nonpositive_minor(m) is None


def rank(m: Sequence[Sequence[Q]]) -> int:
    a = [list(r) for r in as_matrix(m)]
    if not a:
        return 0
    rows, cols = len(a), len(a[0])
    r = 0
    for c in range(cols):
        piv = next((i for i in range(r, rows) if not a[i][c].is_zero()), None)
        if piv is None:
            continue
        a[r], a[piv] = a[piv], a[r]
        for i in range(rows):
            if i != r and not a[i][c].is_zero():
                f = a[i][c] / a[r][c]
                a[i] = [a[i][k] - f * a[r][k] for k in range(cols)]
        r += 1
    return r


def char_poly(m: Sequence[Sequence[Q]]) -> Poly:
    """det(xI - m), low to high degree, by the Faddeev-LeVerrier recurrence."""
    mm = as_matrix(m)
    n = _square(mm)
    coeffs = [ZERO] * (n + 1)
    coeffs[n] = ONE
    mk = [[ZERO] * n for _ in range(n)]  # M_0 = 0
    ck = ONE  # c_n
    for k in range(1, n + 1):
        # M_k = A M_{k-1} + c_{n-k+1} I
        prod = [
            [sum((mm[i][t] * mk[t][j] for t in range(n)), ZERO) for j in range(n)]
            for i in range(n)
        ]
        mk = [[prod[i][j] + (ck if i == j else ZERO) for j in range(n)] for i in range(n)]
        am = [
            [sum((mm[i][t] * mk[t][j] for t in range(n)), ZERO) for j in range(n)]
            for i in range(n)
        ]
        tr = sum((am[i][i] for i in range(n)), ZERO)
        ck = -(tr / Q(k))
        coeffs[n - k] = ck
    return trim(coeffs)
