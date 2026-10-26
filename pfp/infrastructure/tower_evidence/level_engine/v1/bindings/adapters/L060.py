"""Adapter for level 060: the engine's checks, errors and claimed readings
written as the target checker's words and readings.  A word is written as
its two parts, each a string of one bit per site in declared site order; a
reading is a string of one bit per check in declared check order.  Written
against the registered stage-60 checker.

C1 (a word of the wrong length) is not claimed: a hosted word has one bit
per site by construction, so no engine fixture can state a short word.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_060"
CLAUSES = (("C2", "R060_ANTICOMMUTING"), ("C3", "R060_NOT_DISTINCT"), ("C4", "R060_READING"))
COEFFICIENT_DOMAIN = {"source": "two-part words over sites", "target": "two-part words over sites"}
SORTS = (("site", "site"), ("check", "check word"), ("error", "error word"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.word_length", "one bit per site by construction", "a length refusal by code", "WEAKENED"),)
NEAR = (("own_neg", "R060_ANTICOMMUTING"),)
MUTATIONS = (("C2", "R060_ANTICOMMUTING", "checks_anticommute", "near_anti"),
             ("C3", "R060_NOT_DISTINCT", "error_reads_nothing", "near_blind"), ("C4", "R060_READING", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def code_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    sites, checks, errors = _sort(structure, "site"), _sort(structure, "check"), _sort(structure, "error")
    rel = {(n, tuple(a)) for n, a in structure["relations"]}

    def word(kind: str, w: int) -> list[str]:
        return ["".join(str(int((f"{kind}_{p}", (w, s)) in rel)) for s in sites) for p in ("x", "z")]

    return {"checks": [word("check", q) for q in checks], "errors": [word("error", e) for e in errors],
            "readings": ["".join(str(int(("reads", (e, q)) in rel)) for q in checks) for e in errors],
            "sites": len(sites)}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": code_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": code_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": code_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"site:{k}", f"bit:{k}"] for k in range(positive["sites"])]
