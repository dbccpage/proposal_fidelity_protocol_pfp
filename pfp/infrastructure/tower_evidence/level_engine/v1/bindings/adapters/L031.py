"""Adapter for level 031: the engine's corners, patches, formula, test
cochains and maps written as the target checker's triangles, terms,
constant, cocycles and maps.  Corners are named by their positions; a
triangle is its corners ascending, listed in declared patch order; a term is
its patch's position and its two edges, each ascending; the rows are sorted.
Written against the registered stage-31 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_031"
CLAUSES = (("C1", "R031_NOT_COCYCLE"), ("C2", "R031_REP_DEPENDENT"), ("C3", "R031_NOT_NATURAL"))
COEFFICIENT_DOMAIN = {"source": "the two-element field", "target": "the two-element field"}
SORTS = (("corner", "vertex"), ("patch", "triangle"), ("cochain", "test cocycle"), ("map", "simplicial map"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = ""
LOSS_ROWS = (("target.vertex_bound", "any number of corners within the carrier cap", "at most 12 vertices",
              "PRESERVED"),)
NEAR = (("own_neg", "R031_REP_DEPENDENT"),)
MUTATIONS = (("C1", "R031_NOT_COCYCLE", "cochain_cut", "near_cocycle"),
             ("C2", "R031_REP_DEPENDENT", "mut", "mut"),
             ("C3", "R031_NOT_NATURAL", "constant_added", "near_natural"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    corners, patches = _sort(structure, "corner"), _sort(structure, "patch")
    cochains, maps = _sort(structure, "cochain"), _sort(structure, "map")
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def c(e: int) -> int:
        return corners.index(e)

    def edge(a: int, b: int) -> list[int]:
        return sorted([c(a), c(b)])

    spans = {a[0]: sorted(c(x) for x in a[1:]) for n, a in rel if n == "spans"}
    return {
        "cocycles": [sorted(edge(a[1], a[2]) for n, a in rel if n == "carries" and a[0] == k) for k in cochains],
        "constant": sorted(patches.index(a[0]) for n, a in rel if n == "constant"),
        "maps": [[next(c(a[2]) for n, a in rel if n == "sends" and a[0] == m and a[1] == v) for v in corners]
                 for m in maps],
        "terms": sorted([patches.index(a[0]), edge(a[1], a[2]), edge(a[3], a[4])] for n, a in rel if n == "term"),
        "triangles": [spans[t] for t in patches],
    }


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def squares(source: object, positive: object) -> list[tuple[str, object, object]]:
    """The naturality square's map: each hosted ``sends`` row carried through
    the corner names (left) against the positive's image lists (right)."""
    assert isinstance(source, dict) and isinstance(positive, dict)
    corners, maps = _sort(source, "corner"), _sort(source, "map")
    carried = [sorted([corners.index(a[1]), corners.index(a[2])] for n, a in source["relations"]
                      if n == "sends" and a[0] == m) for m in maps]
    read = [sorted([v, img] for v, img in enumerate(g)) for g in positive["maps"]]
    return [("naturality_square", carried, read)]


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"patch:{k}", "triangle:" + ",".join(str(v) for v in t)] for k, t in enumerate(positive["triangles"])]
