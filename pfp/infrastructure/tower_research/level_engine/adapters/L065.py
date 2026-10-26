# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 065: the engine's two step systems, map and map back
written as the target checker's source, target, map, back and claim.  States
and sights are named by their positions in the declared order; a system
with no map rows is written with no map (``null``), and likewise the map
back; the claim is ``equivalence`` when both ways are claimed, otherwise
``simulation``.  Written against the registered stage-65 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_065"
CLAUSES = (("C1", "R065_NO_MAP"), ("C2", "R065_NOT_A_MAP"), ("C3", "R065_STEP_SQUARE"),
           ("C4", "R065_OBSERVATION_SQUARE"), ("C5", "R065_NOT_EQUIVALENT"))
COEFFICIENT_DOMAIN = {"source": "finite step systems", "target": "finite step systems"}
SORTS = (("here", "source state"), ("there", "target state"), ("sight", "observation"))
UNMAPPED_SORTS = ("presentation token", "witness form", "bond")
STRUCTURE_MAP_REASON = "the map is the claim's own datum; its squares are the clauses the checker decides"
LOSS_ROWS = (("target.names", "states and sights as elements", "their positions as names", "PRESERVED"),)
NEAR = (("own_neg", "R065_NO_MAP"),)
MUTATIONS = (("C1", "R065_NO_MAP", "map_withdrawn", "near_no_map"), ("C2", "R065_NOT_A_MAP", "image_missing", "near_partial"),
             ("C3", "R065_STEP_SQUARE", "step_not_carried", "near_step"), ("C4", "R065_OBSERVATION_SQUARE", "mut", "mut"),
             ("C5", "R065_NOT_EQUIVALENT", "both_ways_unbacked", "near_equiv"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def systems_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    here, there, sight = _sort(structure, "here"), _sort(structure, "there"), _sort(structure, "sight")
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def pairs_of(name: str, left: list[int], right: list[int], prefix: str = "") -> list[list[str]]:
        return [[str(left.index(a[0])), prefix + str(right.index(a[1]))] for n, a in rel if n == name]

    def system(states: list[int], step: str, sees: str) -> dict[str, Any]:
        return {"observe": pairs_of(sees, states, sight, "r"), "states": [str(k) for k in range(len(states))],
                "step": pairs_of(step, states, states)}

    sends, back = pairs_of("sends", here, there), pairs_of("returns", there, here)
    return {"back": back or None, "claim": "equivalence" if any(n == "both_ways" for n, _ in rel) else "simulation",
            "map": sends or None, "source": system(here, "here_step", "here_sees"),
            "target": system(there, "there_step", "there_sees")}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": systems_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": systems_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": systems_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"here:{s}", f"source:{s}"] for s in positive["source"]["states"]] + \
        [[f"there:{t}", f"target:{t}"] for t in positive["target"]["states"]]
