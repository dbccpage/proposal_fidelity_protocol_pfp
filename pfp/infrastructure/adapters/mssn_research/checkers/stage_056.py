"""Target checker of record for MSS-056, row 56 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 56): check the reduced (one-side) table is positive
semidefinite with trace one. Negative instance: a trace-changing reduction is
rejected.

Input (closed): ``{"shape": [m, n], "row": [pair], "reduced": R}``. ``row``
is a joined unit row s of an m x n frame (pairs ``[a, b]``, a + b i; slot
(i, j) at n * i + j), standing for the joined table s s*. ``reduced`` is the
producer's m x m one-side reduction. The checker recomputes it as
R[i][j] = sum_k s[n * i + k] * mirror(s[n * j + k]), the sum over the far
slots.

Declared input class: joined tables of the form s s* for a unit row s over
Q(i) (a mixed joined table is not an input of this checker). Positive
semidefiniteness of the claimed table is decided exactly by symmetric
elimination with nonnegative pivots: a zero pivot followed by a nonzero entry
in its column refuses.

Clauses, decided in this order:

- C1 ``R056_NOT_UNIT``: s does not have size exactly 1;
- C2 ``R056_TRACE``: the claimed reduced table does not have trace exactly 1
  (the level's negative);
- C3 ``R056_NOT_PSD``: the claimed reduced table is not self-mirrored or not
  positive semidefinite;
- C4 ``R056_MISMATCH``: the claimed reduced table is not the recomputed one.
"""

STAGE = 56
ROW_SHA256 = "sha256:8dbc7723ac5964b572fad9b549480e505076435865a9ae9b4254691f0ecaad9f"
FIELDS = ("reduced", "row", "shape")
CLAUSES = (
    ("C1", "R056_NOT_UNIT"),
    ("C2", "R056_TRACE"),
    ("C3", "R056_NOT_PSD"),
    ("C4", "R056_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "reduced": [[["1/4", "0/1"], ["0/1", "0/1"]], [["0/1", "0/1"], ["1/2", "0/1"]]],
    "row": [["1/2", "0/1"], ["1/2", "0/1"], ["1/2", "0/1"], ["-1/2", "0/1"]],
    "shape": [2, 2],
}
OWN_NEGATIVE_CODE = "R056_TRACE"
_ZERO = (Fraction(0), Fraction(0))


def _pair(value):
    return tuple(_rats(value, 2))


def _mul(x, y):
    return (x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def _sub(x, y):
    return (x[0] - y[0], x[1] - y[1])


def _conj(x):
    return (x[0], -x[1])


def _psd(table):
    a = [list(line) for line in table]
    size = len(a)
    for k in range(size):
        pivot = a[k][k][0]
        if pivot < 0:
            return False
        if pivot == 0:
            if any(a[i][k] != _ZERO for i in range(k + 1, size)):
                return False
            continue
        for i in range(k + 1, size):
            factor = (a[i][k][0] / pivot, a[i][k][1] / pivot)
            for j in range(k + 1, size):
                a[i][j] = _sub(a[i][j], _mul(factor, a[k][j]))
    return True


def _decide(payload):
    shape = _seq(payload["shape"], 2)
    m, n = _nat(shape[0]), _nat(shape[1])
    _require(m >= 1 and n >= 1, "R_SCHEMA")
    row = [_pair(entry) for entry in _seq(payload["row"], m * n)]
    reduced = [[_pair(entry) for entry in _seq(line, m)] for line in _seq(payload["reduced"], m)]
    _require(sum((a * a + b * b for a, b in row), Fraction(0)) == 1, "R056_NOT_UNIT")
    _require(sum((reduced[i][i][0] for i in range(m)), Fraction(0)) == 1, "R056_TRACE")
    _require(all(reduced[i][i][1] == 0 for i in range(m)), "R056_NOT_PSD")
    _require(all(reduced[i][j] == _conj(reduced[j][i]) for i in range(m) for j in range(m)), "R056_NOT_PSD")
    _require(_psd(reduced), "R056_NOT_PSD")
    recomputed = []
    for i in range(m):
        line = []
        for j in range(m):
            total = _ZERO
            for k in range(n):
                x = _mul(row[n * i + k], _conj(row[n * j + k]))
                total = (total[0] + x[0], total[1] + x[1])
            line.append(total)
        recomputed.append(line)
    _require(reduced == recomputed, "R056_MISMATCH")
