"""Adapter for level 023: the engine's points, patches, sections and glue
written as the target checker's points, patches, sections and glued rows.
Point ``k`` (declared order) is named ``str(k + 1)`` and value ``k`` is
named ``str(k)``; section ``i`` lives on patch ``i``; rows are sorted.
Written against the registered stage-23 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_023"
CLAUSES = (("C1", "R023_NOT_COVERING"), ("C2", "R023_SECTION_DOMAIN"), ("C3", "R023_OVERLAP_CONFLICT"),
           ("C4", "R023_GLUE_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "finite value names", "target": "finite value names"}
SORTS = (("point", "point"), ("patch", "patch"), ("value", "value"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = ""
LOSS_ROWS = (("target.transport_reading", "the function reading", "the function reading", "PRESERVED"),)
NEAR = (("own_neg", "R023_OVERLAP_CONFLICT"), ("near_glue", "R023_GLUE_MISMATCH"))
MUTATIONS = (("C1", "R023_NOT_COVERING", "point_uncovered", "near_uncovered"),
             ("C2", "R023_SECTION_DOMAIN", "section_short", "near_domain"),
             ("C3", "R023_OVERLAP_CONFLICT", "overlap_conflict", "own_neg"),
             ("C4", "R023_GLUE_MISMATCH", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    points, patches, values = _sort(structure, "point"), _sort(structure, "patch"), _sort(structure, "value")
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def pt(e: int) -> str:
        return str(points.index(e) + 1)

    def val(e: int) -> str:
        return str(values.index(e))

    return {"glued": sorted([pt(a[0]), val(a[1])] for n, a in rel if n == "glue"),
            "patches": [sorted(pt(a[0]) for n, a in rel if n == "member" and a[1] == p) for p in patches],
            "points": [pt(e) for e in points],
            "sections": [sorted([pt(a[1]), val(a[2])] for n, a in rel if n == "assigns" and a[0] == p)
                         for p in patches]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def squares(source: object, positive: object) -> list[tuple[str, object, object]]:
    """Restriction: the hosted glue restricted to each patch through the
    hosted membership (left), against the positive's glue restricted to its
    patches (right)."""
    assert isinstance(source, dict) and isinstance(positive, dict)
    points, values = _sort(source, "point"), _sort(source, "value")
    rel = [(n, list(a)) for n, a in source["relations"]]
    glue = {a[0]: a[1] for n, a in rel if n == "glue"}
    carried = [sorted([str(points.index(a[0]) + 1), str(values.index(glue[a[0]]))]
                      for n, a in rel if n == "member" and a[1] == p) for p in _sort(source, "patch")]
    g = dict((x, v) for x, v in positive["glued"])
    read = [sorted([x, g[x]] for x in patch) for patch in positive["patches"]]
    return [("restriction", carried, read)]


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"point:{k}", f"point:{p}"] for k, p in enumerate(positive["points"])]
