"""Adapter for level 059: the engine's setting rows and claims written as the
target checker's near rows, far rows, correlations, total, bound and
excess.  Settings and slots follow the declared order.  Written against the
registered stage-59 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_059"
CLAUSES = (("C1", "R059_NOT_UNIT"), ("C2", "R059_CORRELATION"), ("C3", "R059_TOTAL"), ("C4", "R059_BOUND"),
           ("C5", "R059_EXCESS"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("setting", "setting"), ("slot", "row slot"), ("val", "rational"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.row_width", "two-slot rows", "rows of any common width", "WEAKENED"),)
NEAR = (("own_neg", "R059_TOTAL"),)
MUTATIONS = (("C1", "R059_NOT_UNIT", "row_not_unit", "near_unit"), ("C2", "R059_CORRELATION", "correlation_off", "near_corr"),
             ("C3", "R059_TOTAL", "mut", "mut"), ("C4", "R059_BOUND", "bound_off", "near_bound"),
             ("C5", "R059_EXCESS", "margin_off", "near_excess"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def bound_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    settings, slots = _sort(structure, "setting"), _sort(structure, "slot")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def grid(name: str, second: list[int]) -> list[list[str]]:
        got = {(a[0], a[1]): value[a[2]] for n, a in rel if n == name}
        return [[got[(x, s)] for s in second] for x in settings]

    def one(name: str) -> str:
        return next(value[a[0]] for n, a in rel if n == name)

    return {"bound": one("bound"), "correlations": grid("corr", settings), "excess": one("excess"),
            "far": grid("far", slots), "near": grid("near", slots), "total": one("total")}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": bound_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": bound_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": bound_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"setting:{k}", f"setting:{k}"] for k in range(len(positive["near"]))]
