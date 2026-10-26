"""Target checker of record for MSS-003, row 3 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 3): check n+1 distinct vertices and all implied subfaces.
Negative instance: a two-simplex with two vertices is rejected.

Input (closed): ``{"vertices": [nat], "cells": [{"dim": nat >= 1, "verts":
[nat]}]}``. Vertices are the 0-cells; every listed cell has dimension >= 1.

Clauses, recomputed from the vertex lists (the declared ``dim`` is compared,
never trusted):

- C1 ``R003_ARITY``: a cell of dimension n does not have n+1 vertices;
- C2 ``R003_REPEATED_VERTEX``: a cell repeats a vertex;
- C3 ``R003_ABSENT_VERTEX``: a cell names an undeclared vertex;
- C4 ``R003_UNORDERED``: a cell's vertices are not strictly ascending;
- C5 ``R003_MISSING_SUBFACE``: a facet of a cell of dimension >= 2 is not a
  cell. Closure under facets gives closure under all subfaces, by induction on
  dimension; 0-faces are covered by C3.
"""

STAGE = 3
ROW_SHA256 = "sha256:0e88b93eaa99cb83c257179dcf84e160f972c5b964161d1fdbaf472cf8f16acb"
FIELDS = ("cells", "vertices")
CLAUSES = (
    ("C1", "R003_ARITY"),
    ("C2", "R003_REPEATED_VERTEX"),
    ("C3", "R003_ABSENT_VERTEX"),
    ("C4", "R003_UNORDERED"),
    ("C5", "R003_MISSING_SUBFACE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {"cells": [{"dim": 2, "verts": [0, 1]}], "vertices": [0, 1]}
OWN_NEGATIVE_CODE = "R003_ARITY"


def _decide(payload):
    vertices = [_nat(v) for v in _seq(payload["vertices"])]
    _require(len(set(vertices)) == len(vertices), "R_SCHEMA")
    known = set(vertices)
    cells = []
    for cell in _seq(payload["cells"]):
        _require(isinstance(cell, dict) and set(cell) == {"dim", "verts"}, "R_SCHEMA")
        dim = _nat(cell["dim"])
        verts = [_nat(v) for v in _seq(cell["verts"])]
        _require(dim >= 1, "R_SCHEMA")
        _require(len(verts) == dim + 1, "R003_ARITY")
        _require(len(set(verts)) == len(verts), "R003_REPEATED_VERTEX")
        _require(all(v in known for v in verts), "R003_ABSENT_VERTEX")
        _require(verts == sorted(verts), "R003_UNORDERED")
        _require(tuple(verts) not in cells, "R_SCHEMA")
        cells.append(tuple(verts))
    present = set(cells)
    for cell in cells:
        if len(cell) >= 3:
            for drop in range(len(cell)):
                _require(cell[:drop] + cell[drop + 1 :] in present, "R003_MISSING_SUBFACE")
