"""Adapter for level 068: the engine's quantities, bounds, steps and grid
written as the target checker's values, steps and grid.  Quantities are
named by their positions in the declared order; a quantity that is no
step's result is a value, and the steps follow the declared order of their
results.  Written against the registered stage-68 checker.

C1 (a value or result that is not a two-end bound, such as a decimal) is
not claimed: exact intake refuses a decimal, and a quantity with no bound is
refused by the grammar (bounds_given) before it reaches the checker's
schema, which has no way to write it.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_068"
CLAUSES = (("C2", "R068_EMPTY"), ("C3", "R068_DIVISOR_ZERO"), ("C4", "R068_NOT_ENCLOSED"), ("C5", "R068_OFF_GRID"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("quantity", "value or step"), ("val", "rational"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.no_bound", "a quantity with no bound refused by the grammar", "a bare decimal refused by code",
              "WEAKENED"),)
OPS = ("add", "sub", "mul", "div")
NEAR = (("near_divisor", "R068_DIVISOR_ZERO"),)
MUTATIONS = (("C2", "R068_EMPTY", "bound_empty", "near_empty"), ("C3", "R068_DIVISOR_ZERO", "divisor_holds_zero", "near_divisor"),
             ("C4", "R068_NOT_ENCLOSED", "mut", "mut"), ("C5", "R068_OFF_GRID", "grid_coarsened", "near_offgrid"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def bounds_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    qs = _sort(structure, "quantity")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    bound = {a[0]: [value[a[1]], value[a[2]]] for n, a in rel if n == "bound"}
    step = {a[0]: (n, a[1], a[2]) for n, a in rel if n in OPS}
    grid = next(int(Fraction(value[a[0]])) for n, a in rel if n == "grid")
    return {"grid": grid,
            "steps": [[f"q{qs.index(q)}", step[q][0], f"q{qs.index(step[q][1])}", f"q{qs.index(step[q][2])}", bound[q]]
                      for q in qs if q in step],
            "values": [[f"q{qs.index(q)}", bound[q]] for q in qs if q not in step]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": bounds_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": bounds_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": bounds_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"quantity:{v[0]}", f"value:{v[0]}"] for v in positive["values"]] + \
        [[f"quantity:{s[0]}", f"step:{s[0]}"] for s in positive["steps"]]
