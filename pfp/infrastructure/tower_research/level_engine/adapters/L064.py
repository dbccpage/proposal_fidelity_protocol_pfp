# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 064: the engine's corners, faces, walks, values and
transports written as the target checker's cell, faces and edges.  Corners
and labels are named by their positions; the cell lists the corners in
declared order, so its base is the first corner; each face row is its place,
its connector, its boundary walk (slot order) and its value; edge rows are
sorted.  Written against the registered stage-64 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_064"
CLAUSES = (("C1", "R064_WALK"), ("C2", "R064_NOT_A_BOUNDARY"), ("C3", "R064_FACE_MISMATCH"),
           ("C4", "R064_NOT_CLOSED"))
COEFFICIENT_DOMAIN = {"source": "permutations of a finite label set", "target": "permutations of a finite label set"}
SORTS = (("corner", "vertex"), ("label", "label"), ("face", "face"), ("slot", "walk position"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.slots", "walk positions as elements with index values", "list order", "PRESERVED"),)
NEAR = (("own_neg", "R064_NOT_CLOSED"),)
MUTATIONS = (("C1", "R064_WALK", "connector_short", "near_short"),
             ("C2", "R064_NOT_A_BOUNDARY", "edge_used_twice", "near_twice"),
             ("C3", "R064_FACE_MISMATCH", "mut", "mut"),
             ("C4", "R064_NOT_CLOSED", "order_changed", "near_order"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    corners, labels = _sort(structure, "corner"), _sort(structure, "label")
    faces = _sort(structure, "face")
    value = {int(e): int(Fraction(str(v))) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def walk(name: str, f: int) -> list[int]:
        got = sorted((value[a[1]], corners.index(a[2])) for n, a in rel if n == name and a[0] == f)
        return [v for _, v in got]

    def perm(f: int) -> list[int]:
        img = {labels.index(a[1]): labels.index(a[2]) for n, a in rel if n == "sends" and a[0] == f}
        return [img[x] for x in range(len(labels))]

    edges: dict[tuple[int, int], dict[int, int]] = {}
    for n, a in rel:
        if n == "link":
            edges.setdefault((corners.index(a[0]), corners.index(a[1])), {})[labels.index(a[2])] = labels.index(a[3])
    return {"cell": list(range(len(corners))),
            "edges": [[u, v, [m[x] for x in range(len(labels))]] for (u, v), m in sorted(edges.items())],
            "faces": [[value[f], walk("joins", f), walk("runs", f), perm(f)] for f in faces],
            "labels": len(labels)}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"face:{k}", f"face:{k}"] for k in range(len(positive["faces"]))]
