"""Target checker of record for MSS-029, row 29 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 29): check chain degrees and boundaries square to zero.
Negative instance: a nonzero composite of consecutive differentials is
rejected.

Input (closed): ``{"cells": [[nat]], "differentials": [matrix]}``. Cells are
simplices written as strictly ascending vertex lists; a cell with k + 1
vertices has degree k, and within each degree cells are ordered as listed.
``differentials[k-1]`` is the declared boundary from degree k to degree k - 1,
a matrix of canonical rationals with one row per (k-1)-cell and one column
per k-cell.

Declared input class: finite ordered simplicial complexes with integer
coefficients (computed over the rationals, so the signless countermodel is
refused; over F2 it would vanish). The checker derives the signed boundary
from the cells, so a declared matrix is never trusted for the complex it
claims to present. ``derived_limit`` is not decided: derived limits of finite
towers of finite groups vanish, so it has no finite witness beyond zero.

Clauses, each recomputed:

- C1 ``R029_DEGREE``: the declared matrices do not chain: wrong count, or a
  shape that is not (cells of degree k-1) x (cells of degree k);
- C2 ``R029_NONZERO_COMPOSITE``: some composite of consecutive declared
  differentials is nonzero (the level's negative);
- C3 ``R029_NOT_THE_BOUNDARY``: a declared matrix differs from the signed
  boundary recomputed from the cells;
- C4 ``R029_NOT_CLOSED``: a face of a cell is not a declared cell.
"""

STAGE = 29
ROW_SHA256 = "sha256:d8c6f62b002df077b12094eb923108f0f1279a251799ee46dfa6564fbeac4775"
FIELDS = ("cells", "differentials")
CLAUSES = (
    ("C1", "R029_DEGREE"),
    ("C2", "R029_NONZERO_COMPOSITE"),
    ("C3", "R029_NOT_THE_BOUNDARY"),
    ("C4", "R029_NOT_CLOSED"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "cells": [[0], [1], [2], [0, 1], [0, 2], [1, 2], [0, 1, 2]],
    "differentials": [
        [["1/1", "1/1", "0/1"], ["1/1", "0/1", "1/1"], ["0/1", "1/1", "1/1"]],
        [["1/1"], ["1/1"], ["1/1"]],
    ],
}
OWN_NEGATIVE_CODE = "R029_NONZERO_COMPOSITE"


def _decide(payload):
    cells = []
    for cell in _seq(payload["cells"]):
        verts = [_nat(v) for v in _seq(cell)]
        _require(verts and verts == sorted(set(verts)) and tuple(verts) not in cells, "R_SCHEMA")
        cells.append(tuple(verts))
    known = set(cells)
    for cell in cells:
        if len(cell) > 1:
            for i in range(len(cell)):
                _require(cell[:i] + cell[i + 1:] in known, "R029_NOT_CLOSED")
    top = max(len(c) for c in cells) - 1
    by_degree = [[c for c in cells if len(c) == k + 1] for k in range(top + 1)]
    declared = _seq(payload["differentials"])
    _require(len(declared) == top, "R029_DEGREE")
    matrices = []
    for k in range(1, top + 1):
        rows = _seq(declared[k - 1])
        _require(len(rows) == len(by_degree[k - 1]), "R029_DEGREE")
        for row in rows:
            _require(len(_seq(row)) == len(by_degree[k]), "R029_DEGREE")
        matrices.append([_rats(row) for row in rows])
    for k in range(2, top + 1):
        lower, upper = matrices[k - 2], matrices[k - 1]
        for i in range(len(by_degree[k - 2])):
            for j in range(len(by_degree[k])):
                value = sum((lower[i][t] * upper[t][j] for t in range(len(by_degree[k - 1]))), Fraction(0))
                _require(value == 0, "R029_NONZERO_COMPOSITE")
    for k in range(1, top + 1):
        index = {c: i for i, c in enumerate(by_degree[k - 1])}
        for j, cell in enumerate(by_degree[k]):
            column = [Fraction(0)] * len(by_degree[k - 1])
            for i in range(len(cell)):
                column[index[cell[:i] + cell[i + 1:]]] += (-1) ** i
            for i in range(len(column)):
                _require(matrices[k - 1][i][j] == column[i], "R029_NOT_THE_BOUNDARY")
