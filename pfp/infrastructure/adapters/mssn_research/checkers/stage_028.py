"""Target checker of record for MSS-028, row 28 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 28): check both inverse homotopies before any univalence use.
Negative instance: one-sided inverse asserted as equivalence is rejected.

Input (closed): ``{"source": {"dims": [nat], "d": [matrix]}, "target":
{...}, "f": [matrix], "g": [matrix], "h": [matrix], "k": [matrix]}``.
Matrices are lists of rows of canonical rationals. A complex lives in degrees
0..top, with ``dims[i]`` the dimension in degree i and ``d[i-1]`` the
differential from degree i to degree i-1 (a dims[i-1] x dims[i] matrix).
``f`` and ``g`` are chain maps source -> target and back, one matrix per
degree. ``h`` and ``k`` are the two homotopies, one matrix per degree
0..top-1, raising degree by one: h on the source, k on the target.

Declared input class: bounded chain complexes of finite-dimensional rational
vector spaces with the same top degree, and a declared homotopy equivalence.
The checker replays the declared witnesses exactly over the rationals; it
does not search for homotopies. The groupoid and univalence readings of the
row are not decided here.

Clauses, each recomputed by matrix arithmetic:

- C1 ``R028_NOT_A_COMPLEX``: two consecutive differentials of the source or
  target do not compose to zero;
- C2 ``R028_NOT_A_CHAIN_MAP``: f or g does not commute with the
  differentials;
- C3 ``R028_LEFT_HOMOTOPY``: g f - 1 is not d h + h d in some degree;
- C4 ``R028_RIGHT_HOMOTOPY``: f g - 1 is not d k + k d in some degree (the
  level's negative: a one-sided inverse).
"""

STAGE = 28
ROW_SHA256 = "sha256:897d47fa5cca6ba9c09050c21941aeda6c78d9e238b1a1ba0333c89f5b3a7fbf"
FIELDS = ("f", "g", "h", "k", "source", "target")
CLAUSES = (
    ("C1", "R028_NOT_A_COMPLEX"),
    ("C2", "R028_NOT_A_CHAIN_MAP"),
    ("C3", "R028_LEFT_HOMOTOPY"),
    ("C4", "R028_RIGHT_HOMOTOPY"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "f": [[["1/1"], ["0/1"]]],
    "g": [[["1/1", "0/1"]]],
    "h": [],
    "k": [],
    "source": {"d": [], "dims": [1]},
    "target": {"d": [], "dims": [2]},
}
OWN_NEGATIVE_CODE = "R028_RIGHT_HOMOTOPY"


def _shaped(value, rows, columns):
    out = [_rats(row, columns) for row in _seq(value, rows)]
    return out


def _mul(a, b, rows, inner, columns):
    return [[sum((a[i][t] * b[t][j] for t in range(inner)), Fraction(0)) for j in range(columns)] for i in range(rows)]


def _zero(rows, columns):
    return [[Fraction(0)] * columns for _ in range(rows)]


def _add(a, b):
    return [[x + y for x, y in zip(ra, rb)] for ra, rb in zip(a, b)]


def _complex(value):
    _require(isinstance(value, dict) and set(value) == {"d", "dims"}, "R_SCHEMA")
    dims = [_nat(x) for x in _seq(value["dims"])]
    _require(dims, "R_SCHEMA")
    top = len(dims) - 1
    d = [_shaped(m, dims[i], dims[i + 1]) for i, m in enumerate(_seq(value["d"], top))]
    return dims, d


def _decide(payload):
    cdims, cd = _complex(payload["source"])
    ddims, dd = _complex(payload["target"])
    _require(len(cdims) == len(ddims), "R_SCHEMA")
    top = len(cdims) - 1
    f = [_shaped(m, ddims[i], cdims[i]) for i, m in enumerate(_seq(payload["f"], top + 1))]
    g = [_shaped(m, cdims[i], ddims[i]) for i, m in enumerate(_seq(payload["g"], top + 1))]
    h = [_shaped(m, cdims[i + 1], cdims[i]) for i, m in enumerate(_seq(payload["h"], top))]
    k = [_shaped(m, ddims[i + 1], ddims[i]) for i, m in enumerate(_seq(payload["k"], top))]
    for dims, d in ((cdims, cd), (ddims, dd)):
        for i in range(1, top):
            product = _mul(d[i - 1], d[i], dims[i - 1], dims[i], dims[i + 1])
            _require(product == _zero(dims[i - 1], dims[i + 1]), "R028_NOT_A_COMPLEX")
    for i in range(1, top + 1):
        left = _mul(dd[i - 1], f[i], ddims[i - 1], ddims[i], cdims[i])
        right = _mul(f[i - 1], cd[i - 1], ddims[i - 1], cdims[i - 1], cdims[i])
        _require(left == right, "R028_NOT_A_CHAIN_MAP")
        left = _mul(cd[i - 1], g[i], cdims[i - 1], cdims[i], ddims[i])
        right = _mul(g[i - 1], dd[i - 1], cdims[i - 1], ddims[i - 1], ddims[i])
        _require(left == right, "R028_NOT_A_CHAIN_MAP")
    for (dims, d, there, back, hom, code) in (
        (cdims, cd, f, g, h, "R028_LEFT_HOMOTOPY"),
        (ddims, dd, g, f, k, "R028_RIGHT_HOMOTOPY"),
    ):
        other = ddims if dims is cdims else cdims
        for i in range(top + 1):
            n = dims[i]
            loop = _mul(back[i], there[i], n, other[i], n)
            loop = [[x - (1 if r == c else 0) for c, x in enumerate(row)] for r, row in enumerate(loop)]
            total = _zero(n, n)
            if i < top:
                total = _add(total, _mul(d[i], hom[i], n, dims[i + 1], n))
            if i > 0:
                total = _add(total, _mul(hom[i - 1], d[i - 1], n, dims[i - 1], n))
            _require(loop == total, code)
