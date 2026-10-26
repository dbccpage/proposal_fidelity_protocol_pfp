# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 007: the engine's hosted letters, steps, words and rings
written as the target checker's alphabet, transition table and orbit
records.  A letter is written as its position in the declared order of
letters (``"0"``, ``"1"``, ...); a word as its two letters; the length is two,
the payload's declared class; each ring with a lead becomes one orbit record
whose members are its words in the declared order of words, whose
representative is its lead and whose period is its declared span.  Written
against the registered stage-7 checker (``b697efad``).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_007"
CLAUSES = (("C1", "R007_NOT_ALLOWED"), ("C2", "R007_ORBIT_NOT_CLOSED"), ("C3", "R007_PERIOD_MISMATCH"),
           ("C4", "R007_NONCANONICAL_REP"), ("C5", "R007_MISSING_ORBIT"))
COEFFICIENT_DOMAIN = {"source": "finite structure", "target": "words over an alphabet"}
SORTS = (("letter", "symbol"), ("word", "word"), ("ring", "orbit record"), ("count", "period"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.length", "words of length two, the declared class", "length 2 only", "WEAKENED"),
    ("target.symbol_names", "letters as elements in a declared order", "one-character position names",
     "PRESERVED"),
)
NEAR = (("near_lead", "R007_NONCANONICAL_REP"), ("near_span", "R007_PERIOD_MISMATCH"),
        ("near_step", "R007_NOT_ALLOWED"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def shift_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    letters, words, rings = _sort(structure, "letter"), _sort(structure, "word"), _sort(structure, "ring")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(name, list(args)) for name, args in structure["relations"]]
    name = {a: str(letters.index(a)) for a in letters}
    first = {a[0]: a[1] for n, a in rel if n == "first"}
    second = {a[0]: a[1] for n, a in rel if n == "second"}
    spell = {w: name[first[w]] + name[second[w]] for w in words if w in first and w in second}
    orbits = []
    for r in rings:
        lead = [a[1] for n, a in rel if n == "lead" and a[0] == r]
        span = [a[1] for n, a in rel if n == "span" and a[0] == r]
        if not lead:
            continue
        members = [spell[w] for w in words if ["lies_in", [w, r]] in [[n, a] for n, a in rel]]
        orbits.append({"members": members, "period": int(value[span[0]].split("/")[0]),
                       "representative": spell[lead[0]]})
    steps = sorted([name[a[0]], name[a[1]]] for n, a in rel if n == "step")
    return {"alphabet": [name[a] for a in letters], "length": 2, "orbits": orbits, "transitions": steps}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": shift_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": shift_of(by[fid])}
            for fid, code in NEAR]
    out += [
        {"clause": "C1", "expected_code": "R007_NOT_ALLOWED", "id": "forbidden_step", "kind": "decisive_mutation",
         "payload": shift_of(by["near_step"]), "repair": "pos"},
        {"clause": "C2", "expected_code": "R007_ORBIT_NOT_CLOSED", "id": "mut", "kind": "decisive_mutation",
         "payload": shift_of(by["mut"]), "repair": "pos"},
        {"clause": "C3", "expected_code": "R007_PERIOD_MISMATCH", "id": "constant_span_two",
         "kind": "decisive_mutation", "payload": shift_of(by["own_neg"]), "repair": "pos"},
        {"clause": "C4", "expected_code": "R007_NONCANONICAL_REP", "id": "greater_lead", "kind": "decisive_mutation",
         "payload": shift_of(by["near_lead"]), "repair": "pos"},
        {"clause": "C5", "expected_code": "R007_MISSING_ORBIT", "id": "ring_absent", "kind": "decisive_mutation",
         "payload": shift_of(by["near_missing_ring"]), "repair": "pos"},
    ]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"element:{i}", f"symbol:{a}"] for i, a in enumerate(positive["alphabet"])]
