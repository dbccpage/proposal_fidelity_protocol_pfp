"""Target checker of record for MSS-057, row 57 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 57): check conjugate transpose times step equals identity.
Negative instance: a norm-changing step cannot claim size-keeping evolution.

Input (closed): ``{"table": U, "rows": [[v, image]]}``. U is an n x n table
of pairs ``[a, b]`` (a + b i, canonical rationals). Each carried test row v
comes with the producer's claimed image U v.

Declared input class: static n x n tables over Q(i), n >= 1. The table is
data, not a native step. Size-keeping is decided on the whole table
(mirror(U)^T U = I, and U mirror(U)^T = I), never by sampling rows: diag(1, 2)
keeps the size of (1, 0) and is still refused.

Clauses, decided in this order:

- C1 ``R057_NOT_SIZE_KEEPING``: mirror(U)^T U or U mirror(U)^T is not the
  unit table (the level's negative: the shear [[1, 1], [0, 1]]);
- C2 ``R057_IMAGE``: a claimed image differs from the recomputed U v.
"""

STAGE = 57
ROW_SHA256 = "sha256:2a94ee136bfab6d6c411ec1bc4f3044ab056d7e973b11768f1ab688fdd34fa71"
FIELDS = ("rows", "table")
CLAUSES = (
    ("C1", "R057_NOT_SIZE_KEEPING"),
    ("C2", "R057_IMAGE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "rows": [[[["0/1", "0/1"], ["1/1", "0/1"]], [["1/1", "0/1"], ["1/1", "0/1"]]]],
    "table": [[["1/1", "0/1"], ["1/1", "0/1"]], [["0/1", "0/1"], ["1/1", "0/1"]]],
}
OWN_NEGATIVE_CODE = "R057_NOT_SIZE_KEEPING"
_ZERO = (Fraction(0), Fraction(0))


def _pair(value):
    return tuple(_rats(value, 2))


def _mul(x, y):
    return (x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def _add(x, y):
    return (x[0] + y[0], x[1] + y[1])


def _dot(xs, ys):
    total = _ZERO
    for x, y in zip(xs, ys):
        total = _add(total, _mul(x, y))
    return total


def _decide(payload):
    table = [[_pair(entry) for entry in _seq(line)] for line in _seq(payload["table"])]
    n = len(table)
    _require(n >= 1 and all(len(line) == n for line in table), "R_SCHEMA")
    rows = []
    for item in _seq(payload["rows"]):
        _seq(item, 2)
        rows.append(([_pair(e) for e in _seq(item[0], n)], [_pair(e) for e in _seq(item[1], n)]))
    _require(rows, "R_SCHEMA")
    mirror = [[(table[j][i][0], -table[j][i][1]) for j in range(n)] for i in range(n)]
    unit = [[(Fraction(int(i == j)), Fraction(0)) for j in range(n)] for i in range(n)]
    left = [[_dot(mirror[i], [table[k][j] for k in range(n)]) for j in range(n)] for i in range(n)]
    right = [[_dot(table[i], [mirror[k][j] for k in range(n)]) for j in range(n)] for i in range(n)]
    _require(left == unit and right == unit, "R057_NOT_SIZE_KEEPING")
    for v, image in rows:
        _require([_dot(line, v) for line in table] == image, "R057_IMAGE")
