# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 087: the engine's pinned check, base list and challenge
lists written as the target checker's subject, base and challenges (in
declared order).  The check's number is written as its pinned name.
Written against the registered stage-87 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_087"
CLAUSES = (("C1", "R087_BASE_REFUSED"), ("C2", "R087_NOT_A_MUTATION"), ("C3", "R087_NEGATIVE_STILL_PASSES"),
           ("C4", "R087_RESULT_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "lists of naturals", "target": "lists of naturals"}
SORTS = (("list", "fixture"), ("entry", "list entry"), ("subject", "pinned check"), ("bound", "sum bound"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.subjects", "three pinned checks", "three pinned checks", "PRESERVED"),)
NEAR = (("own_neg", "R087_NEGATIVE_STILL_PASSES"), ("near_result", "R087_RESULT_MISMATCH"))
MUTATIONS = (("C1", "R087_BASE_REFUSED", "base_refused", "near_base"),
             ("C2", "R087_NOT_A_MUTATION", "mutant_is_base", "near_same"),
             ("C3", "R087_NEGATIVE_STILL_PASSES", "mutant_passes", "near_passes"),
             ("C4", "R087_RESULT_MISMATCH", "mut", "mut"))
SUBJECTS = ("nondecreasing", "distinct", "bounded_sum")


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    value = {int(e): int(Fraction(str(v))) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    lists, items = _sort(structure, "list"), _sort(structure, "entry")

    def entries(lst: int) -> list[int]:
        mine = {a[0] for n, a in rel if n == "of" and a[1] == lst}
        return [value[e] for e in items if e in mine]

    subject = [SUBJECTS[value[_sort(structure, "subject")[0]]]]
    bounds = _sort(structure, "bound")
    if bounds:
        subject.append(value[bounds[0]])  # type: ignore[arg-type]
    result = {a[0]: ("PASS" if n == "recorded_pass" else "FAIL") for n, a in rel
              if n in ("recorded_pass", "recorded_fail")}
    return {"base": entries(lists[0]), "challenges": [{"mutant": entries(m), "result": result[m]} for m in lists[1:]],
            "subject": subject}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [["list:0", "base"]] + [[f"list:{k + 1}", f"challenge:{k}"] for k in range(len(positive["challenges"]))]
