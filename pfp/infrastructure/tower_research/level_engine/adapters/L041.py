# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 041: the engine's context, copyable kinds, term tree
and declared type written as the target checker's context, duplicable
kinds, term (``var``, ``pair``, ``dup`` for a copy, ``drop`` for a discard)
and type.  Names and kinds are written ``v<k>`` and ``k<k>`` by their
positions.  Written against the registered stage-41 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_041"
CLAUSES = (("C1", "R041_UNTYPED"), ("C2", "R041_DUPLICATE"), ("C3", "R041_UNUSED"),
           ("C4", "R041_CONTRACTION_KIND"), ("C5", "R041_TYPE_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "use counts", "target": "use counts"}
SORTS = (("name", "variable"), ("kind", "kind"), ("node", "term node"), ("tnode", "type node"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.names", "names and kinds by position", "strings v<k>, k<k>", "PRESERVED"),)
NEAR = (("own_neg", "R041_DUPLICATE"),)
MUTATIONS = (("C1", "R041_UNTYPED", "name_unbound", "near_unbound"),
             ("C2", "R041_DUPLICATE", "name_twice", "near_twice"),
             ("C3", "R041_UNUSED", "name_unused", "near_unused"),
             ("C4", "R041_CONTRACTION_KIND", "mut", "mut"),
             ("C5", "R041_TYPE_MISMATCH", "type_changed", "near_type"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    names, kinds = _sort(structure, "name"), _sort(structure, "kind")
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def nm(e: int) -> str:
        return f"v{names.index(e)}"

    def kd(e: int) -> str:
        return f"k{kinds.index(e)}"

    def tm(n: int) -> Any:
        for r, a in rel:
            if a[0] != n:
                continue
            if r == "var":
                return ["var", nm(a[1])]
            if r == "pair":
                return ["pair", tm(a[1]), tm(a[2])]
            if r == "copy":
                return ["dup", nm(a[1]), nm(a[2]), nm(a[3]), tm(a[4])]
            if r == "discard":
                return ["drop", nm(a[1]), tm(a[2])]
        raise KeyError(n)

    leaves = {a[0]: a[1] for r, a in rel if r == "leaf"}
    boths = {a[0]: (a[1], a[2]) for r, a in rel if r == "both"}

    def ty(t: int) -> Any:
        return kd(leaves[t]) if t in leaves else [ty(boths[t][0]), ty(boths[t][1])]

    return {"context": sorted([nm(a[0]), kd(a[1])] for r, a in rel if r == "in_context"),
            "duplicable": sorted(kd(a[0]) for r, a in rel if r == "copyable"),
            "term": tm(next(a[0] for r, a in rel if r == "root")),
            "type": ty(next(a[0] for r, a in rel if r == "declared"))}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"name:{k}", f"variable:{c[0]}"] for k, c in enumerate(positive["context"])]
