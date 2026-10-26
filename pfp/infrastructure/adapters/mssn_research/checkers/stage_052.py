"""Target checker of record for MSS-052, row 52 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 52): check conditional normalization and order-dependent
probabilities. Negative instance: independent marginal probabilities
substituted for conditionals are rejected.

Input (closed): ``{"row": [pair], "first": [P], "second": [E], "table":
[[w]], "conditionals": [[w] | null], "reverse": [[w]]}``. ``row`` is v over
Q(i); ``first`` (splits P_a) and ``second`` (splits E_b) are families of n x n
tables of pairs. The producer claims:

- ``table[a][b]``: the weight of a then b, recomputed as |E_b P_a v|^2 (the
  row is updated by the first split before the second acts);
- ``conditionals[a]``: the weights of b given a, recomputed as
  table[a][b] / p(a) with p(a) = |P_a v|^2; it must be null when p(a) = 0
  (a zero weight is never divided through);
- ``reverse[b][a]``: the weight of b then a, recomputed as |P_a E_b v|^2.

Declared input class: finite frames over Q(i); two splits, each a complete
family of mutually orthogonal self-mirrored idempotents.

Clauses, decided in this order:

- C1 ``R052_NOT_UNIT``: v does not have size exactly 1;
- C2 ``R052_PROJECTOR``: a split member is not self-mirrored or not
  idempotent;
- C3 ``R052_INCOMPLETE``: a split does not sum to the unit table, or two of
  its members have a nonzero product;
- C4 ``R052_NOT_SEQUENTIAL``: ``table`` is not the recomputed sequential
  table (the level's negative: the product of the two marginals, which for
  splits that do not commute matches neither order);
- C5 ``R052_CONDITIONAL``: a conditional row is not table[a] / p(a) (which
  sums to exactly 1), or is not null where p(a) = 0;
- C6 ``R052_REVERSE``: ``reverse`` is not the recomputed table in the other
  order.
"""

STAGE = 52
ROW_SHA256 = "sha256:a6a505b524c927c39590e2d500f44e646392b97dd5e7a24fbbe1e3fc6e4723c6"
FIELDS = ("conditionals", "first", "reverse", "row", "second", "table")
CLAUSES = (
    ("C1", "R052_NOT_UNIT"),
    ("C2", "R052_PROJECTOR"),
    ("C3", "R052_INCOMPLETE"),
    ("C4", "R052_NOT_SEQUENTIAL"),
    ("C5", "R052_CONDITIONAL"),
    ("C6", "R052_REVERSE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
_P = [[["4/5", "0/1"], ["2/5", "0/1"]], [["2/5", "0/1"], ["1/5", "0/1"]]]
_M = [[["1/5", "0/1"], ["-2/5", "0/1"]], [["-2/5", "0/1"], ["4/5", "0/1"]]]
_E0 = [[["1/1", "0/1"], ["0/1", "0/1"]], [["0/1", "0/1"], ["0/1", "0/1"]]]
_E1 = [[["0/1", "0/1"], ["0/1", "0/1"]], [["0/1", "0/1"], ["1/1", "0/1"]]]
OWN_NEGATIVE = {
    "conditionals": [["4/5", "1/5"], ["1/5", "4/5"]],
    "first": [_P, _M],
    "reverse": [["4/5", "1/5"], ["0/1", "0/1"]],
    "row": [["1/1", "0/1"], ["0/1", "0/1"]],
    "second": [_E0, _E1],
    "table": [["4/5", "0/1"], ["1/5", "0/1"]],
}
OWN_NEGATIVE_CODE = "R052_NOT_SEQUENTIAL"
_ZERO = (Fraction(0), Fraction(0))


def _pair(value):
    return tuple(_rats(value, 2))


def _mul(x, y):
    return (x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def _add(x, y):
    return (x[0] + y[0], x[1] + y[1])


def _square(value, n):
    return [[_pair(entry) for entry in _seq(row, n)] for row in _seq(value, n)]


def _matmul(a, b):
    n = len(a)
    return [[_sum(_mul(a[i][k], b[k][j]) for k in range(n)) for j in range(n)] for i in range(n)]


def _sum(items):
    total = _ZERO
    for item in items:
        total = _add(total, item)
    return total


def _mirrored(a):
    n = len(a)
    return [[(a[j][i][0], -a[j][i][1]) for j in range(n)] for i in range(n)]


def _apply(a, v):
    return [_sum(_mul(entry, component) for entry, component in zip(line, v)) for line in a]


def _size(v):
    return sum((a * a + b * b for a, b in v), Fraction(0))


def _split(value, n):
    family = [_square(p, n) for p in _seq(value)]
    _require(family, "R_SCHEMA")
    return family


def _weights(value, rows, columns):
    return [_rats(line, columns) for line in _seq(value, rows)]


def _decide(payload):
    row = [_pair(entry) for entry in _seq(payload["row"])]
    n = len(row)
    _require(n >= 1, "R_SCHEMA")
    first, second = _split(payload["first"], n), _split(payload["second"], n)
    _require(_size(row) == 1, "R052_NOT_UNIT")
    unit = [[(Fraction(int(i == j)), Fraction(0)) for j in range(n)] for i in range(n)]
    zero = [[_ZERO] * n for _ in range(n)]
    for family in (first, second):
        for p in family:
            _require(_mirrored(p) == p and _matmul(p, p) == p, "R052_PROJECTOR")
    for family in (first, second):
        total = zero
        for p in family:
            total = [[_add(total[i][j], p[i][j]) for j in range(n)] for i in range(n)]
        _require(total == unit, "R052_INCOMPLETE")
        for i, p in enumerate(family):
            for j, q in enumerate(family):
                _require(i == j or _matmul(p, q) == zero, "R052_INCOMPLETE")
    table = _weights(payload["table"], len(first), len(second))
    reverse = _weights(payload["reverse"], len(second), len(first))
    conditionals = [None if line is None else _rats(line, len(second)) for line in _seq(payload["conditionals"], len(first))]
    sequential = [[_size(_apply(e, _apply(p, row))) for e in second] for p in first]
    _require(table == sequential, "R052_NOT_SEQUENTIAL")
    for a, p in enumerate(first):
        weight = _size(_apply(p, row))
        if weight == 0:
            _require(conditionals[a] is None, "R052_CONDITIONAL")
        else:
            _require(conditionals[a] == [w / weight for w in sequential[a]], "R052_CONDITIONAL")
            _require(sum(conditionals[a], Fraction(0)) == 1, "R052_CONDITIONAL")
    other = [[_size(_apply(p, _apply(e, row))) for p in first] for e in second]
    _require(reverse == other, "R052_REVERSE")
