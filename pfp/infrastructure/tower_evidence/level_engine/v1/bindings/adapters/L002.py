"""Adapter for level 002: the engine's hosted arcs written as the target
checker's graph.  Vertices are the node elements; any other sort is not a
vertex; edges are the arcs in the order hosted; the obstruction list is
recomputed as the indices of self-loop edges (none occur).

The lift is the hosting lift's image of the positive: the sealed grammar only
adds, so the old graph reappears unchanged at the next stage, and no new
vertex or edge is claimed.  Every fixture is stated against that one next
stage.  The engine's protected-pair clause has no image in the target's
input, so the fixtures that bite it are not stated.  Only the endpoint clause
is claimed.  Written against the registered stage-2 checker (``b697efad``).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_002"
CLAUSES = (("C1", "R002_ABSENT_ENDPOINT"),)
COEFFICIENT_DOMAIN = {"source": "finite structure", "target": "directed graph with a lift"}
SORTS = (("node", "vertex"), ("arc", "edge"))
UNMAPPED_SORTS = ("mark", "presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("clause.protect", "a protected pair stays separated", "no protected pair in the target input", "DROPPED"),
    ("target.lift", "the hosting lift: the sealed grammar only adds", "the positive graph, unchanged", "WEAKENED"),
    ("target.obstruction_carrier", "no self-loop is hosted", "an empty carrier; its clauses are not claimed",
     "WEAKENED"),
)


def graph(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    off, nodes = 0, []
    for name, count in structure["sorts"]:
        if name == "node":
            nodes = list(range(off, off + count))
        off += count
    edges = [list(args) for name, args in structure["relations"] if name == "arc"]
    return {"edges": edges, "obstructions": [i for i, (a, b) in enumerate(edges) if a == b], "vertices": nodes}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    pos = graph(by["pos"])
    lift = {"edges": [list(e) for e in pos["edges"]], "vertices": list(pos["vertices"])}

    def stated(fid: str) -> dict[str, Any]:
        return {**graph(by[fid]), "lift": lift}

    return [
        {"id": "pos", "kind": "positive", "payload": stated("pos")},
        {"expected_code": "R002_ABSENT_ENDPOINT", "id": "near_source", "kind": "near_miss",
         "payload": stated("near_source")},
        {"expected_code": "R002_ABSENT_ENDPOINT", "id": "near_target", "kind": "near_miss",
         "payload": stated("near_target")},
        {"clause": "C1", "expected_code": "R002_ABSENT_ENDPOINT", "id": "absent", "kind": "decisive_mutation",
         "payload": stated("own_neg"), "repair": "pos"},
    ]


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"element:{v}", f"vertex:{v}"] for v in positive["vertices"]]
