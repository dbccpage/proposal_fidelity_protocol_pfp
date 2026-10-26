"""Target checker of record for MSS-070, row 70 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 70): compute the exact determinant polynomial. Negative
instance: an asserted eigenvalue with no matrix witness is rejected.

Input (closed): ``{"table": M | null, "polynomial": [c0, ..., cn], "roots":
[lambda]}``. M is an n x n table of canonical rationals. ``polynomial`` is the
producer's det(xI - M) in ascending degree; each root is a claimed rational
eigenvalue.

The checker computes det(xI - M) by two independent routes and requires them
to agree: the Faddeev-LeVerrier trace recurrence, and exact elimination
determinants of xI - M at x = 0..n followed by Lagrange interpolation. A
disagreement would be a fault of the checker, refused as a schema fault.

Declared input class: square rational tables, 1 <= n <= 8, and rational root
claims. An irrational eigenvalue is not claimable here; its defining
polynomial and isolating interval belong to stage 069.

Clauses, decided in this order:

- C1 ``R070_NO_TABLE``: roots are asserted with no table (the level's
  negative);
- C2 ``R070_POLYNOMIAL``: the claimed polynomial differs from the computed one;
- C3 ``R070_NOT_A_ROOT``: a claimed root lambda has p_M(lambda) != 0.
"""

STAGE = 70
ROW_SHA256 = "sha256:09ce8d7c9f2865b0a06ec50206e3a33a478996330caecf9f53ec3fcc5530d4ba"
FIELDS = ("polynomial", "roots", "table")
CLAUSES = (
    ("C1", "R070_NO_TABLE"),
    ("C2", "R070_POLYNOMIAL"),
    ("C3", "R070_NOT_A_ROOT"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {"polynomial": ["1/1", "0/1", "1/1"], "roots": ["2/1"], "table": None}
OWN_NEGATIVE_CODE = "R070_NO_TABLE"


def _leverrier(m):
    n = len(m)
    coefficients = [Fraction(0)] * (n + 1)
    coefficients[n] = Fraction(1)
    current = [[Fraction(0)] * n for _ in range(n)]
    for k in range(1, n + 1):
        current = [
            [sum((m[i][t] * current[t][j] for t in range(n)), Fraction(0)) + (coefficients[n - k + 1] if i == j else 0)
             for j in range(n)]
            for i in range(n)
        ]
        product_trace = sum((m[i][t] * current[t][i] for i in range(n) for t in range(n)), Fraction(0))
        coefficients[n - k] = -product_trace / k
    return coefficients


def _det(a):
    a = [list(row) for row in a]
    n, sign, out = len(a), 1, Fraction(1)
    for c in range(n):
        pivot = next((r for r in range(c, n) if a[r][c] != 0), None)
        if pivot is None:
            return Fraction(0)
        if pivot != c:
            a[c], a[pivot] = a[pivot], a[c]
            sign = -sign
        out *= a[c][c]
        for r in range(c + 1, n):
            factor = a[r][c] / a[c][c]
            a[r] = [x - factor * y for x, y in zip(a[r], a[c])]
    return sign * out


def _interpolated(m):
    n = len(m)
    points = list(range(n + 1))
    values = [_det([[(x if i == j else 0) - m[i][j] for j in range(n)] for i in range(n)]) for x in points]
    coefficients = [Fraction(0)] * (n + 1)
    for k, xk in enumerate(points):
        basis, scale = [Fraction(1)], Fraction(1)
        for j, xj in enumerate(points):
            if j != k:
                basis = [Fraction(0)] + basis
                for t in range(len(basis) - 1):
                    basis[t] -= xj * basis[t + 1]
                scale *= xk - xj
        for t in range(n + 1):
            coefficients[t] += values[k] * basis[t] / scale
    return coefficients


def _evaluate(p, x):
    total = Fraction(0)
    for c in reversed(p):
        total = total * x + c
    return total


def _decide(payload):
    claimed = _rats(payload["polynomial"])
    roots = _rats(payload["roots"])
    table = payload["table"]
    _require(table is not None, "R070_NO_TABLE")
    m = _matrix(table)
    n = len(m)
    _require(1 <= n <= 8 and all(len(row) == n for row in m), "R_SCHEMA")
    first, second = _leverrier(m), _interpolated(m)
    if first != second:
        raise ValueError("the two routes disagree")
    _require(claimed == first, "R070_POLYNOMIAL")
    _require(all(_evaluate(first, r) == 0 for r in roots), "R070_NOT_A_ROOT")
