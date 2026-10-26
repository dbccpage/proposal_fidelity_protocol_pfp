# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 066: the engine's terms and cancellation record written
as the target checker's terms, pairs, rest and total.  Terms are indexed by
their position in the declared order; each pair and each rest term is
written by those positions.  Written against the registered stage-66
checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_066"
CLAUSES = (("C1", "R066_NOT_A_PARTITION"), ("C2", "R066_NOT_OPPOSITE"), ("C3", "R066_UNPAIRED_REST"),
           ("C4", "R066_TOTAL"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("term", "term index"), ("val", "rational"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.term_order", "terms as elements", "their positions as indices", "PRESERVED"),)
NEAR = (("own_neg", "R066_UNPAIRED_REST"),)
MUTATIONS = (("C1", "R066_NOT_A_PARTITION", "term_unplaced", "near_partition"),
             ("C2", "R066_NOT_OPPOSITE", "pair_not_opposite", "near_opposite"),
             ("C3", "R066_UNPAIRED_REST", "rest_both_signs", "near_mixed"), ("C4", "R066_TOTAL", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def record_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    ts = _sort(structure, "term")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    weight = {a[0]: value[a[1]] for n, a in rel if n == "weight"}
    return {"pairs": [[ts.index(a[0]), ts.index(a[1])] for n, a in rel if n == "paired"],
            "rest": [ts.index(a[0]) for n, a in rel if n == "rest"],
            "terms": [weight[t] for t in ts],
            "total": next(value[a[0]] for n, a in rel if n == "total")}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": record_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": record_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": record_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"term:{k}", f"index:{k}"] for k in range(len(positive["terms"]))]
