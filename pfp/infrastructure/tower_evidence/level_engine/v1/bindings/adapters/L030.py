"""Adapter for level 030: the engine's cells, degrees, pages and steps
written as the target checker's cells, differentials and pages.  A cell is
written as its vertex list: the vertices are the cells with no facet,
numbered in declared order, and a cell's vertices are those below it
through the facet table.  Cells keep their declared order (the checker
breaks ties in its reduction order by it); page rows follow the declared
page order; a page's cells are in declared cell order; steps are sorted.
Written against the registered stage-30 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_030"
CLAUSES = (("C1", "R030_FILTRATION"), ("C2", "R030_BIDEGREE"), ("C3", "R030_SQUARE"),
           ("C4", "R030_DIFFERENTIAL"), ("C5", "R030_RESURRECTED"), ("C6", "R030_PAGE"))
COEFFICIENT_DOMAIN = {"source": "the two-element field", "target": "the two-element field"}
SORTS = (("cell", "simplex"), ("page", "page"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.cells", "cells with a facet table", "vertex lists", "PRESERVED"),)
NEAR = (("own_neg", "R030_RESURRECTED"),)
MUTATIONS = (("C1", "R030_FILTRATION", "degree_raised", "near_degree"),
             ("C2", "R030_BIDEGREE", "step_misgraded", "near_graded"),
             ("C3", "R030_SQUARE", "square_not_zero", "near_square"),
             ("C4", "R030_DIFFERENTIAL", "step_omitted", "near_missing"),
             ("C5", "R030_RESURRECTED", "mut", "mut"),
             ("C6", "R030_PAGE", "page_short", "near_page"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    cells, pages = _sort(structure, "cell"), _sort(structure, "page")
    value = {int(e): int(Fraction(str(v))) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    below = {c: [a[1] for n, a in rel if n == "face" and a[0] == c] for c in cells}
    corners = [c for c in cells if not below[c]]

    def verts(c: int) -> list[int]:
        if not below[c]:
            return [corners.index(c)]
        return sorted({v for f in below[c] for v in verts(f)})

    steps = sorted([value[a[0]], verts(a[1]), verts(a[2])] for n, a in rel if n == "step")
    return {"cells": [[verts(c), value[c]] for c in cells], "differentials": steps,
            "pages": [[value[p], [verts(c) for c in cells if ["listed", [p, c]] in [[n, a] for n, a in rel]]]
                      for p in pages]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"cell:{k}", "simplex:" + ",".join(str(v) for v in c[0])] for k, c in enumerate(positive["cells"])]
