"""Adapter for level 026: the engine's colours, slot positions, operations,
units and substitution table written as the target checker's colours,
bound, operations, units and substitutions.  Colours and operations are
named ``c<k>`` and ``p<k>`` by their positions; the bound is the number of
hosted slot positions and a slot is written as its position; an
operation's input colours are written in slot order; unit and
substitution rows are written once per hosted tuple, in the order of their
element indices.  Written against the registered stage-26 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_026"
CLAUSES = (("C1", "R026_KIND_MISMATCH"), ("C2", "R026_TABLE_GAP"), ("C3", "R026_UNIT_LAW"),
           ("C4", "R026_BRACKETING"))
COEFFICIENT_DOMAIN = {"source": "finite substitution tables", "target": "finite substitution tables"}
SORTS = (("colour", "colour"), ("slot", "slot"), ("op", "operation"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.names", "colours and operations as elements", "their positions as names c<k>, p<k>", "PRESERVED"),
    ("target.bound", "the bound is the number of hosted slot positions", "a declared natural number", "PRESERVED"),
)
NEAR = (("own_neg", "R026_KIND_MISMATCH"), ("near_colour", "R026_KIND_MISMATCH"),
        ("near_outside", "R026_KIND_MISMATCH"), ("near_output", "R026_KIND_MISMATCH"),
        ("near_unit_outside", "R026_UNIT_LAW"))
MUTATIONS = (("C1", "R026_KIND_MISMATCH", "colour_mismatch", "own_neg"),
             ("C2", "R026_TABLE_GAP", "row_missing", "near_gap"),
             ("C3", "R026_UNIT_LAW", "unit_moves", "near_unit"),
             ("C4", "R026_BRACKETING", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    colours, slots, ops = _sort(structure, "colour"), _sort(structure, "slot"), _sort(structure, "op")
    nm = {e: f"c{k}" for k, e in enumerate(colours)} | {e: f"p{k}" for k, e in enumerate(ops)}
    rel = sorted((n, list(a)) for n, a in structure["relations"])
    output = {a[0]: a[1] for n, a in rel if n == "output"}
    inputs = {o: [nm[a[2]] for i in slots for n, a in rel if n == "input" and a[0] == o and a[1] == i] for o in ops}
    return {
        "bound": len(slots),
        "colours": [nm[c] for c in colours],
        "operations": [[nm[o], inputs[o], nm[output[o]]] for o in ops if o in output],
        "substitutions": [[nm[a[0]], slots.index(a[1]), nm[a[2]], nm[a[3]]] for n, a in rel if n == "subst"],
        "units": [[nm[a[0]], nm[a[1]]] for n, a in rel if n == "unit"],
    }


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"op:{k}", f"operation:{o[0]}"] for k, o in enumerate(positive["operations"])]
