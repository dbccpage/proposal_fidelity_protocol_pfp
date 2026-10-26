"""Target checker of record for MSS-034, row 34 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 34): check normalized likelihood and positive semidefinite
Fisher matrix. Negative instance: a negative variance direction is rejected.

Input (closed): ``{"family": [[[rational, [nat]]]], "point": [rational],
"fisher": [[rational]]}``. ``family`` gives one polynomial per outcome in the
k parameters, as monomials ``[coefficient, exponents]``; ``point`` is the
parameter value; ``fisher`` is the declared k x k information matrix there.

Declared input class: finitely many outcomes, polynomial parametrisations
with rational coefficients, one rational interior point (every outcome has
positive probability there). Normalisation is decided as a polynomial
identity; the matrix is recomputed exactly as the sum over outcomes of
(d_i p)(d_j p) / p at the point, with exact polynomial derivatives; positive
semidefiniteness is decided by every principal minor (k at most 6).

Clauses, each recomputed:

- C1 ``R034_NOT_NORMALISED``: the outcome polynomials do not sum to 1
  identically, or some outcome is not positive at the point;
- C2 ``R034_NEGATIVE_DIRECTION``: the declared matrix is not symmetric
  positive semidefinite: a principal minor is negative (the level's
  negative);
- C3 ``R034_MATRIX_MISMATCH``: the declared matrix is not the recomputed
  information matrix.

C2 is decided on the declared matrix before it is recomputed, so a matrix
with a negative variance direction is refused as such.
"""

from itertools import combinations, permutations

STAGE = 34
ROW_SHA256 = "sha256:7a790466e7c1ba5fd13361699a695ad2919590e3369dc8856eaa6ea3b869c486"
FIELDS = ("family", "fisher", "point")
CLAUSES = (
    ("C1", "R034_NOT_NORMALISED"),
    ("C2", "R034_NEGATIVE_DIRECTION"),
    ("C3", "R034_MATRIX_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "family": [
        [["1/1", [1, 0]]],
        [["1/1", [0, 1]]],
        [["1/1", [0, 0]], ["-1/1", [1, 0]], ["-1/1", [0, 1]]],
    ],
    "fisher": [["1/1", "2/1"], ["2/1", "1/1"]],
    "point": ["1/3", "1/3"],
}
OWN_NEGATIVE_CODE = "R034_NEGATIVE_DIRECTION"


def _poly(value, k):
    out = {}
    for term in _seq(value):
        _seq(term, 2)
        coefficient = _rat(term[0])
        exponents = tuple(_nat(e) for e in _seq(term[1], k))
        _require(exponents not in out, "R_SCHEMA")
        out[exponents] = coefficient
    return out


def _evaluate(poly, point):
    total = Fraction(0)
    for exponents, coefficient in poly.items():
        value = coefficient
        for x, e in zip(point, exponents):
            value *= x ** e
        total += value
    return total


def _derivative(poly, i):
    out = {}
    for exponents, coefficient in poly.items():
        if exponents[i]:
            lowered = exponents[:i] + (exponents[i] - 1,) + exponents[i + 1:]
            out[lowered] = out.get(lowered, Fraction(0)) + coefficient * exponents[i]
    return out


def _det(matrix):
    n = len(matrix)
    total = Fraction(0)
    for perm in permutations(range(n)):
        sign = 1
        for a in range(n):
            for b in range(a + 1, n):
                if perm[a] > perm[b]:
                    sign = -sign
        term = Fraction(sign)
        for row, column in enumerate(perm):
            term *= matrix[row][column]
        total += term
    return total


def _decide(payload):
    point = _rats(payload["point"])
    k = len(point)
    _require(1 <= k <= 6, "R_SCHEMA")
    family = [_poly(p, k) for p in _seq(payload["family"])]
    _require(len(family) >= 2, "R_SCHEMA")
    fisher = _matrix(payload["fisher"], k, k)
    total = {}
    for poly in family:
        for exponents, coefficient in poly.items():
            total[exponents] = total.get(exponents, Fraction(0)) + coefficient
    total = {e: c for e, c in total.items() if c != 0}
    _require(total == {(0,) * k: Fraction(1)}, "R034_NOT_NORMALISED")
    values = [_evaluate(poly, point) for poly in family]
    _require(all(v > 0 for v in values), "R034_NOT_NORMALISED")
    symmetric = all(fisher[i][j] == fisher[j][i] for i in range(k) for j in range(k))
    _require(symmetric, "R034_NEGATIVE_DIRECTION")
    for size in range(1, k + 1):
        for rows in combinations(range(k), size):
            minor = [[fisher[i][j] for j in rows] for i in rows]
            _require(_det(minor) >= 0, "R034_NEGATIVE_DIRECTION")
    slopes = [[_evaluate(_derivative(poly, i), point) for i in range(k)] for poly in family]
    for i in range(k):
        for j in range(k):
            value = sum((s[i] * s[j] / p for s, p in zip(slopes, values)), Fraction(0))
            _require(fisher[i][j] == value, "R034_MATRIX_MISMATCH")
