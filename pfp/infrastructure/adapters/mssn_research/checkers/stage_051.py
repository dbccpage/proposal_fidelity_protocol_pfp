"""Target checker of record for MSS-051, row 51 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 51): check projector completeness and exact outcome weights.
Negative instance: a reported weight not matching the projector norm is
rejected.

Input (closed): ``{"row": [pair], "family": [P], "weights": [rational]}``.
``row`` is v over Q(i) (pairs ``[a, b]`` of canonical rationals); each P is an
n x n table of pairs; ``weights[k]`` is the producer's reported weight of
outcome k. Nothing reported is trusted: the weight of k is recomputed as
v* P_k v = |P_k v|^2.

Declared input class: finite frames over Q(i), n = len(row) >= 1. The
quadratic weight rule is the rule checked; it is not claimed to be forced.

Clauses, decided in this order:

- C1 ``R051_NOT_UNIT``: v does not have size exactly 1;
- C2 ``R051_PROJECTOR``: some P_k is not self-mirrored or not idempotent;
- C3 ``R051_INCOMPLETE``: the P_k do not sum to the unit table, or two of them
  have a nonzero product;
- C4 ``R051_WEIGHT_MISMATCH``: the reported weights are not, entry by entry,
  the recomputed v* P_k v (the level's negative).
"""

STAGE = 51
ROW_SHA256 = "sha256:9f7c00e84439a89c06824af117f4b5f6dc5f7f8bd346e37a4593ac803c9a95a8"
FIELDS = ("family", "row", "weights")
CLAUSES = (
    ("C1", "R051_NOT_UNIT"),
    ("C2", "R051_PROJECTOR"),
    ("C3", "R051_INCOMPLETE"),
    ("C4", "R051_WEIGHT_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "family": [
        [[["4/5", "0/1"], ["2/5", "0/1"]], [["2/5", "0/1"], ["1/5", "0/1"]]],
        [[["1/5", "0/1"], ["-2/5", "0/1"]], [["-2/5", "0/1"], ["4/5", "0/1"]]],
    ],
    "row": [["1/1", "0/1"], ["0/1", "0/1"]],
    "weights": ["1/2", "1/5"],
}
OWN_NEGATIVE_CODE = "R051_WEIGHT_MISMATCH"
_ZERO = (Fraction(0), Fraction(0))


def _pair(value):
    return tuple(_rats(value, 2))


def _mul(x, y):
    return (x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def _add(x, y):
    return (x[0] + y[0], x[1] + y[1])


def _conj(x):
    return (x[0], -x[1])


def _square(value, n):
    return [[_pair(entry) for entry in _seq(row, n)] for row in _seq(value, n)]


def _matmul(a, b):
    n = len(a)
    out = []
    for i in range(n):
        line = []
        for j in range(n):
            total = _ZERO
            for k in range(n):
                total = _add(total, _mul(a[i][k], b[k][j]))
            line.append(total)
        out.append(line)
    return out


def _mirrored(a):
    n = len(a)
    return [[_conj(a[j][i]) for j in range(n)] for i in range(n)]


def _apply(a, v):
    out = []
    for line in a:
        total = _ZERO
        for entry, component in zip(line, v):
            total = _add(total, _mul(entry, component))
        out.append(total)
    return out


def _size(v):
    return sum((a * a + b * b for a, b in v), Fraction(0))


def _decide(payload):
    row = [_pair(entry) for entry in _seq(payload["row"])]
    n = len(row)
    _require(n >= 1, "R_SCHEMA")
    family = [_square(p, n) for p in _seq(payload["family"])]
    weights = _rats(payload["weights"])
    _require(family, "R_SCHEMA")
    _require(_size(row) == 1, "R051_NOT_UNIT")
    for p in family:
        _require(_mirrored(p) == p and _matmul(p, p) == p, "R051_PROJECTOR")
    unit = [[(Fraction(int(i == j)), Fraction(0)) for j in range(n)] for i in range(n)]
    total = [[_ZERO] * n for _ in range(n)]
    for p in family:
        total = [[_add(total[i][j], p[i][j]) for j in range(n)] for i in range(n)]
    _require(total == unit, "R051_INCOMPLETE")
    for i, p in enumerate(family):
        for j, q in enumerate(family):
            if i != j:
                _require(_matmul(p, q) == [[_ZERO] * n for _ in range(n)], "R051_INCOMPLETE")
    recomputed = [_size(_apply(p, row)) for p in family]
    _require(weights == recomputed, "R051_WEIGHT_MISMATCH")
