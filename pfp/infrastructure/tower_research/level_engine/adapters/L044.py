# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 044: the engine's domain and triples written as the
target checker's domain and claims.  Claims are named by their positions in
the declared order; a step is written ``["add", k]``; a proved claim's
witness is its cases in ascending order, or ``null`` when no witness is
given; a refuted claim's witness is its one case; any other claim stands
pending with no witness.  Written against the registered stage-44 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_044"
CLAUSES = (("C1", "R044_NO_WITNESS"), ("C2", "R044_WITNESS_INCOMPLETE"), ("C3", "R044_WITNESS_FAILS"),
           ("C4", "R044_BAD_COUNTEREXAMPLE"))
COEFFICIENT_DOMAIN = {"source": "natural numbers as exact values", "target": "natural numbers"}
SORTS = (("num", "natural number"), ("claim", "claim"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.names", "claims as elements", "their positions as names", "PRESERVED"),)
NEAR = (("near_bad_counter", "R044_BAD_COUNTEREXAMPLE"),)
MUTATIONS = (("C1", "R044_NO_WITNESS", "proved_without_witness", "own_neg"),
             ("C2", "R044_WITNESS_INCOMPLETE", "case_left_out", "near_incomplete"),
             ("C3", "R044_WITNESS_FAILS", "case_leaves_post", "near_fails"), ("C4", "R044_BAD_COUNTEREXAMPLE", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def triples_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    claims = _sort(structure, "claim")
    value = {int(e): int(Fraction(v)) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def one(name: str, c: int) -> list[int]:
        return next([value[x] for x in a[1:]] for n, a in rel if n == name and a[0] == c)

    def has(name: str, c: int) -> bool:
        return any(n == name and a[0] == c for n, a in rel)

    out = []
    for k, c in enumerate(claims):
        cases = sorted(value[a[1]] for n, a in rel if n == "case" and a[0] == c)
        if has("proved", c):
            standing, witness = "PROVED", (cases if has("certified", c) else None)
        elif has("refuted", c):
            standing, witness = "REFUTED", cases[0]
        else:
            standing, witness = "PENDING", None
        out.append([f"c{k}", one("pre", c), ["add", one("adds", c)[0]], one("post", c), standing, witness])
    domain = next([value[a[0]], value[a[1]]] for n, a in rel if n == "domain")
    return {"claims": out, "domain": domain}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": triples_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": triples_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": triples_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"claim:{k}", f"claim:{c[0]}"] for k, c in enumerate(positive["claims"])]
