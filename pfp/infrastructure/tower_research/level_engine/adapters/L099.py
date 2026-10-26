# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 099: the engine's bounds, seed, property, failing input
and shrink trace written as the target checker's generator, seed (``null``
when none is hosted), property, failing input and shrink trace.  The
property's kind is written as its pinned name.  Written against the
registered stage-99 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_099"
CLAUSES = (("C1", "R099_NO_REPLAY_SEED"), ("C2", "R099_REPLAY_MISMATCH"), ("C3", "R099_NOT_A_FAILURE"),
           ("C4", "R099_SHRINK_STEP"), ("C5", "R099_NOT_SHRUNK"))
COEFFICIENT_DOMAIN = {"source": "naturals", "target": "naturals"}
SORTS = (("bound", "generator bound"), ("seed", "seed"), ("property", "property"), ("list", "list"),
         ("entry", "list entry"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.generator", "the pinned generator", "the pinned generator", "PRESERVED"),)
NEAR = (("own_neg", "R099_NO_REPLAY_SEED"),)
MUTATIONS = (("C1", "R099_NO_REPLAY_SEED", "seed_dropped", "own_neg"),
             ("C2", "R099_REPLAY_MISMATCH", "seed_changed", "near_replay"),
             ("C3", "R099_NOT_A_FAILURE", "property_holds", "near_holds"),
             ("C4", "R099_SHRINK_STEP", "step_too_long", "near_step"),
             ("C5", "R099_NOT_SHRUNK", "left_unshrunk", "near_unshrunk"))
KINDS = ("sum_below", "no_value")


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
    items = _sort(structure, "entry")

    def entries(lst: int) -> list[int]:
        mine = {a[0] for n, a in rel if n == "of" and a[1] == lst}
        return [value[e] for e in items if e in mine]

    lists = [entries(lst) for lst in _sort(structure, "list")]
    bounds, prop, seeds = _sort(structure, "bound"), _sort(structure, "property"), _sort(structure, "seed")
    return {"failing_input": lists[0], "generator": {"max_len": value[bounds[0]], "max_value": value[bounds[1]]},
            "property": [KINDS[value[prop[0]]], value[prop[1]]], "seed": value[seeds[0]] if seeds else None,
            "shrink_trace": lists[1:]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [["list:0", "failing_input"]] + [[f"list:{k + 1}", f"trace:{k}"] for k in range(len(positive["shrink_trace"]))]
