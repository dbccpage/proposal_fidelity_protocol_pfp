# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Adapter for level 061's research-tree replay: the replayed presentation
(sign_slice's mover family on the square at occupancy three, as
convention_price relabels it) is the target checker's labels, objects,
arrows, walk, composite, change, changed transports and changed composite
as they stand.  The tree's rank orderings are the labels, its occupations the
objects, its arrows the arrows (named by their index), and its pointwise
relabel the target's frame change (a gauge transformation at every object).
Written against the registered stage-61 checker.

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_061"
CLAUSES = (("C1", "R061_NOT_A_WALK"), ("C2", "R061_COMPOSITE"), ("C3", "R061_ONE_END"), ("C4", "R061_COVARIANCE"))
COEFFICIENT_DOMAIN = {"source": "permutations of the six rank orderings", "target": "permutations of a finite label set"}
SORTS = (("rank ordering", "label"), ("occupation", "object"), ("arrow", "arrow"), ("object map", "change"))
UNMAPPED_SORTS = ("presentation token", "amp", "hop", "slot")
STRUCTURE_MAP_REASON = "the obligation names no structure map"
LOSS_ROWS = (
    ("target.labels", "the member's six rank orderings, in sign_slice's ordering order",
     "labels 0..5", "PRESERVED"),
    ("target.arrow_names", "arrows by index in the tree's presentation", "names a0..a7", "PRESERVED"),
    ("target.change", "the maps of convention_price's recorded first moving assignment at their objects "
     "(map 1 at object 2, map 3 at object 3), completed pointwise: a pointwise-shaped assignment of the tree",
     "one permutation per object, computed by the replay", "PRESERVED"),
    ("target.changed", "convention_price's relabel of the member under that pointwise-shaped assignment",
     "the changed transport of every arrow", "PRESERVED"),
    ("target.walk", "once around the square from object 2 along the relabelled hop; its composite is among "
     "sign_slice's closed-walk transports at that object", "the walk a4, a7, a3, a0, chosen by the replay",
     "PRESERVED"),
    ("target.composite", "the walk's transports composed by sign_slice's composition",
     "the composite, computed by the replay", "PRESERVED"),
    ("target.changed_composite", "convention_price's conjugation law applied to the composite at the walk's ends",
     "the changed composite, computed by the replay", "PRESERVED"),
    ("source.hop_pairing", "each hop's two arrows share their slot maps; a reverse arrow carries the inverse",
     "each arrow listed on its own", "DROPPED"),
    ("source.amps", "the member's unit weighting, one amp per arrow", "not carried", "DROPPED"),
    ("source.class_verdict", "sign_slice's section predicate: the recorded assignment moves the member's class "
     "and the pointwise change keeps it", "not decided by the checker; reported beside the record", "DROPPED"),
    ("source.lean", "convention_price's two-label parity laws and natural_sections' re-presentation theorems",
     "not cited; the replay rests on the trees' Python", "DROPPED"),
)
NEAR = (("own_neg", "R061_ONE_END"), ("near_walk", "R061_NOT_A_WALK"), ("near_composite", "R061_COMPOSITE"),
        ("near_one_end", "R061_ONE_END"))
MUTATIONS = (("C1", "R061_NOT_A_WALK", "walk_broken", "near_walk"),
             ("C2", "R061_COMPOSITE", "composite_off", "near_composite"),
             ("C3", "R061_ONE_END", "changed_off", "near_one_end"),
             ("C4", "R061_COVARIANCE", "mut", "mut"))


def packet_of(obj: object) -> dict[str, Any]:
    assert isinstance(obj, dict)
    packet = obj["packet"]
    assert isinstance(packet, dict)
    return copy.deepcopy(dict(packet))


def fixtures(result: object, inputs: Sequence[tuple[str, str, object]]) -> list[dict[str, Any]]:
    by = {fid: obj for fid, _, obj in inputs}
    out: list[dict[str, Any]] = [{"id": "pos", "kind": "positive", "payload": packet_of(by["pos"])}]
    out += [{"expected_code": code, "id": fid, "kind": "near_miss", "payload": packet_of(by[fid])}
            for fid, code in NEAR]
    out += [{"clause": clause, "expected_code": code, "id": mid, "kind": "decisive_mutation",
             "payload": packet_of(by[fid]), "repair": "pos"} for clause, code, mid, fid in MUTATIONS]
    return out


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"arrow:{a[0]}", f"arrow:{a[0]}"] for a in positive["arrows"]]
