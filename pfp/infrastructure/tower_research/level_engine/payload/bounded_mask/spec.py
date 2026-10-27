# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Replay of sealed evidence: an obstruction claim as a bounded formula over
the sealed response menu, evaluated by full enumeration.

The sealed truncated-search world (``derivation.represented``, read from the
pinned clone) has a violated requirement and a finite response menu; the
sealed ``repairs`` says which menu entries repair it.  "The requirement is
obstructed" is the formula: for every menu position below the menu's length,
the position is none of the repairing ones.  Its value is recomputed by
enumerating the whole menu; its quantifier mask is recomputed from the tree.
A search cut at the first entry reports an obstruction that the full search
refutes (sealed ``incomplete_search_false_alarm``), so the bound must be the
menu's length, never a budget.

Clauses, each decided on the replayed sealed facts:

* ``menu_replayed``: the formula ranges over the whole sealed menu and names
  exactly the sealed repairing positions;
* ``bounded``: no quantifier ranges over an unbounded domain;
* ``mask_replayed``: the declared mask is the tree's quantifiers in order;
* ``within_budget``: the declared budget covers full enumeration;
* ``value_replayed``: the declared value is the sealed exhaustive verdict.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from operations.use_cases.level_engine.research_engine.level import LevelResult
from operations.use_cases.level_engine.research_engine.replay import Packet, Row, packets as replay_packets, result
from derivation.represented import TRUNC_WORLD, obstructed, obstructed_trunc, repairs, response_menu

CHALLENGE_ID = "bounded_mask"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
LEAN = ("Represented.incomplete_search_false_alarm",)
SOURCES = ("code/derivation/represented.py",)
CLAUSES = ("menu_replayed", "bounded", "mask_replayed", "within_budget", "value_replayed")
REQ = (1, 2)
VAR = "k"


def repairing() -> list[int]:
    menu = response_menu(TRUNC_WORLD)
    return [k for k, m in enumerate(menu) if repairs(TRUNC_WORLD, m, REQ)]


def body(fixes: list[int]) -> list[object]:
    atoms: list[list[object]] = [["neq", VAR, r] for r in fixes]
    out: list[object] = atoms[0]
    for a in atoms[1:]:
        out = ["and", out, a]
    return out


def formula(bound: object) -> list[object]:
    return ["forall", VAR, bound, body(repairing())]


def steps(tree: object) -> int:
    assert isinstance(tree, list)
    if tree[0] in ("forall", "exists"):
        return int(tree[2]) * steps(tree[3])
    if tree[0] in ("and", "or"):
        return steps(tree[1]) + steps(tree[2])
    return 1


def mask(tree: object) -> list[str]:
    assert isinstance(tree, list)
    if tree[0] in ("forall", "exists"):
        return [str(tree[0])] + mask(tree[3])
    if tree[0] in ("and", "or"):
        return mask(tree[1]) + mask(tree[2])
    return []


def positive() -> Packet:
    tree = formula(len(response_menu(TRUNC_WORLD)))
    return {"budget": steps(tree), "formula": tree, "mask": mask(tree),
            "value": "true" if obstructed(TRUNC_WORLD, REQ) else "false"}


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def _unbounded(tree: object) -> bool:
    if not isinstance(tree, list):
        return False
    if tree[0] in ("forall", "exists"):
        return tree[2] == "nat" or _unbounded(tree[3])
    return any(_unbounded(t) for t in tree[1:])


def decide(pk: Packet) -> tuple[str, ...]:
    failed: list[str] = []
    tree = pk["formula"]
    if tree != formula(len(response_menu(TRUNC_WORLD))):
        failed.append("menu_replayed")
    if _unbounded(tree):
        failed.append("bounded")
    else:
        if pk["mask"] != mask(tree):
            failed.append("mask_replayed")
        if not isinstance(pk["budget"], int) or pk["budget"] < steps(tree):
            failed.append("within_budget")
    if pk["value"] != ("true" if obstructed(TRUNC_WORLD, REQ) else "false"):
        failed.append("value_replayed")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    extra = {"menu_length": len(response_menu(TRUNC_WORLD)), "repairing_positions": repairing(),
             "truncated_at_one_reports_obstruction": obstructed_trunc(1, TRUNC_WORLD, REQ),
             "exhaustive_reports_obstruction": obstructed(TRUNC_WORLD, REQ)}
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, LEAN, SOURCES, extra)
