"""Replay of sealed evidence: every executed step stays within the capability
its scope grants, and each step's effects are computed from the sealed step
itself.

The sealed represented world (``derivation.represented``, read from the
pinned clone; its truncated-search world) grants two capabilities: the
licence to augment its views, and a budget to spend.  An event's effect row
is computed, never declared: a capability is in the row exactly when the
event changes the world, and withdrawing that capability alone makes the
sealed step inert.  Adding a view needs both (sealed
``progress_needs_license``, ``progress_needs_budget``), a mark needs only the
budget, and a note needs neither.

Two scopes: the world as it is, which grants both capabilities, and inside
it the same world with the licence withdrawn, which grants only the budget.
Each edge runs its events in its scope's world.

Clauses, each decided on the replayed sealed facts:

* ``rows_replayed``: every operation's effect row is the computed one;
* ``scopes_replayed``: the scopes are the two sealed configurations, nested,
  with the capabilities each grants;
* ``operations_known``: every edge performs only declared operations;
* ``edges_progress``: every event of every edge changes its scope's world
  under the sealed step.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Literal

from engine.level import LevelResult
from engine.replay import Packet, Row, packets as replay_packets, result
from derivation.represented import TRUNC_WORLD, World, step

CHALLENGE_ID = "granted_steps"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
LEAN = ("Represented.progress_needs_license", "Represented.progress_needs_budget",
        "GraphGenesis.proposal_confers_no_execution")
SOURCES = ("code/derivation/represented.py",)
CLAUSES = ("rows_replayed", "scopes_replayed", "operations_known", "edges_progress")
OPERATIONS: dict[str, tuple[object, ...]] = {
    "add_view": ("addView", (1,)),
    "mark": ("mark", (0,), 1),
    "note": ("note", 7),
}
def _unlicensed(w: World) -> World:
    return replace(w, aug_licensed=False)


def _unfunded(w: World) -> World:
    return replace(w, budget=0)


WITHDRAW: dict[str, Callable[[World], World]] = {"augment": _unlicensed, "spend": _unfunded}


def grants(w: World) -> list[str]:
    return sorted(c for c, ok in (("augment", w.aug_licensed), ("spend", w.budget > 0)) if ok)


def worlds() -> dict[str, World]:
    return {"licensed": TRUNC_WORLD, "unlicensed": replace(TRUNC_WORLD, aug_licensed=False)}


def row(event: tuple[object, ...]) -> list[str]:
    w = TRUNC_WORLD
    if step(w, event) == w:
        return []
    return sorted(c for c, cut in WITHDRAW.items() if step(cut(w), event) == cut(w))


def positive() -> Packet:
    ws = worlds()
    return {
        "edges": [["e1", "licensed", ["add_view"]], ["e2", "unlicensed", ["mark", "note"]]],
        "operations": [[name, row(ev)] for name, ev in OPERATIONS.items()],
        "scopes": [["licensed", None, grants(ws["licensed"])], ["unlicensed", "licensed", grants(ws["unlicensed"])]],
    }


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def decide(pk: Packet) -> tuple[str, ...]:
    failed: list[str] = []
    pos = positive()
    if pk["operations"] != pos["operations"]:
        failed.append("rows_replayed")
    if pk["scopes"] != pos["scopes"]:
        failed.append("scopes_replayed")
    ws = worlds()
    edges = pk["edges"]
    assert isinstance(edges, list)
    ops = [op for _, _, names in edges for op in names]
    if any(op not in OPERATIONS for op in ops):
        failed.append("operations_known")
    for _, scope, names in edges:
        w = ws.get(str(scope))
        if w is None or any(n in OPERATIONS and step(w, OPERATIONS[n]) == w for n in names):
            failed.append("edges_progress")
            break
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    extra = {"effect_rows": {name: row(ev) for name, ev in OPERATIONS.items()},
             "grants": {name: grants(w) for name, w in worlds().items()}}
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, LEAN, SOURCES, extra)
