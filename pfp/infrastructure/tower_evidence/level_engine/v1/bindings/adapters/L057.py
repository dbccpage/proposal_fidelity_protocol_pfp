"""Adapter for level 057: the engine's table and probes written as the target
checker's table and carried test rows.  Row ``i``, column ``j`` of the table
is the cell at slots ``i`` and ``j`` in declared order, written ``[a, b]``;
each probe is written as its row and its claimed image.  Written against the
registered stage-57 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_057"
CLAUSES = (("C1", "R057_NOT_SIZE_KEEPING"), ("C2", "R057_IMAGE"))
COEFFICIENT_DOMAIN = {"source": "exact pairs of rationals", "target": "exact pairs of rationals"}
SORTS = (("slot", "frame slot"), ("probe", "carried test row"), ("val", "rational"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.slot_order", "slots as elements", "row and column positions", "PRESERVED"),)
NEAR = (("own_neg", "R057_NOT_SIZE_KEEPING"),)
MUTATIONS = (("C1", "R057_NOT_SIZE_KEEPING", "mut", "mut"), ("C2", "R057_IMAGE", "image_off", "near_image"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def steps_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    slots, probes = _sort(structure, "slot"), _sort(structure, "probe")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def grid(name: str) -> dict[tuple[int, int], list[str]]:
        return {(a[0], a[1]): [value[a[2]], value[a[3]]] for n, a in rel if n == name}

    cell, test, image = grid("cell"), grid("test"), grid("image")
    return {"rows": [[[test[(p, s)] for s in slots], [image[(p, s)] for s in slots]] for p in probes],
            "table": [[cell[(i, j)] for j in slots] for i in slots]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": steps_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": steps_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": steps_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"slot:{k}", f"index:{k}"] for k in range(len(positive["table"]))]
