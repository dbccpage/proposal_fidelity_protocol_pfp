"""Target checker of record for MSS-030, row 30 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 30): check page bidegrees and d_r composed with itself is
zero. Negative instance: a class killed on a prior page cannot reappear
without transport.

Input (closed): ``{"cells": [[[nat], nat]], "differentials": [[r, [nat],
[nat]]], "pages": [[r, [[nat]]]]}``. A cell is a simplex (a strictly
ascending vertex list) with its filtration degree p. A differential row
``[r, source, target]`` is one entry, coefficient 1 over F2, of the declared
d_r from the source cell to the target cell. A page row ``[r, cells]`` lists
the declared basis of E_r, for r = 1, 2, ..., N in order; differentials are
declared for r = 1 .. N - 1.

Declared input class: finite filtered simplicial complexes over F2, with the
pages presented in the reduced basis. The checker runs the standard column
reduction of the boundary over F2, with cells ordered by (filtration,
dimension, declared position); a reduced pair (sigma, tau) whose filtration
gap is r is one entry of d_r from tau to sigma, and E_r is the set of cells
in no pair of gap below r. Pages presented in another basis are refused, not
translated.

Clauses, each recomputed:

- C1 ``R030_FILTRATION``: a face has a higher filtration degree than its cell,
  so the boundary does not respect the filtration;
- C2 ``R030_BIDEGREE``: a declared d_r entry does not have bidegree
  (-r, r - 1): its filtration gap is not r, or it does not lower dimension by
  one;
- C3 ``R030_SQUARE``: some declared d_r composed with itself is nonzero over
  F2;
- C4 ``R030_DIFFERENTIAL``: the declared d_r entries are not the recomputed
  pairs of gap r;
- C5 ``R030_RESURRECTED``: a page lists a class killed on an earlier page
  (the level's negative);
- C6 ``R030_PAGE``: a page differs from the recomputed page otherwise.
"""

STAGE = 30
ROW_SHA256 = "sha256:8e07866b4ce340c0abacf61b9e9d0c3c704302590a5fbc848606a5c966431b27"
FIELDS = ("cells", "differentials", "pages")
CLAUSES = (
    ("C1", "R030_FILTRATION"),
    ("C2", "R030_BIDEGREE"),
    ("C3", "R030_SQUARE"),
    ("C4", "R030_DIFFERENTIAL"),
    ("C5", "R030_RESURRECTED"),
    ("C6", "R030_PAGE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
_TRIANGLE = [[[0], 0], [[1], 0], [[2], 0], [[0, 1], 2], [[0, 2], 2], [[1, 2], 2], [[0, 1, 2], 4]]
OWN_NEGATIVE = {
    "cells": _TRIANGLE,
    "differentials": [[2, [0, 1], [1]], [2, [0, 2], [2]], [2, [0, 1, 2], [1, 2]]],
    "pages": [[1, [c for c, _ in _TRIANGLE]], [2, [c for c, _ in _TRIANGLE]], [3, [[0], [1, 2]]]],
}
OWN_NEGATIVE_CODE = "R030_RESURRECTED"


def _cell(value, known):
    verts = tuple(_nat(v) for v in _seq(value))
    _require(verts in known, "R_SCHEMA")
    return verts


def _decide(payload):
    filt, order = {}, []
    for entry in _seq(payload["cells"]):
        _seq(entry, 2)
        verts = tuple(_nat(v) for v in _seq(entry[0]))
        _require(verts and list(verts) == sorted(set(verts)) and verts not in filt, "R_SCHEMA")
        filt[verts] = _nat(entry[1])
        order.append(verts)
    for cell in order:
        if len(cell) > 1:
            for i in range(len(cell)):
                face = cell[:i] + cell[i + 1:]
                _require(face in filt, "R_SCHEMA")
                _require(filt[face] <= filt[cell], "R030_FILTRATION")
    position = {c: i for i, c in enumerate(order)}
    ranked = sorted(order, key=lambda c: (filt[c], len(c), position[c]))
    rank = {c: i for i, c in enumerate(ranked)}
    low_owner, pairs = {}, []
    for cell in ranked:
        column = set()
        if len(cell) > 1:
            column = {rank[cell[:i] + cell[i + 1:]] for i in range(len(cell))}
        while column and max(column) in low_owner:
            column ^= low_owner[max(column)]
        if column:
            low_owner[max(column)] = column
            pairs.append((ranked[max(column)], cell))
    gap = {(tau, sigma): filt[tau] - filt[sigma] for sigma, tau in pairs}
    pages_in = []
    for entry in _seq(payload["pages"]):
        _seq(entry, 2)
        r = _nat(entry[0])
        _require(r == len(pages_in) + 1, "R_SCHEMA")
        cells = [_cell(c, filt) for c in _seq(entry[1])]
        _require(len(set(cells)) == len(cells), "R_SCHEMA")
        pages_in.append(set(cells))
    last = len(pages_in)
    _require(last >= 1, "R_SCHEMA")
    declared = {}
    for entry in _seq(payload["differentials"]):
        _seq(entry, 3)
        r = _nat(entry[0])
        source, target = _cell(entry[1], filt), _cell(entry[2], filt)
        _require(1 <= r < last and (source, target) not in declared.get(r, set()), "R_SCHEMA")
        ok = filt[source] - filt[target] == r and len(source) == len(target) + 1
        _require(ok, "R030_BIDEGREE")
        declared.setdefault(r, set()).add((source, target))
    for r, entries in declared.items():
        for x in {source for source, _ in entries}:
            hits = {}
            for source, middle in entries:
                if source == x:
                    for middle2, target in entries:
                        if middle2 == middle:
                            hits[target] = hits.get(target, 0) + 1
            _require(all(count % 2 == 0 for count in hits.values()), "R030_SQUARE")
    for r in range(1, last):
        recomputed = {pair for pair, g in gap.items() if g == r}
        _require(declared.get(r, set()) == recomputed, "R030_DIFFERENTIAL")
    for r in range(1, last + 1):
        page = {c for c in order if not any(c in pair and g < r for pair, g in gap.items())}
        killed_before = set(order) - page
        _require(not (pages_in[r - 1] & killed_before), "R030_RESURRECTED")
        _require(pages_in[r - 1] == page, "R030_PAGE")
