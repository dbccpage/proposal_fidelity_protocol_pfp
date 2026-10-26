# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 061: the engine's corners, links, walk, composite and
change of labels written as the target checker's objects, arrows, walk,
composite, change, changed transports and changed composite.  Corners,
links and labels are named by their positions in the declared order; the
walk lists its strides' links in declared stride order.  Written against the
registered stage-61 checker.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_061"
CLAUSES = (("C1", "R061_NOT_A_WALK"), ("C2", "R061_COMPOSITE"), ("C3", "R061_ONE_END"), ("C4", "R061_COVARIANCE"))
COEFFICIENT_DOMAIN = {"source": "permutations of a finite label set", "target": "permutations of a finite label set"}
SORTS = (("label", "label"), ("corner", "object"), ("link", "arrow"), ("stride", "walk step"))
UNMAPPED_SORTS = ("presentation token", "witness form")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (("target.names", "corners and links as elements", "their positions as names", "PRESERVED"),)
NEAR = (("own_neg", "R061_ONE_END"),)
MUTATIONS = (("C1", "R061_NOT_A_WALK", "walk_broken", "near_walk"), ("C2", "R061_COMPOSITE", "composite_off", "near_composite"),
             ("C3", "R061_ONE_END", "change_at_one_end", "near_one_end"), ("C4", "R061_COVARIANCE", "mut", "mut"))


def _sort(structure: dict[str, Any], name: str) -> list[int]:
    off = 0
    for sort, count in structure["sorts"]:
        if sort == name:
            return list(range(off, off + count))
        off += count
    raise KeyError(name)


def transport_of(structure: object) -> dict[str, Any]:
    assert isinstance(structure, dict)
    labels, corners = _sort(structure, "label"), _sort(structure, "corner")
    links, strides = _sort(structure, "link"), _sort(structure, "stride")
    rel = [(n, list(a)) for n, a in structure["relations"]]

    def images(name: str, owner: int | None) -> list[int]:
        got = {labels.index(a[-2]): labels.index(a[-1]) for n, a in rel
               if n == name and (owner is None or a[0] == owner)}
        return [got[k] for k in range(len(labels))]

    def end(name: str, e: int) -> str:
        return next(str(corners.index(a[1])) for n, a in rel if n == name and a[0] == e)

    return {"arrows": [[f"e{k}", end("from", e), end("to", e), images("moves", e)] for k, e in enumerate(links)],
            "change": [[str(k), images("regauge", v)] for k, v in enumerate(corners)],
            "changed": [[f"e{k}", images("moved", e)] for k, e in enumerate(links)],
            "changed_composite": images("recomposite", None), "composite": images("composite", None),
            "labels": len(labels), "objects": [str(k) for k in range(len(corners))],
            "walk": [f"e{links.index(a[1])}" for w in strides for n, a in rel if n == "walks" and a[0] == w]}


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": transport_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": transport_of(by[fid])} for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": transport_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"link:{k}", f"arrow:{a[0]}"] for k, a in enumerate(positive["arrows"])]
