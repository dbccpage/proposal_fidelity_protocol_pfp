# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 006: the replayed stages are the target checker's old and
new presentations as they stand (generators are the data's tokens, equations
their inseparable pairs, the embedding the identity on old data).  The sealed
stage states no arrow, so ``arrows`` and ``cells`` are empty and the endpoint
clauses (C4, C5) are not claimed.  Written against the registered stage-6
checker (``b697efad``).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_006"
CLAUSES = (("C1", "R006_COLLAPSES_OLD"), ("C2", "R006_RELATION_LOST"), ("C3", "R006_EMBEDDING_PARTIAL"))
COEFFICIENT_DOMAIN = {"source": "replayed regimes", "target": "finite presentations"}
SORTS = (("datum", "generator"), ("regime", "presentation"))
UNMAPPED_SORTS = ("presentation token", "form", "instance")
STRUCTURE_MAP_REASON = ""
LOSS_ROWS = (
    ("target.cells", "the sealed stage states no arrow", "arrows and cells empty; C4 and C5 not claimed",
     "WEAKENED"),
    ("target.protection", "validity protects the required pairs", "conservativity protects every old pair",
     "WEAKENED"),
    ("target.demand", "the demand the response answers", "not presented", "DROPPED"),
)
NEAR = (("near_lost", "R006_RELATION_LOST"),)
MUTATIONS = (("C1", "R006_COLLAPSES_OLD", "protected_pair_identified", "own_neg"),
             ("C2", "R006_RELATION_LOST", "old_equation_dropped", "near_lost"),
             ("C3", "R006_EMBEDDING_PARTIAL", "mut", "mut"))


def stages_of(obj: object) -> dict[str, Any]:
    assert isinstance(obj, dict)
    packet = obj["packet"]
    assert isinstance(packet, dict)
    return dict(packet)


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": stages_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": stages_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": stages_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"datum:{g}", f"generator:{g}"] for g in positive["new_generators"]]


def squares(source: object, positive: object) -> list[tuple[str, object, object]]:
    """The stage embedding: each old datum carried to itself by the replay
    (left) against the positive's embedding (right)."""
    assert isinstance(source, dict) and isinstance(positive, dict)
    old = source["packet"]["old_generators"]
    carried = sorted([g, g] for g in old if g in source["packet"]["new_generators"])
    return [("stage_embedding", carried, sorted(positive["embedding"]))]
