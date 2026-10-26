# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 100: the engine's claims, tests, obligations, frontier
and release written as the target checker's release manifest.  Claims and
tests are named ``c<k>`` and ``t<k>`` by position; an obligation's kind is
written from its place in the closed list (an untyped place as ``KIND<v>``)
with the note ``held``; a link to anything that is not a declared test is
written ``undeclared<e>``; the release writes ``final`` and an authority
effect only when it hosts them.  Written against the registered stage-100
checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_100"
CLAUSES = (("C1", "R100_SELF_CERTIFICATION"), ("C2", "R100_UNCOVERED_CLAIM"), ("C3", "R100_UNTYPED_OBLIGATION"),
           ("C4", "R100_DANGLING_REFERENCE"), ("C5", "R100_FRONTIER_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "finite names", "target": "finite names"}
SORTS = (("claim", "claim"), ("test", "test"), ("kind", "obligation type"), ("release", "release"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.test_semantics", "links resolve; testing is not decided", "not decided", "PRESERVED"),)
NEAR = (("own_neg", "R100_SELF_CERTIFICATION"), ("near_authority", "R100_SELF_CERTIFICATION"))
MUTATIONS = (("C1", "R100_SELF_CERTIFICATION", "self_certified", "own_neg"),
             ("C2", "R100_UNCOVERED_CLAIM", "claim_uncovered", "near_uncovered"),
             ("C3", "R100_UNTYPED_OBLIGATION", "kind_untyped", "near_untyped"),
             ("C4", "R100_DANGLING_REFERENCE", "link_dangles", "near_dangling"),
             ("C5", "R100_FRONTIER_MISMATCH", "mut", "mut"))
TYPES = ("OPEN", "CONJECTURE", "BLOCKED", "OUT_OF_SCOPE")


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    claims, tests = _sort(structure, "claim"), _sort(structure, "test")
    value = {int(e): int(Fraction(str(v))) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def test(e: int) -> str:
        return f"t{tests.index(e)}" if e in tests else f"undeclared{e}"

    def kind(e: int) -> str:
        v = value.get(e, -1)
        return TYPES[v] if 0 <= v < len(TYPES) else f"KIND{v}"

    return {"authority_effect": "granted" if any(n == "grants_authority" for n, _ in rel) else "None",
            "claims": [f"c{k}" for k in range(len(claims))],
            "evidence": sorted([f"c{claims.index(a[0])}", test(a[1])] for n, a in rel if n == "evidence"),
            "frontier": sorted(f"c{claims.index(a[0])}" for n, a in rel if n == "frontier"),
            "open": sorted([f"c{claims.index(a[0])}", kind(a[1]), "held"] for n, a in rel if n == "held"),
            "self_certification": "final" if any(n == "self_certified" for n, _ in rel) else "none",
            "tests": [f"t{k}" for k in range(len(tests))]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"claim:{k}", f"claim:{c}"] for k, c in enumerate(positive["claims"])]
