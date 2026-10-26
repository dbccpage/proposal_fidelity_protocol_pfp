# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 070: the engine's table, claimed coefficients and
claimed roots written as the target checker's table, polynomial and roots.
The table follows the declared order of slots, and a claim with no slot is
written with no table (``null``); the coefficients are written in ascending
power; the roots, a set, are written in ascending value.  Written against
the registered stage-70 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_070"
CLAUSES = (("C1", "R070_NO_TABLE"), ("C2", "R070_POLYNOMIAL"), ("C3", "R070_NOT_A_ROOT"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("slot", "table index"), ("val", "rational"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.root_order", "claimed roots as a set", "a list in ascending value", "PRESERVED"),)
NEAR = (("own_neg", "R070_NO_TABLE"),)
MUTATIONS = (("C1", "R070_NO_TABLE", "table_withdrawn", "near_no_table"),
             ("C2", "R070_POLYNOMIAL", "coefficient_off", "near_coef"), ("C3", "R070_NOT_A_ROOT", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    slots = _sort(structure, "slot")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    entry = {(a[0], a[1]): value[a[2]] for n, a in rel if n == "entry"}
    coef = {int(Fraction(value[a[0]])): value[a[1]] for n, a in rel if n == "coef"}
    return {"polynomial": [coef[p] for p in sorted(coef)],
            "roots": sorted((value[a[0]] for n, a in rel if n == "root"), key=Fraction),
            "table": [[entry[(i, j)] for j in slots] for i in slots] if slots else None}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"slot:{k}", f"index:{k}"] for k in range(len(positive["table"]))]
