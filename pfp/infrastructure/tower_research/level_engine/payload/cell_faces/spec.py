# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A hosted two-dimensional cell lists three distinct points, and every side
of every cell is present.

Claim-only: there is no existential part.  Distinctness of a cell's points is not a separate clause:
a cell repeating a point has a degenerate side, which ``side_distinct``
refuses (so a separate cell-level clause could never be isolated by a
near-miss).  Nothing ever adds a missing side: that would edit the claim.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Forbid
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, Fixture

CHALLENGE_ID = "cell_faces"
ANSWER_TYPE = "D"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    side, cell, pt = e.form("side"), e.form("cell"), e.form("pt")
    c = (cell, ("x", "y", "z"))
    return Compiled(
        (
            Closure("side_first", (c,), ((side, ("x", "y")),)),
            Closure("side_last", (c,), ((side, ("y", "z")),)),
            Closure("side_outer", (c,), ((side, ("x", "z")),)),
            Closure("side_ends", ((side, ("x", "y")),), ((pt, ("x",)), (pt, ("y",)))),
            Forbid("side_distinct", ((side, ("x", "x")),)),
        )
    )
