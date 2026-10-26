"""Adapter for level 008: the engine's hosted network and its two maps written
as the target checker's certificate packet.  Vertices are node positions;
edges are the arcs in the declared order of arcs, as ``[tail, head]``; the
weights, cochain and flow are the arcs' weight, load and carry; the
potential is the nodes' levels; the value is the declared price.  In the
adjunction, the plain and kept points are named by their tokens and the spare
point is written ``*``, the target's reserved point.  Written against the
registered stage-8 checker (``b697efad``).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_008"
CLAUSES = (("C1", "R008_CAPACITY"), ("C2", "R008_NOT_DIVERGENCE_FREE"), ("C3", "R008_GAP"),
           ("C4", "R008_VALUE_MISMATCH"), ("C5", "R008_COUNIT_NOT_POINTED"), ("C6", "R008_TRIANGLE_LEFT"),
           ("C7", "R008_TRIANGLE_RIGHT"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("node", "vertex"), ("arc", "edge"), ("pt", "adjunction element"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = ""
LOSS_ROWS = (
    ("target.spare_point", "one spare point shared by both maps", "the reserved name *", "PRESERVED"),
    ("target.price", "the declared price, the dual value", "the declared value, the primal value", "PRESERVED"),
)
NEAR = (("near_balance", "R008_NOT_DIVERGENCE_FREE"), ("near_gap", "R008_GAP"), ("near_right", "R008_TRIANGLE_RIGHT"))
MUTATIONS = (("C1", "R008_CAPACITY", "capacity_exceeded", "mut"),
             ("C2", "R008_NOT_DIVERGENCE_FREE", "unbalanced", "near_balance"),
             ("C3", "R008_GAP", "shifted_level", "near_gap"),
             ("C4", "R008_VALUE_MISMATCH", "wrong_price", "near_price"),
             ("C5", "R008_COUNIT_NOT_POINTED", "spare_off_base", "near_point"),
             ("C6", "R008_TRIANGLE_LEFT", "unit_to_spare", "near_left"),
             ("C7", "R008_TRIANGLE_RIGHT", "constant_counit", "near_right"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def packet_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    nodes, pts = _sort(structure, "node"), _sort(structure, "pt")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(name, list(args)) for name, args in structure["relations"]]
    pos = {n: k for k, n in enumerate(nodes)}
    arcs = sorted((a[0], a[1]) for n, a in rel if n == "arc")

    def per_arc(name: str) -> list[str]:
        got = {(a[0], a[1]): value[a[2]] for n, a in rel if n == name}
        return [got[e] for e in arcs]

    level = {a[0]: value[a[1]] for n, a in rel if n == "level"}
    spare = {a[0] for n, a in rel if n == "spare"}
    name = {p: ("*" if p in spare else f"pt{p - pts[0]}") for p in pts}
    return {
        "adjunction": {
            "base": [name[a[0]] for n, a in rel if n == "base"][0],
            "counit": sorted([name[a[0]], name[a[1]]] for n, a in rel if n == "counit"),
            "pointed": [name[a[0]] for n, a in rel if n == "kept"],
            "set": [name[a[0]] for n, a in rel if n == "plain"],
            "unit": sorted([name[a[0]], name[a[1]]] for n, a in rel if n == "unit"),
        },
        "cochain": per_arc("load"),
        "edges": [[pos[u], pos[v]] for u, v in arcs],
        "flow": per_arc("carry"),
        "potential": [level[n] for n in nodes],
        "value": [value[a[0]] for n, a in rel if n == "price"][0],
        "vertices": [pos[n] for n in nodes],
        "weights": per_arc("weight"),
    }


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": packet_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": packet_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": packet_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"element:{v}", f"vertex:{v}"] for v in positive["vertices"]]


def squares(source: object, positive: object) -> list[tuple[str, object, object]]:
    """The unit square: the engine's unit carried through the element names
    (left) against the target packet's unit (right)."""
    assert isinstance(source, dict) and isinstance(positive, dict)
    pts = _sort(source, "pt")
    spare = {a[0] for n, a in source["relations"] if n == "spare"}
    name = {p: ("*" if p in spare else f"pt{p - pts[0]}") for p in pts}
    carried = sorted([name[a[0]], name[a[1]]] for n, a in source["relations"] if n == "unit")
    target = dict((x, y) for x, y in positive["adjunction"]["unit"])
    read = sorted([x, target[x]] for x in positive["adjunction"]["set"])
    return [("adjunction_unit", carried, read)]
