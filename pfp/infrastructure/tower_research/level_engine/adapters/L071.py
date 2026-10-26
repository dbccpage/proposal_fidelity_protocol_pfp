# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 071: the engine's coefficients, limit, rate, moduli and
samples written as the target checker's numerator, denominator, limit,
rate (``null`` when none is hosted), start, modulus and checkpoints.  Rows
are sorted.  Written against the registered stage-71 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_071"
CLAUSES = (("C1", "R071_CHECKPOINTS_ONLY"), ("C2", "R071_DENOMINATOR"), ("C3", "R071_BOUND_FAILS"),
           ("C4", "R071_MODULUS"), ("C5", "R071_CHECKPOINT_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("top", "numerator coefficient"), ("bottom", "denominator coefficient"), ("limit", "limit"),
         ("rate", "rate"), ("modulus", "modulus"), ("index", "index"), ("sample", "checkpoint"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.limit_object", "no limit object is formed", "no limit object is formed", "PRESERVED"),)
NEAR = (("own_neg", "R071_CHECKPOINTS_ONLY"), ("near_far", "R071_BOUND_FAILS"))
MUTATIONS = (("C1", "R071_CHECKPOINTS_ONLY", "rate_dropped", "own_neg"),
             ("C2", "R071_DENOMINATOR", "denominator_vanishes", "near_zero"),
             ("C3", "R071_BOUND_FAILS", "rate_too_fast", "near_slow"),
             ("C4", "R071_MODULUS", "modulus_too_small", "near_modulus"),
             ("C5", "R071_CHECKPOINT_MISMATCH", "mut", "mut"))


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

    def nat(e: int) -> int:
        return int(Fraction(value[e]))

    rate = _sort(structure, "rate")
    return {
        "checkpoints": sorted([nat(a[1]), value[a[0]]] for n, a in rel if n == "at"),
        "denominator": [value[e] for e in _sort(structure, "bottom")],
        "limit": value[_sort(structure, "limit")[0]],
        "modulus": sorted([value[a[0]], nat(a[1])] for n, a in rel if n == "after"),
        "numerator": [value[e] for e in _sort(structure, "top")],
        "rate": value[rate[0]] if rate else None,
        "start": next(nat(a[0]) for n, a in rel if n == "starts"),
    }


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"top:{k}", f"numerator:{k}"] for k in range(len(positive["numerator"]))] + [
        [f"bottom:{k}", f"denominator:{k}"] for k in range(len(positive["denominator"]))]
