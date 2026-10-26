"""Adapter for level 034: the engine's outcomes, terms, point and declared
table written as the target checker's family, point and fisher matrix.
Outcomes, parameters and terms keep their declared order.  Each outcome's
polynomial lists every hosted term with its hosted coefficient, zeros
included (the engine hosts one coefficient for every outcome and term); a
term's exponents are its hosted powers, one per parameter, written as
naturals.  Written against the registered stage-34 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_034"
CLAUSES = (("C1", "R034_NOT_NORMALISED"), ("C2", "R034_NEGATIVE_DIRECTION"), ("C3", "R034_MATRIX_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "exact rationals", "target": "exact rationals"}
SORTS = (("outcome", "outcome polynomial"), ("parameter", "parameter index"), ("term", "monomial"))
UNMAPPED_SORTS = ("presentation token", "witness form", "number")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.monomials", "one hosted coefficient on every declared term, zeros included",
     "every term listed for every outcome, a zero coefficient written 0/1", "PRESERVED"),
    ("target.size", "outcomes, parameters, terms and numbers within the 18-element cap",
     "any finite family, k from 1 to 6", "WEAKENED"),
    ("clause.C1", "two value clauses: the weights sum to one, and each is positive at the point",
     "one code for both", "PRESERVED"),
)
NEAR = (("own_neg", "R034_NEGATIVE_DIRECTION"),)
MUTATIONS = (("C1", "R034_NOT_NORMALISED", "constant_raised", "near_not_one"),
             ("C2", "R034_NEGATIVE_DIRECTION", "mut", "mut"),
             ("C3", "R034_MATRIX_MISMATCH", "table_entry_moved", "near_table"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    outcomes, params, terms = _sort(structure, "outcome"), _sort(structure, "parameter"), _sort(structure, "term")
    value = {int(e): str(v) for e, v in structure["values"]}
    rel = [(n, list(a)) for n, a in structure["relations"]]
    power = {(a[0], a[1]): int(Fraction(value[a[2]])) for n, a in rel if n == "power"}
    weight = {(a[0], a[1]): value[a[2]] for n, a in rel if n == "weight"}
    at = {a[0]: value[a[1]] for n, a in rel if n == "at"}
    declared = {(a[0], a[1]): value[a[2]] for n, a in rel if n == "declared"}
    return {"family": [[[weight[(o, t)], [power[(t, p)] for p in params]] for t in terms] for o in outcomes],
            "fisher": [[declared[(p, q)] for q in params] for p in params],
            "point": [at[p] for p in params]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    out = [[f"outcome:{k}", f"family:{k}"] for k in range(len(positive["family"]))]
    out += [[f"parameter:{k}", f"point:{k}"] for k in range(len(positive["point"]))]
    out += [[f"term:{k}", "exponents:" + ",".join(str(e) for e in t[1])] for k, t in enumerate(positive["family"][0])]
    return out
