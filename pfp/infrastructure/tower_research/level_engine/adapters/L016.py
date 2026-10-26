# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 016: the replayed sealed stage chain is the target
checker's input as it stands (stages of generators and equations, maps on
generators).  Generators are the data's presentation tokens.  Written against
the registered stage-16 checker (``b697efad``).

The sealed stages state no equation, so on the positive the
relation-preservation clause (C2) has nothing to check; a single stated
equation in the middle stage, which the last stage does not keep, bites it.
The stage
transition square compares the sealed replay's inclusion of each stage's data
in the next (left) with the positive's consecutive maps (right).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_016"
CLAUSES = (("C1", "R016_MAP_PARTIAL"), ("C2", "R016_RELATION_NOT_PRESERVED"), ("C3", "R016_COLLAPSES_EQUATION"),
           ("C4", "R016_NOT_COHERENT"))
COEFFICIENT_DOMAIN = {"source": "replayed regimes", "target": "finite presentations"}
SORTS = (("datum", "generator"), ("regime", "stage"))
UNMAPPED_SORTS = ("presentation token", "form", "instance")
STRUCTURE_MAP_REASON = ""
LOSS_ROWS = (
    ("target.relations", "the sealed stages state no equation", "relation preservation bitten only by a mutation",
     "WEAKENED"),
    ("target.stage_content", "a replayed regime", "its admitted data only", "WEAKENED"),
)
NEAR = (("mut", "R016_MAP_PARTIAL"),)
MUTATIONS = (("C1", "R016_MAP_PARTIAL", "forgotten_datum", "near_partial"),
             ("C2", "R016_RELATION_NOT_PRESERVED", "equation_not_kept", "near_equation"),
             ("C3", "R016_COLLAPSES_EQUATION", "two_data_to_one", "near_collapse"),
             ("C4", "R016_NOT_COHERENT", "direct_map_off_composite", "near_incoherent"))


def chain_of(obj: object) -> dict[str, Any]:
    assert isinstance(obj, dict)
    packet = obj["packet"]
    assert isinstance(packet, dict)
    return dict(packet)


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": chain_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": chain_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": chain_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    last = positive["stages"][-1]["generators"]
    return [[f"datum:{g}", f"generator:{g}"] for g in last]


def squares(source: object, positive: object) -> list[tuple[str, object, object]]:
    """The stage transition: each stage's data carried into the next by the
    replay (left) against the positive's consecutive maps (right)."""
    assert isinstance(source, dict) and isinstance(positive, dict)
    stages = source["packet"]["stages"]
    carried = [sorted([g, g] for g in stages[i]["generators"]) for i in range(len(stages) - 1)]
    consecutive = {(m["source"], m["target"]): m["on_generators"] for m in positive["maps"]}
    read = [sorted(consecutive[(i, i + 1)]) for i in range(len(stages) - 1)]
    return [("stage_transition", carried, read)]
