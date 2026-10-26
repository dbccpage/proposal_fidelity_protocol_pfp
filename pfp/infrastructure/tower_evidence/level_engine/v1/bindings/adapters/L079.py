"""Adapter for level 079: the engine's states and merge table written as the
target checker's states and merge rows (sorted).  States are named
``s<k>`` by their positions; any other element named in a row is written
``x<k>``.  Written against the registered stage-79 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_079"
CLAUSES = (("C1", "R079_TABLE"), ("C2", "R079_NOT_IDEMPOTENT"), ("C3", "R079_NOT_ASSOCIATIVE"),
           ("C4", "R079_NOT_COMMUTATIVE"))
COEFFICIENT_DOMAIN = {"source": "finite state names", "target": "finite state names"}
SORTS = (("state", "replica state"),)
UNMAPPED_SORTS = ("presentation token", "witness form", "spare")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.domain_bound", "the declared states", "at most 12 states", "PRESERVED"),)
NEAR = (("own_neg", "R079_NOT_IDEMPOTENT"),)
MUTATIONS = (("C1", "R079_TABLE", "row_dropped", "near_gap"),
             ("C2", "R079_NOT_IDEMPOTENT", "self_merge_grows", "near_twice"),
             ("C3", "R079_NOT_ASSOCIATIVE", "bracket_breaks", "near_bracket"),
             ("C4", "R079_NOT_COMMUTATIVE", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    states = _sort(structure, "state")

    def nm(e: int) -> str:
        return f"s{states.index(e)}" if e in states else f"x{e}"

    return {"merge": sorted([nm(a[0]), nm(a[1]), nm(a[2])] for n, a in structure["relations"] if n == "merge"),
            "states": [nm(s) for s in states]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"state:{k}", f"state:{s}"] for k, s in enumerate(positive["states"])]
