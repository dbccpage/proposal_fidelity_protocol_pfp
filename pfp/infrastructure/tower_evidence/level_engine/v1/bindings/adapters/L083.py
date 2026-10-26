"""Adapter for level 083: the engine's records, seals and pins written as
the target checker's sources and derived records, in declared order.
Records are named ``r<k>`` by place (the names their content digests are
computed over); an input that is no record is written ``x<e>``; digests
are written as hosted, never recomputed here.  Written against the
registered stage-83 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_083"
CLAUSES = (("C1", "R083_MISSING_SOURCE"), ("C2", "R083_VALUE"), ("C3", "R083_RECORD_DIGEST"),
           ("C4", "R083_INPUT_CHANGED"))
COEFFICIENT_DOMAIN = {"source": "exact rationals and SHA-256 digests", "target": "exact rationals and SHA-256 digests"}
SORTS = (("record", "record"), ("seal", "record digest"), ("pin", "pinned digest"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.names", "records by place", "strings r<k>", "PRESERVED"),)
NEAR = (("own_neg", "R083_MISSING_SOURCE"),)
MUTATIONS = (("C1", "R083_MISSING_SOURCE", "input_later", "near_later"),
             ("C2", "R083_VALUE", "value_changed", "near_value"),
             ("C3", "R083_RECORD_DIGEST", "seal_changed", "near_seal"),
             ("C4", "R083_INPUT_CHANGED", "pin_changed", "near_pin"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    records = _sort(structure, "record")
    value = {int(e): str(v) for e, v in structure["values"]}
    digest = {int(e): str(d) for e, d in structure["digests"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    seal = {a[0]: digest[a[1]] for n, a in rel if n == "sealed"}
    sources = {a[0] for n, a in rel if n == "source"}
    op = {a[0]: ("sum" if n == "sums" else "product") for n, a in rel if n in ("sums", "multiplies")}

    def nm(e: int) -> str:
        return f"r{records.index(e)}" if e in records else f"x{e}"

    return {"derived": [[nm(r), op[r], [[nm(a[1]), digest[a[2]]] for n, a in rel if n == "reads" and a[0] == r],
                         value[r], seal[r]] for r in records if r not in sources],
            "sources": [[nm(r), value[r], seal[r]] for r in records if r in sources]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"record:{s[0]}", f"source:{s[0]}"] for s in positive["sources"]] + [
        [f"record:{d[0]}", f"derived:{d[0]}"] for d in positive["derived"]]
