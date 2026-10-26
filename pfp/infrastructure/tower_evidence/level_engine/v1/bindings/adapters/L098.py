"""Adapter for level 098: the engine's two sides, cases, merges and recorded
disagreements written as the target checker's function (``round``), the
two implementation names, cases, merged rows and disagreements, in declared
case order.  Inputs are written as canonical rationals.  Written against
the registered stage-98 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_098"
CLAUSES = (("C1", "R098_NOT_INDEPENDENT"), ("C2", "R098_OUTPUT_MISMATCH"), ("C3", "R098_SILENT_MERGE"),
           ("C4", "R098_DISAGREEMENT_RECORD"))
COEFFICIENT_DOMAIN = {"source": "exact rationals and integers", "target": "exact rationals and integers"}
SORTS = (("impl", "implementation"), ("case", "input"), ("integer", "output"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.functions", "rounding only", "three pinned functions", "WEAKENED"),)
NEAR = (("own_neg", "R098_SILENT_MERGE"), ("mut", "R098_DISAGREEMENT_RECORD"))
MUTATIONS = (("C1", "R098_NOT_INDEPENDENT", "same_side", "near_same"),
             ("C2", "R098_OUTPUT_MISMATCH", "output_changed", "near_output"),
             ("C3", "R098_SILENT_MERGE", "differing_merged", "near_merge"),
             ("C4", "R098_DISAGREEMENT_RECORD", "disagreement_dropped", "near_unrecorded"))
NAMES = ("half_up", "half_even")


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

    def integer(e: int) -> int:
        return int(Fraction(value[e]))

    oa = {a[0]: integer(a[1]) for n, a in rel if n == "out_a"}
    ob = {a[0]: integer(a[1]) for n, a in rel if n == "out_b"}
    cases = _sort(structure, "case")
    return {"cases": [[value[c], oa[c], ob[c]] for c in cases],
            "disagreements": [value[c] for c in cases if ["disagrees", [c]] in [[n, a] for n, a in rel]],
            "function": "round",
            "impl_a": NAMES[integer(next(a[0] for n, a in rel if n == "side_a"))],
            "impl_b": NAMES[integer(next(a[0] for n, a in rel if n == "side_b"))],
            "merged": [[value[a[0]], integer(a[1])] for c in cases for n, a in rel if n == "merged" and a[0] == c]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"case:{k}", f"case:{c[0]}"] for k, c in enumerate(positive["cases"])]
