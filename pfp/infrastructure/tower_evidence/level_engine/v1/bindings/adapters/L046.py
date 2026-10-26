"""Adapter for level 046: the engine's program, evaluators and results
written as the target checker's input, base, step, measure, interpreter,
confirmations and output.  Numbers are written as their hosted naturals;
evaluators as their hosted digests, never recomputed here; base rows and
confirmations are sorted.  Written against the registered stage-46 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_046"
CLAUSES = (("C1", "R046_NO_DECREASE"), ("C2", "R046_NO_EXTERNAL_CHECKER"), ("C3", "R046_OUTPUT_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "naturals, and SHA-256 digests as exact 32-byte values",
                      "target": "naturals, and SHA-256 digests as exact 32-byte values"}
SORTS = (("number", "natural"), ("evaluator", "evaluator digest"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.self_description", "no self-description is hosted", "not modelled by the checker",
              "PRESERVED"),)
NEAR = (("own_neg", "R046_NO_DECREASE"),)
MUTATIONS = (("C1", "R046_NO_DECREASE", "step_zero", "near_still"),
             ("C2", "R046_NO_EXTERNAL_CHECKER", "self_confirmed", "near_self"),
             ("C3", "R046_OUTPUT_MISMATCH", "mut", "mut"))


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    value = {int(e): int(Fraction(str(v))) for e, v in structure["values"]}
    digest = {int(e): str(d) for e, d in structure["digests"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def one(name: str) -> list[int]:
        return next(a for n, a in rel if n == name)

    return {"base": sorted([value[a[0]], value[a[1]]] for n, a in rel if n == "base"),
            "confirmations": sorted([digest[a[0]], value[a[1]]] for n, a in rel if n == "confirms"),
            "input": value[one("input")[0]], "interpreter": digest[one("interpreter")[0]],
            "measure": [value[x] for x in one("measure")], "output": value[one("output")[0]],
            "step": [value[x] for x in one("step")]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [["evaluator:0", "interpreter"]] + [[f"evaluator:{k + 1}", f"confirmation:{k}"]
                                               for k in range(len(positive["confirmations"]))]
