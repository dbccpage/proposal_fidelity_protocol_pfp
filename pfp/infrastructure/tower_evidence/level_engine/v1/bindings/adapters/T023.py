"""Adapter for level 023's research-tree replay: the replayed loci, observers'
loci, records and glue are the target checker's points, patches, sections and
glued rows as they stand.  Written against the registered stage-23 checker.

AuthorityEffect: None
"""

from __future__ import annotations

import copy
import importlib
from collections.abc import Sequence
from typing import Any

CHECKER_ID = "stage_023"
CLAUSES = (("C1", "R023_NOT_COVERING"), ("C2", "R023_SECTION_DOMAIN"), ("C3", "R023_OVERLAP_CONFLICT"),
           ("C4", "R023_GLUE_MISMATCH"))
COEFFICIENT_DOMAIN = {"source": "the tree's natural-number values", "target": "finite value names"}
SORTS = (("locus", "point"), ("observer", "patch"), ("value", "value"))
UNMAPPED_SORTS = ("presentation token", "observer name")
STRUCTURE_MAP_REASON = ""
LOSS_ROWS = (
    ("target.transport_reading", "the function reading", "the function reading", "PRESERVED"),
    ("source.lean_cover", "the tree's Lean glues on one fixed cover of three loci",
     "not cited; the replay rests on the tree's Python", "DROPPED"),
)
NEAR = (("own_neg", "R023_OVERLAP_CONFLICT"), ("near_uncovered", "R023_NOT_COVERING"),
        ("near_domain", "R023_SECTION_DOMAIN"))
MUTATIONS = (("C1", "R023_NOT_COVERING", "locus_uncovered", "near_uncovered"),
             ("C2", "R023_SECTION_DOMAIN", "record_short", "short_record"),
             ("C3", "R023_OVERLAP_CONFLICT", "overlap_conflict", "own_neg"),
             ("C4", "R023_GLUE_MISMATCH", "mut", "mut"))


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


def squares(source: object, positive: object) -> list[tuple[str, object, object]]:
    """Restriction: the replayed glue read back through each observer by the
    tree's own projection (left), against the positive's glue restricted to
    its patches (right)."""
    spec = importlib.import_module("payload.observer_glue.spec")
    carried = spec.restricted(packet_of(source))
    assert isinstance(positive, dict)
    g = dict((x, v) for x, v in positive["glued"])
    read = [sorted([x, g[x]] for x in patch) for patch in positive["patches"]]
    return [("restriction", carried, read)]


def pairs(positive: object) -> list[list[str]]:
    assert isinstance(positive, dict)
    return [[f"locus:{p}", f"point:{p}"] for p in positive["points"]]
