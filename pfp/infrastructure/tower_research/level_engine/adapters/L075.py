# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 075: the engine's rows, tables, delta and views written
as the target checker's width, base, new base, delta, view, old view and
patched view.  Tokens are named ``t<k>`` by their positions; a row is its
tokens in column order; tables are sorted; the view's column is its
position.  Written against the registered stage-75 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_075"
CLAUSES = (("C1", "R075_OLD_VIEW"), ("C2", "R075_DELTA_NOT_APPLICABLE"), ("C3", "R075_DELETION_OMITTED"),
           ("C4", "R075_DELTA_MISMATCH"), ("C5", "R075_STALE_VIEW"))
COEFFICIENT_DOMAIN = {"source": "sets of rows", "target": "sets of rows"}
SORTS = (("column", "column index"), ("token", "cell value"), ("row", "row"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.multiplicities", "set semantics", "set semantics", "PRESERVED"),)
NEAR = (("own_neg", "R075_DELETION_OMITTED"),)
MUTATIONS = (("C1", "R075_OLD_VIEW", "old_view_short", "near_old_view"),
             ("C2", "R075_DELTA_NOT_APPLICABLE", "insert_present", "near_inserted_there"),
             ("C3", "R075_DELETION_OMITTED", "deletion_omitted", "near_omitted"),
             ("C4", "R075_DELTA_MISMATCH", "insertion_omitted", "near_unexplained"),
             ("C5", "R075_STALE_VIEW", "mut", "mut"))


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
    rel = [(n, list(a)) for n, a in structure["relations"]]
    cell = {(a[0], a[1]): a[2] for n, a in rel if n == "holds"}

    def row(r: int) -> list[str]:
        return [f"t{tokens.index(cell[(r, c)])}" for c in cols]

    def table(name: str) -> list[list[str]]:
        return sorted(row(a[0]) for n, a in rel if n == name)

    return {"base": table("old"), "delta": {"deleted": table("deleted"), "inserted": table("inserted")},
            "new_base": table("new"), "old_view": table("old_view"), "patched_view": table("patched"),
            "view": {"column": cols.index(next(a[0] for n, a in rel if n == "view_on")),
                     "value": f"t{tokens.index(next(a[0] for n, a in rel if n == 'view_is'))}"},
            "width": len(cols)}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"row:{k}", "row:" + ",".join(r)] for k, r in enumerate(positive["base"])]
