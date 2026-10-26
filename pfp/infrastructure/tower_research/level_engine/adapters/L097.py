# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 097: the engine's base list, invariants, mutants and
recorded kills written as the target checker's fixture, invariants, mutants
and kill matrix.  Entries, invariants and mutants are in declared order; a
mutant's position is the place of the entry it acts at (an element that is
no entry is written past the list's end, so the checker refuses it by its
schema); operator and invariant names travel as hosted texts; a kill-matrix
row is the set of invariants recorded as killing the mutant, written as
their names in sorted order.  Nothing is applied or evaluated here.
Written against the registered stage-97 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_097"
CLAUSES = (("C1", "R097_BASE_FAILS"), ("C2", "R097_NOT_CHANGED"), ("C3", "R097_SURVIVING_MUTANT"),
           ("C4", "R097_WRONG_INVARIANT"), ("C5", "R097_KILL_MATRIX"))
COEFFICIENT_DOMAIN = {"source": "lists of naturals and texts", "target": "lists of naturals and texts"}
SORTS = (("entry", "fixture entry"), ("invariant", "invariant name"), ("operator", "operator name"),
         ("mutant", "mutant"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.positions", "the entry a mutant acts at", "its place in the fixture", "PRESERVED"),
    ("target.kill_matrix", "kills(m, v) as a set per mutant", "rows of names in sorted order", "PRESERVED"),
    ("target.fixture_length", "at most 18 elements in all", "lists of at most 64 naturals", "WEAKENED"),
)
NEAR = (("own_neg", "R097_SURVIVING_MUTANT"), ("near_survivor", "R097_SURVIVING_MUTANT"))
MUTATIONS = (("C1", "R097_BASE_FAILS", "base_broken", "near_base"),
             ("C2", "R097_NOT_CHANGED", "set_to_same", "near_same"),
             ("C3", "R097_SURVIVING_MUTANT", "mut", "mut"),
             ("C4", "R097_WRONG_INVARIANT", "intent_changed", "near_intent"),
             ("C5", "R097_KILL_MATRIX", "row_shortened", "near_matrix"))


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
    text = {int(e): str(t) for e, t in structure["texts"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    entries, invariants, mutants = _sort(structure, "entry"), _sort(structure, "invariant"), _sort(structure, "mutant")
    at = {a[0]: a[1] for n, a in rel if n == "at"}
    op = {a[0]: text[a[1]] for n, a in rel if n == "applies"}
    intent = {a[0]: text[a[1]] for n, a in rel if n == "intends"}

    def place(e: int) -> int:
        return entries.index(e) if e in entries else len(entries) + e

    return {"fixture": [value[x] for x in entries], "invariants": [text[v] for v in invariants],
            "kill_matrix": [sorted(text[a[1]] for n, a in rel if n == "kills" and a[0] == m) for m in mutants],
            "mutants": [[op[m], place(at[m]), value[m], intent[m]] for m in mutants]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return ([[f"entry:{k}", f"fixture:{k}"] for k in range(len(positive["fixture"]))]
            + [[f"invariant:{k}", f"invariants:{k}"] for k in range(len(positive["invariants"]))]
            + [[f"mutant:{k}", f"mutants:{k}"] for k in range(len(positive["mutants"]))])
