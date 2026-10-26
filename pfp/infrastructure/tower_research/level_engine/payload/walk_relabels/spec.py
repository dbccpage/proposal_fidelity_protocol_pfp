# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Replay of research-tree evidence: transports compose along a walk, and a
change of labels at every object moves each arrow's transport at both of its
ends; a change applied at one end only is refused.

The witness is ``research/sign_slice`` with ``research/convention_price``
(read only, through the vendored clone at its pin; admitted by the author's
ruling of 2026-09-25).  The presentation is the census member both trees
name ``square_2x2_occ3``, built by sign_slice's mover family: the four
three-site occupations of the square's four sites are the objects, one arrow
for each move of one occupant to the free neighbouring site, the six rank
orderings are the labels at every object, and each arrow's transport is the
permutation of orderings its move induces.  convention_price relabels that
member slot by slot: each arrow pair (an arrow and its reverse) has a slot at
each of its two ends, each slot takes one of four maps (the identity and
three rank exchanges), and an arrow is conjugated by the maps at its own two
ends.

The change is a pointwise-shaped assignment of the tree (one map per object,
every slot at an object taking that object's map): the one carrying the
maps of convention_price's recorded first moving assignment at their
objects.  That recorded assignment itself is the refused case: it places the
two maps at the two ends of one arrow pair only, so each object's map reaches
that pair's end and not the other pair at the same object.  The tree's section
predicate finds that it moves the member's class, while the pointwise
change keeps it.

Clauses, each decided on the packet by the trees' code where they hold it:

* ``walk_meets``: the walk is nonempty, uses declared arrows, and each arrow
  starts where the previous one ends;
* ``composite_exact``: the claimed composite is the walk's transports
  composed in walk order by sign_slice's composition;
* ``both_ends``: every claimed changed transport is convention_price's
  conjugation of the arrow's transport by the change at its source and at
  its target;
* ``covariance``: the claimed changed composite is that same conjugation of
  the recomputed composite by the change at the walk's first and last
  objects.

AuthorityEffect: None
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from types import ModuleType
from typing import Any, Literal

from omega_engine_operations.use_cases.level_engine.research_engine.level import LevelResult
from omega_engine_operations.use_cases.level_engine.research_engine.replay import Packet, Row, packets as replay_packets, result, tree_json, tree_module, tree_rel
from omega_engine_operations.use_cases.level_engine.research_engine.sealed import vendored

CHALLENGE_ID = "walk_relabels"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
PRICE = "convention_price"
SLICE = "sign_slice"
TREES = (PRICE, SLICE)
RECEIPT = "receipts/convention_price.json"
SOURCES = (f"research/{PRICE}/sixlabel.py", f"research/{PRICE}/parity.py", f"research/{PRICE}/{RECEIPT}",
           f"research/{SLICE}/genpres.py", f"research/{SLICE}/occ_relabel.py",
           f"research/{SLICE}/cone_section.py")
CLAUSES = ("walk_meets", "composite_exact", "both_ends", "covariance")
# Once around the square from object 2, first along the arrow pair the recorded
# assignment relabels (arrow indices of the tree's presentation).
WALK = (4, 7, 3, 0)

Perm = tuple[int, ...]


@contextmanager
def _slice_on_path() -> Iterator[None]:
    """convention_price's modules import sign_slice's by name; its own run
    script puts sign_slice's folder on the path, and so does this while one
    of them loads."""
    folder = str(vendored(tree_rel(SLICE, "")))
    from ...vendor_loading import vendor_import_scope
    from pathlib import Path
    with vendor_import_scope(Path(folder)):
        yield


def price(module: str) -> ModuleType:
    with _slice_on_path():
        return tree_module(PRICE, module)


def six() -> ModuleType:
    return price("sixlabel")


def conjugated(t: Perm, g_src: Perm, g_dst: Perm) -> Perm:
    """convention_price's conjugation of one transport by its two end maps."""
    out: Perm = price("parity").conjugated(t, g_src, g_dst)
    return out


def compose_along(transports: list[Perm], k: int) -> Perm:
    """Transports composed in walk order, by sign_slice's composition."""
    acc: Perm = tuple(range(k))
    for t in transports:
        acc = six().compose(t, acc)
    return acc


@lru_cache(maxsize=1)
def witness() -> tuple[int, ...]:
    """convention_price's recorded first moving assignment of the member."""
    doc = tree_json(PRICE, RECEIPT)
    assert isinstance(doc, dict)
    return tuple(int(x) for x in doc["phase_3_sixlabel"]["exhaustion"]["first_witness"])


def member() -> Any:
    return six().member()


def arrow_pairs() -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = six().undirected_hops(member())
    return out


def change_of(assignment: tuple[int, ...]) -> dict[int, int]:
    """The map index at each object, read from an assignment's slots that
    are not the identity (source slot, then target slot, per arrow pair)."""
    p, out = member(), {o: 0 for o in member().objects}
    for h, (i, _) in enumerate(arrow_pairs()):
        for slot, obj in ((2 * h, p.arrows[i].src), (2 * h + 1, p.arrows[i].dst)):
            if assignment[slot]:
                assert out[obj] in (0, assignment[slot]), "one object, two maps"
                out[obj] = assignment[slot]
    return out


def pointwise(change: dict[int, int]) -> tuple[int, ...]:
    """The assignment that gives every slot its object's map."""
    p = member()
    return tuple(x for i, _ in arrow_pairs() for x in (change[p.arrows[i].src], change[p.arrows[i].dst]))


def relabelled(assignment: tuple[int, ...]) -> Any:
    return six().relabelled_multi(member(), arrow_pairs(), assignment, six().slot_maps())


def _arrows(p: Any) -> list[list[Any]]:
    return [[f"a{i}", str(a.src), str(a.dst), list(a.transport)] for i, a in enumerate(p.arrows)]


def _changed(p: Any) -> list[list[Any]]:
    return [[f"a{i}", list(a.transport)] for i, a in enumerate(p.arrows)]


def positive() -> Packet:
    p, maps = member(), six().slot_maps()
    change = change_of(witness())
    composite = compose_along([p.arrows[i].transport for i in WALK], p.fibre)
    at = p.arrows[WALK[0]].src
    ends = p.arrows[WALK[-1]].dst
    return {"arrows": _arrows(p), "change": [[str(o), list(maps[change[o]])] for o in p.objects],
            "changed": _changed(relabelled(pointwise(change))),
            "changed_composite": list(conjugated(composite, maps[change[at]], maps[change[ends]])),
            "composite": list(composite), "labels": p.fibre, "objects": [str(o) for o in p.objects],
            "walk": [f"a{i}" for i in WALK]}


def one_end() -> list[list[Any]]:
    """The changed transports under the recorded assignment itself."""
    return _changed(relabelled(witness()))


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def _perm(value: object, k: int) -> Perm | None:
    if not isinstance(value, list) or sorted(value) != list(range(k)):
        return None
    return tuple(int(x) for x in value)


def decide(pk: Packet) -> tuple[str, ...]:
    failed: list[str] = []
    k = pk["labels"]
    assert isinstance(k, int)
    arrows = {str(n): (str(s), str(d), _perm(t, k)) for n, s, d, t in pk["arrows"]}  # type: ignore[attr-defined]
    change = {str(o): _perm(g, k) for o, g in pk["change"]}  # type: ignore[attr-defined]
    changed = {str(n): t for n, t in pk["changed"]}  # type: ignore[attr-defined]
    walk = [str(a) for a in pk["walk"]]  # type: ignore[attr-defined]
    known = [a for a in walk if a in arrows]
    if not walk or len(known) != len(walk) or any(arrows[a][1] != arrows[b][0] for a, b in zip(walk, walk[1:])):
        failed.append("walk_meets")
    along = compose_along([arrows[a][2] or () for a in known], k)
    if list(along) != pk["composite"]:
        failed.append("composite_exact")
    for name, (s, d, t) in arrows.items():
        g_s, g_d = change.get(s), change.get(d)
        if t is None or g_s is None or g_d is None or changed.get(name) != list(conjugated(t, g_s, g_d)):
            failed.append("both_ends")
            break
    first = change.get(arrows[known[0]][0]) if known else None
    last = change.get(arrows[known[-1]][1]) if known else None
    if first is None or last is None or pk["changed_composite"] != list(conjugated(along, first, last)):
        failed.append("covariance")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    p, maps = member(), six().slot_maps()
    base = six().cone_section(p)
    change = change_of(witness())
    moved = relabelled(pointwise(change))
    walk_cells = tree_module(SLICE, "cone_section").closed_walks(p, p.arrows[WALK[0]].src, len(WALK))
    extra = {
        "labels": p.fibre, "objects": len(p.objects), "arrows": len(p.arrows), "slot_maps": len(maps),
        "change_is_pointwise_shaped": pointwise(change) in set(six().pointwise_shaped(p, arrow_pairs())),
        "change_keeps_the_class": six().cone_section(moved) == base,
        "recorded_assignment_moves_the_class": six().cone_section(relabelled(witness())) != base,
        "walk_is_a_closed_walk_of_the_tree": positive()["composite"] in [list(t) for t, _ in walk_cells],
        "changed_walk_recomposes": list(compose_along([moved.arrows[i].transport for i in WALK], p.fibre))
        == positive()["changed_composite"],
    }
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, (), SOURCES, extra, trees=TREES)
