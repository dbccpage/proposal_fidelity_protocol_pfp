"""Replay of research-tree evidence: a two-state toggle carried into the
passage by budget writes, with its step square and its reading square
checked on every state, and the claim kept one way.

The witness is ``research/native_bridge`` (read only, through the vendored
clone at its pin; admitted by the author's ruling of 2026-09-25): its budget
register ``budget_sim``, which carries a numbered system into the passage by
one budget write per step and which the tree's receipt runs on the toggle
``x -> 1 - x`` over the states 0 and 1 with one event; its passage replay
``preplay``; and its ``core`` of a passage state.  The positive is that
toggle, the passage states the register writes it to, the map sending each
state to its encoding, and a constant reading.  The reading is constant
because the tree finds that a budget register keeps a reading only when the
reading is constant: the passage's own reading is a function of the core,
and every budget encoding has the core of genesis.  The claim is one way:
the tree refutes reading a commuting square with an injective encoding as
the passage reproducing the source.

The target system is the passage read on the encoded states.  Each of its
steps is the budget write the register issues there, replayed by the tree's
``preplay``; each of its readings is the tree's ``core`` of the state.

Clauses, each decided on the packet:

* ``mapped``: a map is given;
* ``map_total``: the map, and the map back when one is given, sends every
  state to a state of the other system;
* ``target_native``: every target state is a budget encoding of genesis,
  every target step is one budget write the tree's replay realizes, and
  every target reading is the tree's core of that state;
* ``step_square``: for every source state, the tree's replay of the budget
  write the target step names at its image lands on the image of its
  successor;
* ``sight_square``: for every source state, its reading is the core reading
  of its image;
* ``both_ways``: a claim both ways needs the map back, its two squares, and
  both round trips the identity.

AuthorityEffect: None
"""

from __future__ import annotations

from types import ModuleType
from typing import Any, Literal

from engine.errors import Refusal
from engine.level import LevelResult
from engine.replay import Packet, Row, packets as replay_packets, result, tree_json, tree_module

CHALLENGE_ID = "register_squares"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
TREE = "native_bridge"
SOURCES = (f"research/{TREE}/bridge.py", f"research/{TREE}/evidence/receipt.json")
CLAUSES = ("mapped", "map_total", "target_native", "step_square", "sight_square", "both_ways")
# The tree's toggle, as its receipt runs it through the budget register:
# ``budget_sim(lambda x, _e: 1 - x, [0, 1], [0])``.
STATES = (0, 1)
EVENTS = (0,)
PREFIX = "budget:"


def tree() -> ModuleType:
    return tree_module(TREE, "bridge")


def toggle(x: int, _e: int) -> int:
    return 1 - x


def encoding(n: int) -> Any:
    """The register's encoding (``budget_sim``'s ``enc``): genesis with the
    budget written."""
    return tree().PS(budget=n)


def name(ps: Any) -> str:
    return f"{PREFIX}{ps.budget}"


def reading(ps: Any) -> str:
    """The tree's core of a passage state, as text."""
    return "core " + repr(tree().core(ps))


def _decode(label: object) -> Any | None:
    if not isinstance(label, str) or not label.startswith(PREFIX) or not label[len(PREFIX):].isdigit():
        return None
    ps = encoding(int(label[len(PREFIX):]))
    return ps if name(ps) == label else None


def positive() -> Packet:
    t = tree()
    kept = reading(t.GENESIS_P)
    images = {x: encoding(x) for x in STATES}
    return {
        "back": None,
        "claim": "simulation",
        "map": [[str(x), name(images[x])] for x in STATES],
        "source": {"observe": [[str(x), kept] for x in STATES], "states": [str(x) for x in STATES],
                   "step": [[str(x), str(toggle(x, e))] for x in STATES for e in EVENTS]},
        "target": {"observe": [[name(images[x]), reading(images[x])] for x in STATES],
                   "states": [name(images[x]) for x in STATES],
                   "step": [[name(images[x]), name(t.preplay([("setBudget", toggle(x, e))], images[x]))]
                            for x in STATES for e in EVENTS]},
    }


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def _system(value: object) -> tuple[list[str], dict[str, str], dict[str, str]]:
    assert isinstance(value, dict)
    states = [str(s) for s in value["states"]]
    step = {str(a): str(b) for a, b in value["step"]}
    sees = {str(a): str(b) for a, b in value["observe"]}
    return states, step, sees


def _function(rows: object, keys: list[str], into: list[str]) -> dict[str, str] | None:
    """A total function from ``keys`` into ``into``, or nothing."""
    if not isinstance(rows, list):
        return None
    out: dict[str, str] = {}
    for row in rows:
        if not (isinstance(row, list) and len(row) == 2 and row[0] in keys and row[0] not in out
                and row[1] in into):
            return None
        out[str(row[0])] = str(row[1])
    return out if set(out) == set(keys) else None


def _native(states: list[str], step: dict[str, str], sees: dict[str, str], decoded: dict[str, Any]) -> bool:
    t = tree()
    if any(ps is None for ps in decoded.values()):
        return False
    for a in states:
        b = decoded.get(step.get(a, ""))
        if b is None or t.preplay([("setBudget", b.budget)], decoded[a]) != b:
            return False
    return all(sees.get(a) == reading(decoded[a]) for a in states)


def decide(pk: Packet) -> tuple[str, ...]:
    t = tree()
    failed: list[str] = []
    s_states, s_step, s_sees = _system(pk["source"])
    t_states, t_step, t_sees = _system(pk["target"])
    decoded = {x: _decode(x) for x in t_states}
    if not _native(t_states, t_step, t_sees, decoded):
        failed.append("target_native")
    f = None if pk["map"] is None else _function(pk["map"], s_states, t_states)
    g = None if pk["back"] is None else _function(pk["back"], t_states, s_states)
    if pk["map"] is None:
        failed.append("mapped")
    elif f is None or (pk["back"] is not None and g is None):
        failed.append("map_total")
    if f is not None:
        def lands(s: str) -> bool:
            here, there, nxt = decoded.get(f[s]), decoded.get(f[s_step[s]]), decoded.get(t_step.get(f[s], ""))
            return (here is not None and there is not None and nxt is not None
                    and t.preplay([("setBudget", nxt.budget)], here) == there)

        if not all(lands(s) for s in s_states):
            failed.append("step_square")
        if not all(decoded.get(f[s]) is not None and s_sees[s] == reading(decoded[f[s]]) for s in s_states):
            failed.append("sight_square")
    if pk["claim"] == "equivalence":
        ok = f is not None and g is not None
        if f is not None and g is not None:
            ok = (all(g[t_step[x]] == s_step[g[x]] for x in t_states)
                  and all(s_sees[g[x]] == t_sees[x] for x in t_states)
                  and all(g[f[s]] == s for s in s_states) and all(f[g[x]] == x for x in t_states))
        if not ok:
            failed.append("both_ways")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    rerun = tree().budget_sim(toggle, list(STATES), list(EVENTS))
    recorded = tree_json(TREE, "evidence/receipt.json")
    assert isinstance(recorded, dict)
    if rerun != recorded["toggle"]:
        raise Refusal("RR-TREE", f"{CHALLENGE_ID}: the register rerun differs from the tree's receipt")
    extra = {"register_rerun": rerun, "states": len(STATES), "kept_reading": reading(tree().GENESIS_P)}
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, (), SOURCES, extra, trees=(TREE,))
