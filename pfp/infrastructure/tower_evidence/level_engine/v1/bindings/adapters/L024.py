"""Adapter for level 024: the engine's stages, order, elements,
restrictions, subfamily and labels written as the target checker's stages,
below pairs, element sets, restriction tables, subfamily and labels.
Stages and elements are named ``s<k>`` and ``e<k>`` by their positions.
Below pairs are written in the order of their element indices; one
restriction table is written for each hosted below pair ``(q, p)``, holding
the rows of the elements at ``p``; element sets, subfamily sets and label
sets follow declared order; every element's label is written, the empty
label as an empty list.  Written against the registered stage-24 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_024"
CLAUSES = (("C1", "R024_NOT_A_FAMILY"), ("C2", "R024_NOT_MONO"), ("C3", "R024_LABEL_MISMATCH"),
           ("C4", "R024_NOT_PULLBACK"))
COEFFICIENT_DOMAIN = {"source": "down-sets of a finite order", "target": "down-sets of a finite order"}
SORTS = (("stage", "stage"), ("element", "element"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.names", "stages and elements as elements", "their positions as names s<k>, e<k>", "PRESERVED"),
    ("target.missing_label", "an element with no label row carries the empty label",
     "written as an empty label; a missing label row is never presented", "PRESERVED"),
    ("target.pullback_reading", "the subfamily is the elements labelled true at their own stage",
     "the subfamily is the elements whose label is every stage at or below; the readings differ only on "
     "labels the label clauses refuse", "PRESERVED"),
)
NEAR = (("own_neg", "R024_NOT_PULLBACK"), ("near_open_sub", "R024_NOT_MONO"),
        ("near_label_back", "R024_LABEL_MISMATCH"), ("near_true_missing", "R024_NOT_PULLBACK"),
        ("near_restriction_lands", "R024_NOT_A_FAMILY"), ("near_compose", "R024_NOT_A_FAMILY"))
MUTATIONS = (("C1", "R024_NOT_A_FAMILY", "restriction_missing", "near_restriction_missing"),
             ("C2", "R024_NOT_MONO", "mut", "mut"),
             ("C3", "R024_LABEL_MISMATCH", "label_short", "near_label"),
             ("C4", "R024_NOT_PULLBACK", "labelled_true", "near_pullback"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    stages, elements = _sort(structure, "stage"), _sort(structure, "element")
    nm = {e: f"s{k}" for k, e in enumerate(stages)} | {e: f"e{k}" for k, e in enumerate(elements)}
    rel = sorted((n, list(a)) for n, a in structure["relations"])
    at = {a[0]: a[1] for n, a in rel if n == "at"}
    below = [a for n, a in rel if n == "below"]
    sub = {a[0] for n, a in rel if n == "in_sub"}
    label = [a for n, a in rel if n == "label"]
    return {
        "below": [[nm[q], nm[p]] for q, p in below],
        "elements": [[nm[p], [nm[x] for x in elements if at.get(x) == p]] for p in stages],
        "labels": [[nm[at[x]], nm[x], [nm[q] for q in stages if [x, q] in label]] for x in elements if x in at],
        "restrictions": [[nm[p], nm[q], [[nm[a[0]], nm[a[2]]] for n, a in rel
                                         if n == "restricts" and a[1] == q and at.get(a[0]) == p]]
                         for q, p in below],
        "stages": [nm[p] for p in stages],
        "subfamily": [[nm[p], [nm[x] for x in elements if x in sub and at.get(x) == p]] for p in stages],
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
    return [[f"stage:{k}", f"stage:{p}"] for k, p in enumerate(positive["stages"])]
