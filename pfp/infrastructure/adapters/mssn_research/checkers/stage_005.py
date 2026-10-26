"""Target checker of record for MSS-005, row 5 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 5): check complete lengths and a positive definite Gram
matrix; verify incidence before curvature. Negative instance: an indefinite
Gram matrix with positive full determinant is rejected.

Input (closed): ``{"vertices": [nat], "cells": [[nat]], "squared_lengths":
[[u, v, "num/den"]], "hinges": [{"hinge": [nat], "cells": [[nat]],
"deficit": "num/den"}]}``. Squared lengths are exact rationals, keyed by the
edge ``u < v``. A hinge's deficit is in turns (a full turn is 1).

Clauses, all recomputed over the rationals:

- C1 ``R005_INCOMPLETE_LENGTHS``: an edge of some cell has no squared length;
- C2 ``R005_NONPOSITIVE_LENGTH``: a squared length is not positive;
- C3 ``R005_INDEFINITE_GRAM``: some leading principal minor of a cell's Gram
  matrix (based at its first vertex) is not positive. Sylvester's criterion,
  so a positive full determinant alone never passes;
- C4 ``R005_INCIDENCE``: a hinge record lists a cell that is not declared or
  does not contain the hinge. Checked for every listed cell before any angle
  is computed;
- C5 ``R005_HINGE_NOT_CODIM_TWO``: a hinge is not of codimension two in a
  listed cell;
- C6 ``R005_IRRATIONAL_ANGLE``: an angle at the hinge is not a rational part of
  a turn, so no exact deficit exists; it is refused, never approximated;
- C7 ``R005_DEFICIT_MISMATCH``: the declared deficit differs from one turn
  minus the recomputed angles.

Declared class and limit: curvature is computed exactly for vertex hinges in
two-dimensional cells, where an angle with cos^2 in {0, 1/4, 1/2, 3/4} is a
rational part of a turn. A hinge in a cell of any other dimension is refused
with ``R005_UNSUPPORTED_HINGE``: that is an honest limit, not a pass.
"""

from itertools import combinations

STAGE = 5
ROW_SHA256 = "sha256:69dae0261de5ec9ed3ab8cf2c8a1131c7269be89e5d4b867aa7f3e92cc1a7314"
FIELDS = ("cells", "hinges", "squared_lengths", "vertices")
CLAUSES = (
    ("C1", "R005_INCOMPLETE_LENGTHS"),
    ("C2", "R005_NONPOSITIVE_LENGTH"),
    ("C3", "R005_INDEFINITE_GRAM"),
    ("C4", "R005_INCIDENCE"),
    ("C5", "R005_HINGE_NOT_CODIM_TWO"),
    ("C6", "R005_IRRATIONAL_ANGLE"),
    ("C7", "R005_DEFICIT_MISMATCH"),
)
EXTRA_CODES = ("R005_UNSUPPORTED_HINGE",)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES) + EXTRA_CODES
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "cells": [[0, 1, 2, 3]],
    "hinges": [],
    "squared_lengths": [
        [0, 1, "9/1"], [0, 2, "1/1"], [0, 3, "9/1"], [1, 2, "2/1"], [1, 3, "38/1"], [2, 3, "18/1"],
    ],
    "vertices": [0, 1, 2, 3],
}
OWN_NEGATIVE_CODE = "R005_INDEFINITE_GRAM"

# (cos^2, sign of cos) -> the angle as a part of one turn.
_TURNS = {
    (Fraction(1, 4), 1): Fraction(1, 6),
    (Fraction(1, 4), -1): Fraction(1, 3),
    (Fraction(1, 2), 1): Fraction(1, 8),
    (Fraction(1, 2), -1): Fraction(3, 8),
    (Fraction(3, 4), 1): Fraction(1, 12),
    (Fraction(3, 4), -1): Fraction(5, 12),
}


def _det(matrix):
    rows = [list(row) for row in matrix]
    size, out = len(rows), Fraction(1)
    for col in range(size):
        pivot = next((r for r in range(col, size) if rows[r][col] != 0), None)
        if pivot is None:
            return Fraction(0)
        if pivot != col:
            rows[col], rows[pivot] = rows[pivot], rows[col]
            out = -out
        out *= rows[col][col]
        for r in range(col + 1, size):
            factor = rows[r][col] / rows[col][col]
            rows[r] = [x - factor * y for x, y in zip(rows[r], rows[col])]
    return out


def _angle(side_a, side_b, opposite):
    """The angle between two sides, as a part of a turn, or refused."""
    numerator = side_a + side_b - opposite
    if numerator == 0:
        return Fraction(1, 4)
    cos_squared = numerator * numerator / (4 * side_a * side_b)
    key = (cos_squared, 1 if numerator > 0 else -1)
    _require(key in _TURNS, "R005_IRRATIONAL_ANGLE")
    return _TURNS[key]


def _decide(payload):
    vertices = [_nat(v) for v in _seq(payload["vertices"])]
    _require(len(set(vertices)) == len(vertices), "R_SCHEMA")
    known = set(vertices)
    lengths = {}
    for entry in _seq(payload["squared_lengths"]):
        _seq(entry, 3)
        low, high, value = _nat(entry[0]), _nat(entry[1]), _rat(entry[2])
        _require(low < high and low in known and high in known and (low, high) not in lengths, "R_SCHEMA")
        _require(value > 0, "R005_NONPOSITIVE_LENGTH")
        lengths[(low, high)] = value

    def squared(a, b):
        return Fraction(0) if a == b else lengths[(min(a, b), max(a, b))]

    cells = []
    for cell in _seq(payload["cells"]):
        verts = tuple(_nat(v) for v in _seq(cell))
        _require(len(verts) >= 2 and list(verts) == sorted(set(verts)) and set(verts) <= known, "R_SCHEMA")
        _require(verts not in cells, "R_SCHEMA")
        for pair in combinations(verts, 2):
            _require(pair in lengths, "R005_INCOMPLETE_LENGTHS")
        cells.append(verts)
    for verts in cells:
        base, rest = verts[0], verts[1:]
        gram = [[(squared(base, a) + squared(base, b) - squared(a, b)) / 2 for b in rest] for a in rest]
        for k in range(1, len(rest) + 1):
            _require(_det([row[:k] for row in gram[:k]]) > 0, "R005_INDEFINITE_GRAM")
    declared = set(cells)
    for record in _seq(payload["hinges"]):
        _require(isinstance(record, dict) and set(record) == {"cells", "deficit", "hinge"}, "R_SCHEMA")
        hinge = [_nat(v) for v in _seq(record["hinge"])]
        around = [tuple(_nat(v) for v in _seq(cell)) for cell in _seq(record["cells"])]
        _require(around and len(set(around)) == len(around) and len(set(hinge)) == len(hinge), "R_SCHEMA")
        for cell in around:
            _require(cell in declared and set(hinge) <= set(cell), "R005_INCIDENCE")
        for cell in around:
            _require(len(hinge) == len(cell) - 2, "R005_HINGE_NOT_CODIM_TWO")
        _require(all(len(cell) == 3 for cell in around), "R005_UNSUPPORTED_HINGE")
        total = Fraction(0)
        for cell in around:
            apex = hinge[0]
            a, b = [v for v in cell if v != apex]
            total += _angle(squared(apex, a), squared(apex, b), squared(a, b))
        _require(_rat(record["deficit"]) == 1 - total, "R005_DEFICIT_MISMATCH")
