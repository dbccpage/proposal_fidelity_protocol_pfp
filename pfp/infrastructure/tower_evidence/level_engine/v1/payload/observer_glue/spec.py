"""Replay of research-tree evidence: local records on a cover of loci glue to
one global assignment, and the glue is the tree's own.

The witness is ``research/g014_observer_descent`` (read only, through the
vendored clone at its pin; admitted by the author's ruling of 2026-09-25):
its observers, each reading a sub-sector of loci, its projection of a
carrier state onto an observer's loci, its pairwise compatibility check on
shared loci, and its gluing of compatible records.  The cover and the state
are the tree's own compatible-cover fixture (three observers over four
loci); the refused case is the tree's own perturbation, one more at the
first locus two observers share.

Clauses, each decided by the tree's code on the packet:

* ``covered``: the observers cover every declared locus;
* ``on_patch``: each record is defined on exactly its observer's loci;
* ``overlaps_agree``: the tree's compatibility check passes;
* ``glue_replayed``: the declared glue is the tree's glue of the records.

AuthorityEffect: None
"""

from __future__ import annotations

from types import ModuleType
from typing import Any, Literal

from engine.level import LevelResult
from engine.replay import Packet, Row, packets as replay_packets, result, tree_module

CHALLENGE_ID = "observer_glue"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
TREE = "g014_observer_descent"
SOURCES = (f"research/{TREE}/observer_descent.py",)
CLAUSES = ("covered", "on_patch", "overlaps_agree", "glue_replayed")
# The tree's compatible-cover fixture (its test of gluing on a total cover).
STATE = {"l1": 100, "l2": 200, "l3": 300, "l4": 400}
COVER = (("O1", ("l1", "l2")), ("O2", ("l2", "l3")), ("O3", ("l3", "l4")))


def tree() -> ModuleType:
    return tree_module(TREE, "observer_descent")


def _cover(patches: list[list[str]]) -> Any:
    t = tree()
    return t.DescentCoverage(tuple(t.Observer(f"O{k + 1}", tuple(p)) for k, p in enumerate(patches)))


def _rows(state: Any) -> list[list[str]]:
    return [[k, str(v)] for k, v in state.data]


def positive() -> Packet:
    t = tree()
    state = t.CarrierState.from_mapping(STATE)
    cov = _cover([list(loci) for _, loci in COVER])
    records = {o.observer_id: o.project(state) for o in cov.observers}
    glued = cov.glue(records).unwrap()
    return {"glued": _rows(glued), "patches": [sorted(loci) for _, loci in COVER], "points": sorted(STATE),
            "sections": [_rows(records[i]) for i, _ in COVER]}


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def _state(rows: object) -> Any:
    assert isinstance(rows, list)
    return tree().CarrierState.from_mapping({str(k): int(v) for k, v in rows})


def decide(pk: Packet) -> tuple[str, ...]:
    failed: list[str] = []
    patches = pk["patches"]
    sections = pk["sections"]
    assert isinstance(patches, list) and isinstance(sections, list)
    cov = _cover(patches)
    points = pk["points"]
    assert isinstance(points, list)
    if not cov.is_total_cover_for(tree().CarrierState.from_mapping({str(p): 0 for p in points})):
        failed.append("covered")
    records = {o.observer_id: _state(s) for o, s in zip(cov.observers, sections)}
    if any(set(records[o.observer_id].loci) != set(o.loci) for o in cov.observers):
        failed.append("on_patch")
    if cov.check_compatibility(records).is_err():
        failed.append("overlaps_agree")
    glue = cov.glue(records)
    if glue.is_err() or _rows(glue.unwrap()) != pk["glued"]:
        failed.append("glue_replayed")
    return tuple(failed)


def restricted(pk: Packet) -> list[list[list[str]]]:
    """The declared glue read back through each observer by the tree's own
    projection."""
    cov = _cover(pk["patches"])  # type: ignore[arg-type]
    glued = _state(pk["glued"])
    return [_rows(o.project(glued)) for o in cov.observers]


def evaluate(have: frozenset[str]) -> LevelResult:
    pos = positive()
    extra = {"observers": len(COVER), "loci": len(STATE), "restricted_glue": restricted(pos)}
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, (), SOURCES, extra, trees=(TREE,))
