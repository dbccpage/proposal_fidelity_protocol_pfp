"""Target checker of record for MSS-018, row 18 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 18): reconstruct c and check exact harmonic coexact
orthogonality. Negative instance: a zero residual field without matrices is
rejected.

Input (closed): ``{"d0": [[q]], "d1": [[q]], "cochain": [q], "potential": [q],
"copotential": [q], "harmonic": [q]}``. ``d0`` is m x n (one row per edge),
``d1`` is k x m (one row per 2-cell). The split is taken as the witnesses p,
q, h; the checker computes the exact part d0 p and the coexact part d1^T q
itself, so a split whose parts merely sum to c and are pairwise orthogonal
proves nothing (the hollow ``verify_l2_hodge`` defect, W2-DA order 018).

Clauses, over the rationals with the standard inner product:

- C1 ``R018_NO_MATRICES``: ``d0`` is absent or empty (the negative);
- C2 ``R018_BOARD_INVALID``: d1 d0 != 0, so no split is defined;
- C3 ``R018_NOT_HARMONIC``: d0^T h != 0 or d1 h != 0;
- C4 ``R018_RECONSTRUCTION``: d0 p + h + d1^T q != c.

``R018_NOT_ORTHOGONAL`` is recomputed as well, but it follows from C2 and C3,
so no payload that passes them can reach it; it is not claimed as a clause.
"""

STAGE = 18
ROW_SHA256 = "sha256:0c28f53b610fd5325cd223fb5313e20c8f25136207ef855a495699aa702fa672"
FIELDS = ("cochain", "copotential", "d0", "d1", "harmonic", "potential")
CLAUSES = (
    ("C1", "R018_NO_MATRICES"),
    ("C2", "R018_BOARD_INVALID"),
    ("C3", "R018_NOT_HARMONIC"),
    ("C4", "R018_RECONSTRUCTION"),
)
EXTRA_CODES = ("R018_NOT_ORTHOGONAL",)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES) + EXTRA_CODES
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "cochain": ["1/1", "0/1", "0/1", "0/1", "0/1"],
    "copotential": [],
    "d0": [],
    "d1": [],
    "harmonic": ["0/1", "0/1", "0/1", "0/1", "0/1"],
    "potential": [],
}
OWN_NEGATIVE_CODE = "R018_NO_MATRICES"


def _apply(matrix, vector):
    return [sum((a * b for a, b in zip(row, vector)), Fraction(0)) for row in matrix]


def _transpose(matrix, columns):
    return [[row[j] for row in matrix] for j in range(columns)]


def _dot(u, v):
    return sum((a * b for a, b in zip(u, v)), Fraction(0))


def _decide(payload):
    _require(payload["d0"] is not None and payload["d0"] != [] and payload["d1"] is not None, "R018_NO_MATRICES")
    d0 = _matrix(payload["d0"])
    m, n = len(d0), len(d0[0])
    _require(n >= 1, "R_SCHEMA")
    d1 = _matrix(payload["d1"], columns=m)
    k = len(d1)
    c = _rats(payload["cochain"], m)
    p = _rats(payload["potential"], n)
    q = _rats(payload["copotential"], k)
    h = _rats(payload["harmonic"], m)
    for column in _transpose(d0, n):
        _require(all(value == 0 for value in _apply(d1, column)), "R018_BOARD_INVALID")
    harmonic = all(v == 0 for v in _apply(_transpose(d0, n), h)) and all(v == 0 for v in _apply(d1, h))
    _require(harmonic, "R018_NOT_HARMONIC")
    exact = _apply(d0, p)
    coexact = _apply(_transpose(d1, m), q) if k else [Fraction(0)] * m
    _require([a + b + e for a, b, e in zip(exact, h, coexact)] == c, "R018_RECONSTRUCTION")
    parts = (exact, h, coexact)
    for i in range(3):
        for j in range(i + 1, 3):
            _require(_dot(parts[i], parts[j]) == 0, "R018_NOT_ORTHOGONAL")
