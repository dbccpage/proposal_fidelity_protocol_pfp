# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 043: the replayed operations, scopes and edges are the
target checker's input as they stand (effect rows computed from the sealed
step, grants from the sealed world's configuration).  Written against the
registered stage-43 checker (``b5a2c46c``).

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_043"
CLAUSES = (("C1", "R043_OUTSIDE_GRANT"), ("C2", "R043_GRANT_ESCALATION"), ("C3", "R043_UNKNOWN_OPERATION"))
COEFFICIENT_DOMAIN = {"source": "sealed world configurations", "target": "effect rows and grants"}
SORTS = (("event", "operation"), ("world", "scope"), ("capability", "effect"))
UNMAPPED_SORTS = ("presentation token", "view", "requirement")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.rows", "effect rows computed from the sealed step", "declared rows; the target trusts them",
     "WEAKENED"),
    ("target.discipline", "progress gates on a state", "effect inclusion per edge", "WEAKENED"),
)
NEAR = (("own_neg", "R043_OUTSIDE_GRANT"), ("near_unknown", "R043_UNKNOWN_OPERATION"))
MUTATIONS = (("C1", "R043_OUTSIDE_GRANT", "unlicensed_view", "own_neg"),
             ("C2", "R043_GRANT_ESCALATION", "mut", "mut"),
             ("C3", "R043_UNKNOWN_OPERATION", "unknown_operation", "near_unknown"))


def graph_of(obj: object) -> dict[str, Any]:
    assert isinstance(obj, dict)
    packet = obj["packet"]
    assert isinstance(packet, dict)
    return copy.deepcopy(dict(packet))


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": graph_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": graph_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": graph_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"event:{op}", f"operation:{op}"] for op, _ in positive["operations"]]
