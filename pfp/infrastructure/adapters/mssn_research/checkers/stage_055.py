"""Target checker of record for MSS-055, row 55 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 55): recompute local marginal across remote choices.
Negative instance: different local marginals without a postselection flag
are rejected.

Input (closed): ``{"shape": [m, n], "row": [pair], "near": [E], "far":
[[F]], "table": [[[w]]], "selection": null | [[b]]}``. ``row`` is a joined row
s of an m x n frame (pairs ``[a, b]``, a + b i; slot (i, j) at n * i + j).
``near`` is one split of the near factor (m x m tables); ``far[y]`` is the far
split chosen by far choice y (n x n tables). ``table[y][a][b]`` is the
producer's joint weight of near outcome a and far outcome b under choice y.
``selection`` is null, or declares for each choice y the far outcomes kept.

The checker recomputes every joint weight as |(E_a (x) F_b^y) s|^2. Under a
declared selection the recomputed table keeps only the listed b and is
renormalized per choice; its near marginals may then move with y, and the
table is accepted only as that declared selection, never as a blind one.

Declared input class: joined rows over Q(i); one near split; finitely many
far choices, each a complete split.

Clauses, decided in this order:

- C1 ``R055_SPLIT``: a split member is not a self-mirrored idempotent, or a
  split is not complete and mutually orthogonal;
- C2 ``R055_SIGNALLING``: with no selection declared, the near marginals
  sum_b table[y][a][b] of the claimed table differ between two far choices
  (the level's negative);
- C3 ``R055_TABLE_MISMATCH``: the claimed table is not the recomputed one
  (after the declared selection, if any).
"""

STAGE = 55
ROW_SHA256 = "sha256:d85c406d5fa7ecdf6f125fb9b1d7557b1e3cf7c0777594468bd8d0dd61d609ea"
FIELDS = ("far", "near", "row", "selection", "shape", "table")
CLAUSES = (
    ("C1", "R055_SPLIT"),
    ("C2", "R055_SIGNALLING"),
    ("C3", "R055_TABLE_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
_E0 = [[["1/1", "0/1"], ["0/1", "0/1"]], [["0/1", "0/1"], ["0/1", "0/1"]]]
_E1 = [[["0/1", "0/1"], ["0/1", "0/1"]], [["0/1", "0/1"], ["1/1", "0/1"]]]
_P = [[["4/5", "0/1"], ["2/5", "0/1"]], [["2/5", "0/1"], ["1/5", "0/1"]]]
_M = [[["1/5", "0/1"], ["-2/5", "0/1"]], [["-2/5", "0/1"], ["4/5", "0/1"]]]
OWN_NEGATIVE = {
    "far": [[_E0, _E1], [_P, _M]],
    "near": [_E0, _E1],
    "row": [["3/5", "0/1"], ["0/1", "0/1"], ["0/1", "0/1"], ["4/5", "0/1"]],
    "selection": None,
    "shape": [2, 2],
    "table": [[["9/25", "0/1"], ["0/1", "16/25"]], [["1/4", "1/4"], ["1/4", "1/4"]]],
}
OWN_NEGATIVE_CODE = "R055_SIGNALLING"
_ZERO = (Fraction(0), Fraction(0))


def _pair(value):
    return tuple(_rats(value, 2))


def _mul(x, y):
    return (x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def _add(x, y):
    return (x[0] + y[0], x[1] + y[1])


def _sum(items):
    total = _ZERO
    for item in items:
        total = _add(total, item)
    return total


def _square(value, n):
    return [[_pair(entry) for entry in _seq(row, n)] for row in _seq(value, n)]


def _matmul(a, b):
    n = len(a)
    return [[_sum(_mul(a[i][k], b[k][j]) for k in range(n)) for j in range(n)] for i in range(n)]


def _is_split(family):
    n = len(family[0])
    zero = [[_ZERO] * n for _ in range(n)]
    unit = [[(Fraction(int(i == j)), Fraction(0)) for j in range(n)] for i in range(n)]
    total = zero
    for p in family:
        if [[(p[j][i][0], -p[j][i][1]) for j in range(n)] for i in range(n)] != p or _matmul(p, p) != p:
            return False
        total = [[_add(total[i][j], p[i][j]) for j in range(n)] for i in range(n)]
    pairs = all(i == j or _matmul(p, q) == zero for i, p in enumerate(family) for j, q in enumerate(family))
    return total == unit and pairs


def _decide(payload):
    shape = _seq(payload["shape"], 2)
    m, n = _nat(shape[0]), _nat(shape[1])
    _require(m >= 1 and n >= 1, "R_SCHEMA")
    row = [_pair(entry) for entry in _seq(payload["row"], m * n)]
    near = [_square(p, m) for p in _seq(payload["near"])]
    far = [[_square(p, n) for p in _seq(family)] for family in _seq(payload["far"])]
    _require(near and far and all(far), "R_SCHEMA")
    table = [[_rats(line, len(far[y])) for line in _seq(block, len(near))] for y, block in enumerate(_seq(payload["table"], len(far)))]
    selection = payload["selection"]
    if selection is not None:
        selection = [[_nat(b) for b in _seq(kept)] for kept in _seq(selection, len(far))]
        _require(all(kept and all(b < len(far[y]) for b in kept) for y, kept in enumerate(selection)), "R_SCHEMA")
    _require(_is_split(near) and all(_is_split(family) for family in far), "R055_SPLIT")
    if selection is None:
        marginals = [[sum(line, Fraction(0)) for line in block] for block in table]
        _require(all(marginal == marginals[0] for marginal in marginals), "R055_SIGNALLING")
    recomputed = []
    for y, family in enumerate(far):
        block = []
        for e in near:
            line = []
            for f in family:
                image = [
                    _sum(_mul(_mul(e[i][k], f[j][l]), row[n * k + l]) for k in range(m) for l in range(n))
                    for i in range(m)
                    for j in range(n)
                ]
                line.append(sum((a * a + b * b for a, b in image), Fraction(0)))
            block.append(line)
        if selection is not None:
            kept = set(selection[y])
            block = [[w if b in kept else Fraction(0) for b, w in enumerate(line)] for line in block]
            total = sum((w for line in block for w in line), Fraction(0))
            _require(total > 0, "R_SCHEMA")
            block = [[w / total for w in line] for line in block]
        recomputed.append(block)
    _require(table == recomputed, "R055_TABLE_MISMATCH")
