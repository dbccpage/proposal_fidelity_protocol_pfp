# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 073: the engine's integrand, constant, start and listed
sums written as the target checker's integrand (ascending), constant
(``null`` when none is hosted), start and depths (sorted).  Written against
the registered stage-73 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_073"
CLAUSES = (("C1", "R073_NO_RATE"), ("C2", "R073_SUM_MISMATCH"), ("C3", "R073_BOUND_FAILS"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("coef", "integrand coefficient"), ("constant", "constant"), ("index", "depth"), ("sum", "left-end sum"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.continuum", "no continuum object is formed", "no continuum object is formed",
              "PRESERVED"),)
NEAR = (("own_neg", "R073_NO_RATE"), ("near_sum", "R073_SUM_MISMATCH"), ("near_far", "R073_BOUND_FAILS"))
MUTATIONS = (("C1", "R073_NO_RATE", "constant_dropped", "own_neg"),
             ("C2", "R073_SUM_MISMATCH", "mut", "mut"),
             ("C3", "R073_BOUND_FAILS", "constant_too_small", "near_tight"))


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
    rel = [(n, list(a)) for n, a in structure["relations"]]
    const = _sort(structure, "constant")
    return {"constant": value[const[0]] if const else None,
            "depths": sorted([int(Fraction(value[a[1]])), value[a[0]]] for n, a in rel if n == "at"),
            "integrand": [value[c] for c in _sort(structure, "coef")],
            "start": next(int(Fraction(value[a[0]])) for n, a in rel if n == "starts")}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"coef:{k}", f"degree:{k}"] for k in range(len(positive["integrand"]))]
