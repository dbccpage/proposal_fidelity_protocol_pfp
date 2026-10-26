"""Target checker of record for MSS-054, row 54 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 54): check rank of reshaped pure-state amplitude matrix.
Negative instance: a product vector cannot claim rank two.

Input (closed): ``{"shape": [m, n], "row": [pair], "rank": r}``. ``row`` is
a joined row of an m x n frame (pairs ``[a, b]``, a + b i, canonical
rationals), slot (i, j) at index n * i + j. It is reshaped into the m x n
table C with C[i][j] = row[n * i + j], and the rank of C is computed exactly
by Gaussian elimination over Q(i). A nonzero row has rank 1 exactly when it
is a product of two factor rows.

Declared input class: unit rows over Q(i) on m x n frames with m, n >= 1.
No meaning beyond the rank of the reshaped table is attached to a rank.

Clauses, decided in this order:

- C1 ``R054_SHAPE``: m * n is not the number of slots of the row;
- C2 ``R054_NOT_UNIT``: the row does not have size exactly 1;
- C3 ``R054_RANK``: the claimed rank is not the recomputed rank (the level's
  negative: the product row (3/5, 0, 4/5, 0) claiming rank 2).
"""

STAGE = 54
ROW_SHA256 = "sha256:d7b77bd40badc7d6babdc31e8b65b473174ebb39c5d76711dba836636d02ee2f"
FIELDS = ("rank", "row", "shape")
CLAUSES = (
    ("C1", "R054_SHAPE"),
    ("C2", "R054_NOT_UNIT"),
    ("C3", "R054_RANK"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "rank": 2,
    "row": [["3/5", "0/1"], ["0/1", "0/1"], ["4/5", "0/1"], ["0/1", "0/1"]],
    "shape": [2, 2],
}
OWN_NEGATIVE_CODE = "R054_RANK"
_ZERO = (Fraction(0), Fraction(0))


def _pair(value):
    return tuple(_rats(value, 2))


def _mul(x, y):
    return (x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def _sub(x, y):
    return (x[0] - y[0], x[1] - y[1])


def _inv(x):
    norm = x[0] * x[0] + x[1] * x[1]
    return (x[0] / norm, -x[1] / norm)


def _rank(table):
    rows = [list(line) for line in table]
    rank, columns = 0, len(rows[0]) if rows else 0
    for column in range(columns):
        pivot = next((r for r in range(rank, len(rows)) if rows[r][column] != _ZERO), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        scale = _inv(rows[rank][column])
        for r in range(len(rows)):
            if r != rank and rows[r][column] != _ZERO:
                factor = _mul(rows[r][column], scale)
                rows[r] = [_sub(x, _mul(factor, y)) for x, y in zip(rows[r], rows[rank])]
        rank += 1
    return rank


def _decide(payload):
    shape = _seq(payload["shape"], 2)
    m, n = _nat(shape[0]), _nat(shape[1])
    _require(m >= 1 and n >= 1, "R_SCHEMA")
    row = [_pair(entry) for entry in _seq(payload["row"])]
    claimed = _nat(payload["rank"])
    _require(m * n == len(row), "R054_SHAPE")
    _require(sum((a * a + b * b for a, b in row), Fraction(0)) == 1, "R054_NOT_UNIT")
    table = [[row[n * i + j] for j in range(n)] for i in range(m)]
    _require(claimed == _rank(table), "R054_RANK")
