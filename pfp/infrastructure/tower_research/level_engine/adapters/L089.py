# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 089: the engine's outcomes, sources, error cells,
composed cells, rule and bound written as the target checker's weights,
named sources with their errors, composed errors, rule and bound, in
declared outcome order.  Values are written as canonical rationals.
Written against the registered stage-89 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_089"
CLAUSES = (("C1", "R089_ASSUMED_INDEPENDENT"), ("C2", "R089_SUM_BOUND"), ("C3", "R089_VARIANCE_BOUND"),
           ("C4", "R089_COMPOSED_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("outcome", "weighted outcome"), ("source", "error source"), ("cell", "error value"), ("bound", "bound"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.sources", "sources by place", "strings e<k>", "PRESERVED"),)
NEAR = (("own_neg", "R089_ASSUMED_INDEPENDENT"),)
MUTATIONS = (("C1", "R089_ASSUMED_INDEPENDENT", "independence_assumed", "own_neg"),
             ("C2", "R089_SUM_BOUND", "sum_rule", "near_sum"),
             ("C3", "R089_VARIANCE_BOUND", "bound_lowered", "near_bound"),
             ("C4", "R089_COMPOSED_MISMATCH", "composed_changed", "near_composed"))
RULES = (("by_sum", "sum"), ("by_independence", "independent"), ("by_dependence", "dependent"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def _rat(text: str) -> str:
    q = Fraction(text)
    return f"{q.numerator}/{q.denominator}"


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    outcomes, sources = _sort(structure, "outcome"), _sort(structure, "source")
    err = {(a[1], a[2]): value[a[0]] for n, a in rel if n == "err"}
    total = {a[1]: value[a[0]] for n, a in rel if n == "total"}
    rule = next(r for name, r in RULES for n, _ in rel if n == name)
    return {"bound": _rat(value[_sort(structure, "bound")[0]]),
            "composed": [_rat(total[o]) for o in outcomes],
            "rule": rule,
            "sources": [[f"e{k}", [_rat(err[(s, o)]) for o in outcomes]] for k, s in enumerate(sources)],
            "weights": [_rat(value[o]) for o in outcomes]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"source:{k}", f"source:{s[0]}"] for k, s in enumerate(positive["sources"])]
