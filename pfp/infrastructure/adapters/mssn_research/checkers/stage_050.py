"""Target checker of record for MSS-050, row 50 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 50): check Hermitian square equals identity and projector
identities. Negative instance: a matrix with nonreal eigenvalues cannot be
such an observable.

Input (closed): ``{"table": M, "projectors": [[eigenvalue, P]]}``. M and each
P are 2 x 2 tables of pairs ``[a, b]`` (a + b i, canonical rationals); each
eigenvalue is a canonical rational.

Declared input class: 2 x 2 tables over Q(i). The eigenvalues of M are real
exactly when tr(M) and det(M) are real and tr(M)^2 - 4 det(M) >= 0; that
discriminant is the refusal certificate for the level's negative (the
quarter-turn [[0, -1], [1, 0]] has discriminant -4).

Clauses, decided in this order:

- C1 ``R050_NONREAL_EIGENVALUES``: tr(M) or det(M) is not real, or the
  discriminant is negative (the level's negative);
- C2 ``R050_NOT_SELF_MIRRORED``: M differs from its mirrored transpose;
- C3 ``R050_SQUARE``: M times M is not the unit table;
- C4 ``R050_PROJECTOR``: a declared P is not idempotent or not self-mirrored;
- C5 ``R050_INCOMPLETE``: the declared P do not sum to the unit table, or two
  of them have a nonzero product;
- C6 ``R050_SPECTRAL``: M differs from the sum of eigenvalue times P.
"""

STAGE = 50
ROW_SHA256 = "sha256:f70e9e983b84d119a8733994817fdd7b97e650af83f8ea41dd62bebbc8d037e6"
FIELDS = ("projectors", "table")
CLAUSES = (
    ("C1", "R050_NONREAL_EIGENVALUES"),
    ("C2", "R050_NOT_SELF_MIRRORED"),
    ("C3", "R050_SQUARE"),
    ("C4", "R050_PROJECTOR"),
    ("C5", "R050_INCOMPLETE"),
    ("C6", "R050_SPECTRAL"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "projectors": [
        ["1/1", [[["4/5", "0/1"], ["2/5", "0/1"]], [["2/5", "0/1"], ["1/5", "0/1"]]]],
        ["-1/1", [[["1/5", "0/1"], ["-2/5", "0/1"]], [["-2/5", "0/1"], ["4/5", "0/1"]]]],
    ],
    "table": [[["0/1", "0/1"], ["-1/1", "0/1"]], [["1/1", "0/1"], ["0/1", "0/1"]]],
}
OWN_NEGATIVE_CODE = "R050_NONREAL_EIGENVALUES"
_ZERO = (Fraction(0), Fraction(0))
_ONE = (Fraction(1), Fraction(0))
_UNIT = [[_ONE, _ZERO], [_ZERO, _ONE]]


def _pair(value):
    return tuple(_rats(value, 2))


def _table(value):
    return [[_pair(entry) for entry in _seq(row, 2)] for row in _seq(value, 2)]


def _mul(x, y):
    return (x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def _add(x, y):
    return (x[0] + y[0], x[1] + y[1])


def _matmul(a, b):
    return [[_add(_mul(a[i][0], b[0][j]), _mul(a[i][1], b[1][j])) for j in range(2)] for i in range(2)]


def _matadd(a, b):
    return [[_add(a[i][j], b[i][j]) for j in range(2)] for i in range(2)]


def _mirrored(a):
    return [[(a[j][i][0], -a[j][i][1]) for j in range(2)] for i in range(2)]


def _decide(payload):
    table = _table(payload["table"])
    family = []
    for item in _seq(payload["projectors"]):
        _seq(item, 2)
        family.append((_rat(item[0]), _table(item[1])))
    trace = _add(table[0][0], table[1][1])
    det = _add(_mul(table[0][0], table[1][1]), _mul((-table[0][1][0], -table[0][1][1]), table[1][0]))
    _require(trace[1] == 0 and det[1] == 0 and trace[0] * trace[0] - 4 * det[0] >= 0, "R050_NONREAL_EIGENVALUES")
    _require(_mirrored(table) == table, "R050_NOT_SELF_MIRRORED")
    _require(_matmul(table, table) == _UNIT, "R050_SQUARE")
    for _, p in family:
        _require(_mirrored(p) == p and _matmul(p, p) == p, "R050_PROJECTOR")
    total = [[_ZERO, _ZERO], [_ZERO, _ZERO]]
    for _, p in family:
        total = _matadd(total, p)
    _require(total == _UNIT, "R050_INCOMPLETE")
    for i in range(len(family)):
        for j in range(len(family)):
            if i != j:
                _require(_matmul(family[i][1], family[j][1]) == [[_ZERO, _ZERO], [_ZERO, _ZERO]], "R050_INCOMPLETE")
    spectral = [[_ZERO, _ZERO], [_ZERO, _ZERO]]
    for value, p in family:
        spectral = _matadd(spectral, [[_mul((value, Fraction(0)), p[i][j]) for j in range(2)] for i in range(2)])
    _require(spectral == table, "R050_SPECTRAL")
