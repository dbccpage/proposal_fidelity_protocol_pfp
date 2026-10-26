# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Two finite step systems with sights, and a typed map between them whose
squares must commute; a claim that the systems match both ways needs a map
back, with its own squares and both round trips.

The claim: states of the first system (``here``) and of the second
(``there``), sights, a sort ``bond`` with one element, ``here_step`` and
``there_step`` (each state's next state), ``here_sees`` and ``there_sees``
(what each state shows), ``sends(s, t)`` (the map), ``returns(t, s)`` (the
map back) and ``both_ways(k)`` (the systems are claimed to match both ways,
not only one way).

Every clause is relational, carried by derivability over the hosted claim:
the systems are well formed (``here_steps``, ``one_here_step``,
``there_steps``, ``one_there_step``, ``here_seen``, ``one_here_sight``,
``there_seen``, ``one_there_sight``); the map is given, a function, and
typed (``map_given``: a match claimed with no map is refused;
``one_image``, ``map_typed``); its squares commute on every state
(``step_square``: the map carries each step to a step; ``sight_square``: a
state and its image show the same sight); and when both ways are claimed,
the map back is given, a function and typed (``back_given``,
``one_return``, ``return_typed``), its squares commute (``back_square``,
``back_sight``), and both round trips are the identity (``round_here``,
``round_there``).  Nothing is decided over values, so the kernel has
nothing to re-decide.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, Fixture
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import rows

CHALLENGE_ID = "step_squares"
ANSWER_TYPE = "D"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"both_ways": bool(rows(fs, "both_ways")), "map_rows": len(rows(fs, "sends")),
            "back_rows": len(rows(fs, "returns"))}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    here, there, sight = e.form("here"), e.form("there"), e.form("sight")
    hs, ts, hv, tv = e.form("here_step"), e.form("there_step"), e.form("here_sees"), e.form("there_sees")
    sends, returns, both = e.form("sends"), e.form("returns"), e.form("both_ways")
    return Compiled(
        (
            Total("here_steps", ((here, ("s",)),), ((hs, ("s", "n")),)),
            Functional("one_here_step", hs, 1),
            Total("there_steps", ((there, ("t",)),), ((ts, ("t", "n")),)),
            Functional("one_there_step", ts, 1),
            Total("here_seen", ((here, ("s",)),), ((hv, ("s", "r")),)),
            Functional("one_here_sight", hv, 1),
            Total("there_seen", ((there, ("t",)),), ((tv, ("t", "r")),)),
            Functional("one_there_sight", tv, 1),
            Total("map_given", ((here, ("s",)),), ((sends, ("s", "t")),)),
            Functional("one_image", sends, 1),
            Closure("map_typed", ((sends, ("s", "t")),), ((here, ("s",)), (there, ("t",)))),
            Closure("step_square", ((sends, ("s", "t")), (hs, ("s", "s2")), (ts, ("t", "t2"))), ((sends, ("s2", "t2")),)),
            Closure("sight_square", ((sends, ("s", "t")), (hv, ("s", "r"))), ((tv, ("t", "r")),)),
            Total("back_given", ((both, ("k",)), (there, ("t",))), ((returns, ("t", "s")),)),
            Functional("one_return", returns, 1),
            Closure("return_typed", ((returns, ("t", "s")),), ((there, ("t",)), (here, ("s",)))),
            Closure("back_square", ((both, ("k",)), (returns, ("t", "s")), (ts, ("t", "t2")), (hs, ("s", "s2"))),
                    ((returns, ("t2", "s2")),)),
            Closure("back_sight", ((both, ("k",)), (returns, ("t", "s")), (tv, ("t", "r"))), ((hv, ("s", "r")),)),
            Closure("round_here", ((both, ("k",)), (sends, ("s", "t"))), ((returns, ("t", "s")),)),
            Closure("round_there", ((both, ("k",)), (returns, ("t", "s"))), ((sends, ("s", "t")),)),
        ),
    )
