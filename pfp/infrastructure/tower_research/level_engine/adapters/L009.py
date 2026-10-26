# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 009: the replayed arrows, reversal and composites are the
target checker's input as they stand (objects are the carrier's points;
arrows are named by their endpoints; a mark is the sealed collision under the
identity map).  Written against the registered stage-9 checker
(``b697efad``).

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_009"
CLAUSES = (("C1", "R009_NOT_TOTAL"), ("C2", "R009_NOT_INVOLUTION"), ("C3", "R009_ENDPOINTS"),
           ("C4", "R009_OBSTRUCTION_DROPPED"), ("C5", "R009_COMPOSITE_TYPING"), ("C6", "R009_VARIANCE"))
COEFFICIENT_DOMAIN = {"source": "relations on the two-point carrier", "target": "typed arrows"}
SORTS = (("point", "object"), ("pair", "arrow"))
UNMAPPED_SORTS = ("presentation token",)
STRUCTURE_MAP_REASON = ""
LOSS_ROWS = (
    ("target.arrows", "the symmetric datum", "its composition closure, loops included", "WEAKENED"),
    ("target.marks", "collision under the identity map", "a two-valued mark", "PRESERVED"),
)
NEAR = (("near_directed", "R009_NOT_TOTAL"), ("near_typing", "R009_COMPOSITE_TYPING"))
MUTATIONS = (("C1", "R009_NOT_TOTAL", "loop_unreversed", "near_partial"),
             ("C2", "R009_NOT_INVOLUTION", "return_reversed_to_itself", "near_not_involution"),
             ("C3", "R009_ENDPOINTS", "arrow_stated_as_loop", "near_endpoints"),
             ("C4", "R009_OBSTRUCTION_DROPPED", "mark_dropped_by_reversal", "own_neg"),
             ("C5", "R009_COMPOSITE_TYPING", "wrong_loop_composite", "near_typing"),
             ("C6", "R009_VARIANCE", "mut", "mut"))


def arrows_of(obj: object) -> dict[str, Any]:
    assert isinstance(obj, dict)
    packet = obj["packet"]
    assert isinstance(packet, dict)
    return copy.deepcopy(dict(packet))


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": arrows_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": arrows_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": arrows_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"pair:{a[1]}{a[2]}", f"arrow:{a[0]}"] for a in positive["arrows"]]


def squares(source: object, positive: object) -> list[tuple[str, object, object]]:
    """The dagger action: each arrow's transposed pair, carried by the replay
    (left), against the positive's dagger read as pairs of endpoints (right)."""
    assert isinstance(source, dict) and isinstance(positive, dict)
    ends = {a[0]: (a[1], a[2]) for a in source["packet"]["arrows"]}
    carried = sorted([[s, t], [t, s]] for s, t in ends.values())
    target = {a[0]: [a[1], a[2]] for a in positive["arrows"]}
    read = sorted([target[f], target[g]] for f, g in positive["dagger"])
    return [("dagger_action", carried, read)]
