"""Target checker of record for MSS-004, row 4 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 4): match graph edges to simplex 1-faces with declared
orientation. Negative instance: a missing edge of a triangle is rejected.

Input (closed): ``{"vertices": [nat], "cells": [[nat]], "edges": ["u>v"],
"order": [nat]}``. ``cells`` are simplices as strictly ascending vertex lists
(two or more vertices); ``edges`` are directed arcs written ``tail>head``;
``order`` is the declared vertex order that orients every edge (i to j when i
precedes j), which is what makes the orientation transitive.

Clauses, recomputed from the cells, never read from a declared match:

- C1 ``R004_MISSING_EDGE``: a 1-face of some cell has no edge;
- C2 ``R004_UNMATCHED_EDGE``: an edge is not a 1-face of any cell, or two edges
  sit on one 1-face (the matching must be a bijection);
- C3 ``R004_CYCLIC_ORIENTATION``: inside some cell three edges form a directed
  3-cycle, which no vertex order induces;
- C4 ``R004_ORDER_NOT_TOTAL``: ``order`` is not a permutation of the vertices;
- C5 ``R004_ORDER_MISMATCH``: an edge points against the declared order.

Recorded, not decided here: level 4 adds no new opcode, so it fails grammar 1
section 4.3's own admission test for a later level (W1-S01 section 6 item 20).
The orientation is a declared convention, never derived.
"""

from itertools import combinations

STAGE = 4
ROW_SHA256 = "sha256:d16006a9d69b1d5efc21066b106c2c70cd610149e99ad112d3b55236260f1ff6"
FIELDS = ("cells", "edges", "order", "vertices")
CLAUSES = (
    ("C1", "R004_MISSING_EDGE"),
    ("C2", "R004_UNMATCHED_EDGE"),
    ("C3", "R004_CYCLIC_ORIENTATION"),
    ("C4", "R004_ORDER_NOT_TOTAL"),
    ("C5", "R004_ORDER_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {"cells": [[0, 1, 2]], "edges": ["0>1", "1>2"], "order": [0, 1, 2], "vertices": [0, 1, 2]}
OWN_NEGATIVE_CODE = "R004_MISSING_EDGE"

_ARC = re.compile(r"(0|[1-9][0-9]*)>(0|[1-9][0-9]*)")


def _decide(payload):
    vertices = [_nat(v) for v in _seq(payload["vertices"])]
    _require(len(set(vertices)) == len(vertices), "R_SCHEMA")
    known = set(vertices)
    cells, faces = [], set()
    for cell in _seq(payload["cells"]):
        verts = [_nat(v) for v in _seq(cell)]
        _require(len(verts) >= 2 and verts == sorted(set(verts)) and set(verts) <= known, "R_SCHEMA")
        cells.append(verts)
        faces.update(combinations(verts, 2))
    arcs = []
    for text in _seq(payload["edges"]):
        _require(isinstance(text, str), "R_SCHEMA")
        match = _ARC.fullmatch(text)
        _require(match is not None, "R_SCHEMA")
        tail, head = int(match.group(1)), int(match.group(2))
        _require(tail in known and head in known and tail != head, "R_SCHEMA")
        arcs.append((tail, head))
    matched = set()
    for tail, head in arcs:
        face = (min(tail, head), max(tail, head))
        _require(face in faces and face not in matched, "R004_UNMATCHED_EDGE")
        matched.add(face)
    _require(matched == faces, "R004_MISSING_EDGE")
    arcset = set(arcs)
    for verts in cells:
        for a, b, c in combinations(verts, 3):
            forward = (a, b) in arcset and (b, c) in arcset and (c, a) in arcset
            backward = (a, c) in arcset and (c, b) in arcset and (b, a) in arcset
            _require(not (forward or backward), "R004_CYCLIC_ORIENTATION")
    order = [_nat(v) for v in _seq(payload["order"])]
    _require(len(set(order)) == len(order) and set(order) == known, "R004_ORDER_NOT_TOTAL")
    rank = {vertex: index for index, vertex in enumerate(order)}
    for tail, head in arcs:
        _require(rank[tail] < rank[head], "R004_ORDER_MISMATCH")
