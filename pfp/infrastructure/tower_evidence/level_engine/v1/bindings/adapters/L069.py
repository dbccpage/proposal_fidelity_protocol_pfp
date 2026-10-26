"""Adapter for level 069: the engine's coefficients, ends and claimed values
written as the target checker's polynomial (ascending degree), interval and
values.  Written against the registered stage-69 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_069"
CLAUSES = (("C1", "R069_NOT_SQUAREFREE"), ("C2", "R069_ENDPOINT_ROOT"), ("C3", "R069_NOT_ISOLATING"),
           ("C4", "R069_EVALUATION"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("coef", "coefficient"), ("end", "interval end"), ("claimed", "claimed value"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.algebraic_arithmetic", "one isolated root", "no arithmetic on algebraic numbers",
              "PRESERVED"),)
NEAR = (("own_neg", "R069_NOT_ISOLATING"), ("near_value", "R069_EVALUATION"))
MUTATIONS = (("C1", "R069_NOT_SQUAREFREE", "root_repeated", "near_repeated"),
             ("C2", "R069_ENDPOINT_ROOT", "end_is_root", "near_end_root"),
             ("C3", "R069_NOT_ISOLATING", "interval_widened", "near_wide"),
             ("C4", "R069_EVALUATION", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    value = {int(e): str(v) for e, v in structure["values"]}
    at = {a[0]: a[1] for n, a in structure["relations"] if n == "at"}
    ends = _sort(structure, "end")
    return {"interval": [value[e] for e in ends], "polynomial": [value[c] for c in _sort(structure, "coef")],
            "values": [value[at[e]] for e in ends]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"coef:{k}", f"degree:{k}"] for k in range(len(positive["polynomial"]))]
