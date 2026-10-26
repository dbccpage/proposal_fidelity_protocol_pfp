# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A merge table over a declared finite set of replica states: total and
closed, and a join on every state, pair and triple (idempotent,
associative, commutative), decided by exhaustion over the declared states.
Nothing is computed from a declared law name.

The claim: states (in declared order) and ``merge(a, b, c)`` (merging ``a``
with ``b`` gives ``c``).

Relational clauses, all carried by derivability over the hosted claim:
``table_total``, ``one_result`` and ``closed`` (the table is total and a
function into the states), ``idempotent`` (merging a state with itself
gives it back: the refused case is a merge that counts a state twice),
``commutative`` and ``associative`` (a closure over three rows).

Nothing is decided over values: the level is answered by derivability
alone.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, Fixture

CHALLENGE_ID = "merge_tables"
ANSWER_TYPE = "D"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    state, merge = e.form("state"), e.form("merge")
    return Compiled(
        (
            Total("table_total", ((state, ("a",)), (state, ("b",))), ((merge, ("a", "b", "c")),)),
            Functional("one_result", merge, 2),
            Closure("closed", ((merge, ("a", "b", "c")),), ((state, ("a",)), (state, ("b",)), (state, ("c",)))),
            Closure("idempotent", ((state, ("a",)),), ((merge, ("a", "a", "a")),)),
            Closure("commutative", ((merge, ("a", "b", "c")),), ((merge, ("b", "a", "c")),)),
            Closure("associative", ((merge, ("a", "b", "d")), (merge, ("d", "c", "e")), (merge, ("b", "c", "f"))),
                    ((merge, ("a", "f", "e")),)),
        ),
    )
