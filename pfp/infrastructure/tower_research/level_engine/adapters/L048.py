# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 048: the engine's row written as the target checker's
frame and row.  Slots are named by their position in the declared frame;
the row lists each slot's entry ``[a, b]`` in that order, and a slot with no
entry contributes none.  Written against the registered stage-48 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_048"
CLAUSES = (("C1", "R048_FRAME"), ("C2", "R048_NOT_UNIT"))
COEFFICIENT_DOMAIN = {"source": "exact pairs of rationals", "target": "exact pairs of rationals"}
SORTS = (("slot", "frame slot"), ("val", "rational"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.slot_names", "slots as elements", "their positions as names", "PRESERVED"),)
NEAR = (("own_neg", "R048_NOT_UNIT"),)
MUTATIONS = (("C1", "R048_FRAME", "slot_without_entry", "near_gap"), ("C2", "R048_NOT_UNIT", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def row_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    slots = _sort(structure, "slot")
    value = {int(e): str(v) for e, v in structure["values"]}
    got = {a[0]: [value[a[1]], value[a[2]]] for n, a in structure["relations"] if n == "entry"}
    return {"frame": [f"s{k}" for k in range(len(slots))], "row": [got[s] for s in slots if s in got]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": row_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": row_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": row_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"slot:{k}", f"frame:{name}"] for k, name in enumerate(positive["frame"])]
