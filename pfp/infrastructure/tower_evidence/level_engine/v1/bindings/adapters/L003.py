"""Adapter for level 003: the engine's hosted cells written as the target
checker's cells.  A relation becomes a cell whose dimension is its symbol's
declared arity less one and whose vertices are its arguments; the points are
the vertices; any other sort is not a vertex.  Cells are listed in a fixed
order (dimension, then vertices), since relation order is presentation.

Only the clause the engine's own fixtures bite with a single edit is claimed
(a missing subface).  Written against the stage-3 target checker on
``claude/p2-checkers`` (``b697efad``); it takes effect only when that checker
is registered of record under ``CHECKER_ID``.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_003"
CLAUSES = (("C5", "R003_MISSING_SUBFACE"),)
COEFFICIENT_DOMAIN = {"source": "finite structure", "target": "cell list"}
SORTS = (("pt", "vertex"), ("side", "cell of dimension 1"), ("cell", "cell of dimension 2"))
UNMAPPED_SORTS = ("mark", "presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
NEAR = {"near_side_first": "R003_MISSING_SUBFACE", "near_side_last": "R003_MISSING_SUBFACE",
        "near_side_outer": "R003_MISSING_SUBFACE", "near_ends": "R003_ABSENT_VERTEX",
        "near_repeat": "R003_REPEATED_VERTEX"}


def cells(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    arity = {s["name"]: len(s["sorts"]) for s in structure["symbols"]}
    off, points = 0, []
    for name, count in structure["sorts"]:
        if name == "pt":
            points = list(range(off, off + count))
        off += count
    out = [{"dim": arity[name] - 1, "verts": list(args)} for name, args in structure["relations"]]
    return {"cells": sorted(out, key=lambda c: (c["dim"], c["verts"])), "vertices": points}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": cells(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": cells(by[fid])}
            for fid, code in NEAR.items()]
    out.append({"clause": "C5", "expected_code": "R003_MISSING_SUBFACE", "id": "mut", "kind": "decisive_mutation",
                "payload": cells(by["mut"]), "repair": "pos"})
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"element:{v}", f"vertex:{v}"] for v in positive["vertices"]]
