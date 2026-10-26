"""Adapter for level 081: the engine's columns, records, releases, ledger,
budget and threshold written as the target checker's columns, records,
k, budget and releases.  Columns and tokens are named ``col<k>`` and
``t<k>`` by their positions; records and releases follow the declared
order; a release's attributes are in column order.  Written against the
registered stage-81 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_081"
CLAUSES = (("C1", "R081_BUDGET_EXCEEDED"), ("C2", "R081_LEDGER_MISMATCH"), ("C3", "R081_JOINT_CLASS_TOO_SMALL"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("column", "column"), ("record", "record"), ("token", "value"), ("release", "release"),
         ("ledger", "remaining"), ("budget", "budget"), ("threshold", "k"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.noise", "no noise mechanism", "no noise mechanism", "PRESERVED"),)
NEAR = (("own_neg", "R081_BUDGET_EXCEEDED"), ("mut", "R081_LEDGER_MISMATCH"))
MUTATIONS = (("C1", "R081_BUDGET_EXCEEDED", "release_overspends", "near_over"),
             ("C2", "R081_LEDGER_MISMATCH", "remainder_changed", "near_ledger"),
             ("C3", "R081_JOINT_CLASS_TOO_SMALL", "record_moves", "near_class"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    cols, tokens = _sort(structure, "column"), _sort(structure, "token")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    cell = {(a[0], a[1]): a[2] for n, a in rel if n == "cell"}
    after = {a[0]: a[1] for n, a in rel if n == "after"}
    return {
        "budget": value[_sort(structure, "budget")[0]],
        "columns": [f"col{k}" for k in range(len(cols))],
        "k": int(Fraction(value[_sort(structure, "threshold")[0]])),
        "records": [[f"t{tokens.index(cell[(r, c)])}" for c in cols] for r in _sort(structure, "record")],
        "releases": [{"attributes": [f"col{cols.index(c)}" for c in cols if ["reveals", [q, c]] in
                                     [[n, a] for n, a in rel]],
                      "cost": value[q], "remaining": value[after[q]]} for q in _sort(structure, "release")],
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
    return [[f"column:{k}", f"column:{c}"] for k, c in enumerate(positive["columns"])]
