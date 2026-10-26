# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 053: the engine's factors, slots, joined places,
reading and exchange table written as the target checker's factors,
reading, swap, joined row and dimension.

Slot order travels as hosted data, and this adapter only sorts by it:

* the factor order is the hosted relation ``before`` (the one pair it
  holds, first factor then second);
* each factor's row lists its slots in the order of their hosted indices
  (naturals carried by the slot elements), and each factor's name is its
  hosted text;
* the joined row lists the places in the order of their hosted indices;
* the reading is the hosted text of the factor in the hosted relation
  ``slowest``;
* the swap is the hosted relation ``exchange``: entry k is the rank, in the
  order of hosted indices, of the place that the place of rank k is sent
  to; when no exchange tuple is hosted, the swap is written ``null``;
* the dimension is the hosted natural in ``claimed``.

No order is taken from element positions, and no field is computed: the
engine decides the product in the declared reading through the hosted
table itself.  Written against the registered stage-53 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

CHECKER_ID = "stage_053"
CLAUSES = (("C1", "R053_DIMENSION"), ("C2", "R053_UNTRANSPORTED"), ("C3", "R053_SWAP"), ("C4", "R053_PRODUCT"))
COEFFICIENT_DOMAIN = {"source": "exact pairs of rationals", "target": "exact pairs of rationals"}
SORTS = (("factor", "factor name"), ("slot", "factor slot"), ("place", "joined slot"))
UNMAPPED_SORTS = ("presentation token", "witness form", "number")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.slot_order", "slot and place indices hosted as naturals, factor order as the relation before",
     "list positions", "PRESERVED"),
    ("target.swap", "the exchange table as a hosted relation over places; no tuple when none is given",
     "a list of slots, or null", "PRESERVED"),
    ("target.frame_sizes", "two factors of two slots, within the 18-element cap", "any sizes of at least one",
     "WEAKENED"),
)
NEAR = (("own_neg", "R053_UNTRANSPORTED"), ("near_untransported", "R053_UNTRANSPORTED"),
        ("near_unmoved", "R053_PRODUCT"))
MUTATIONS = (("C1", "R053_DIMENSION", "size_misclaimed", "near_size"),
             ("C2", "R053_UNTRANSPORTED", "table_withheld", "own_neg"),
             ("C3", "R053_SWAP", "table_for_declared_order", "near_reading_first"),
             ("C4", "R053_PRODUCT", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def claim_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    value = {int(e): str(v) for e, v in structure["values"]}
    text = {int(e): str(t) for e, t in structure.get("texts", [])}
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def index(e: int) -> Fraction:
        return Fraction(value[e])

    [(first, second)] = [(a[0], a[1]) for n, a in rel if n == "before"]
    entry = {a[0]: [value[a[1]], value[a[2]]] for n, a in rel if n == "entry"}

    def row(f: int) -> list[list[str]]:
        mine = [a[0] for n, a in rel if n == "slot_of" and a[1] == f]
        return [entry[s] for s in sorted(mine, key=index)]

    places = sorted(_sort(structure, "place"), key=index)
    joined = {a[0]: [value[a[1]], value[a[2]]] for n, a in rel if n == "joined"}
    exchange = {a[0]: a[1] for n, a in rel if n == "exchange"}
    [slowest] = [a[0] for n, a in rel if n == "slowest"]
    [claimed] = [a[0] for n, a in rel if n == "claimed"]
    return {"dimension": int(index(claimed)),
            "factors": [[text[first], row(first)], [text[second], row(second)]],
            "joined": [joined[p] for p in places],
            "reading": text[slowest],
            "swap": [places.index(exchange[p]) for p in places] if exchange else None}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": claim_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": claim_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": claim_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    out = [[f"factor:{k}", f"factor:{f[0]}"] for k, f in enumerate(positive["factors"])]
    k = 0
    for f in positive["factors"]:
        for i in range(len(f[1])):
            out.append([f"slot:{k}", f"slot:{f[0]}.{i}"])
            k += 1
    out += [[f"place:{i}", f"joined:{i}"] for i in range(len(positive["joined"]))]
    return out
