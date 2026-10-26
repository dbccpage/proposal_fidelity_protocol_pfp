# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 022: the engine's objects, fibres, arrows, tables,
identities and composites written as the target checker's objects, arrows,
identities and composites.  Objects, terms and arrows are named ``o<k>``,
``t<k>`` and ``a<k>`` by their positions; tables and fibres are sorted.
Written against the registered stage-22 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_022"
CLAUSES = (("C1", "R022_WRONG_FIBRE"), ("C2", "R022_PARTIAL_TABLE"), ("C3", "R022_IDENTITY_LAW"),
           ("C4", "R022_NON_FUNCTORIAL"), ("C5", "R022_BASE_NOT_CLOSED"))
COEFFICIENT_DOMAIN = {"source": "finite maps of terms", "target": "finite maps of terms"}
SORTS = (("object", "object"), ("term", "term"), ("arrow", "arrow"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = ""
LOSS_ROWS = (("target.associativity", "not decided", "not decided", "PRESERVED"),)
NEAR = (("own_neg", "R022_WRONG_FIBRE"),)
MUTATIONS = (("C1", "R022_WRONG_FIBRE", "image_misplaced", "own_neg"),
             ("C2", "R022_PARTIAL_TABLE", "table_short", "near_partial"),
             ("C3", "R022_IDENTITY_LAW", "identity_moves", "near_identity"),
             ("C4", "R022_NON_FUNCTORIAL", "mut", "mut"),
             ("C5", "R022_BASE_NOT_CLOSED", "composite_dropped", "near_unclosed"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def _names(structure: dict[str, Any]) -> dict[int, str]:
    out = {}
    for sort, prefix in (("object", "o"), ("term", "t"), ("arrow", "a")):
        for k, e in enumerate(_sort(structure, sort)):
            out[e] = f"{prefix}{k}"
    return out


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    nm = _names(structure)
    rel = [(n, list(a)) for n, a in structure["relations"]]
    runs = {a[0]: (a[1], a[2]) for n, a in rel if n == "runs"}
    return {
        "arrows": [[nm[a], nm[runs[a][0]], nm[runs[a][1]],
                    sorted([nm[r[1]], nm[r[2]]] for n, r in rel if n == "sends" and r[0] == a)]
                   for a in _sort(structure, "arrow")],
        "composites": sorted([nm[a[0]], nm[a[1]], nm[a[2]]] for n, a in rel if n == "composite"),
        "identities": sorted([nm[a[0]], nm[a[1]]] for n, a in rel if n == "identity"),
        "objects": [[nm[o], sorted(nm[a[0]] for n, a in rel if n == "over" and a[1] == o)]
                    for o in _sort(structure, "object")],
    }


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def squares(source: object, positive: object) -> list[tuple[str, object, object]]:
    """Reindexing: each hosted table carried through the names (left) against
    the positive's arrow tables (right)."""
    assert isinstance(source, dict) and isinstance(positive, dict)
    nm = _names(source)
    rel = [(n, list(a)) for n, a in source["relations"]]
    carried = [sorted([nm[r[1]], nm[r[2]]] for n, r in rel if n == "sends" and r[0] == a)
               for a in _sort(source, "arrow")]
    read = [sorted(a[3]) for a in positive["arrows"]]
    return [("reindexing", carried, read)]


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"arrow:{k}", f"arrow:{a[0]}"] for k, a in enumerate(positive["arrows"])]
