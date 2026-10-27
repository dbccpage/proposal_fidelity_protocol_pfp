# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Sections on the patches of a finite cover, and a claimed glue: every point
is covered, each section is defined exactly on its patch, sections agree
wherever patches overlap, and the glue is a global assignment restricting
to every section.

The claim: points, patches and values (each in declared order),
``member(x, p)`` (point ``x`` lies in patch ``p``), ``assigns(p, x, v)``
(the section on patch ``p`` gives point ``x`` the value ``v``) and
``glue(x, v)`` (the claimed glue gives ``x`` the value ``v``).

Relational clauses, carried by derivability over the hosted claim:
``covered`` (every point lies in a patch), ``defined_on_patch`` and
``within_patch`` (each section is defined exactly on its patch),
``glue_total``, ``glue_restricts`` (every section's value is the glue's),
``one_assign``, ``one_glue`` and the typing closures.

Nothing is decided over values: the level is answered by derivability
alone.  A conflict on an overlap is refused natively: with one glue value
per point, two sections disagreeing at a shared point cannot both restrict
the glue (``glue_restricts``), which is the refused case, locally agreeing
sections with conflicting overlaps.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, Fixture

CHALLENGE_ID = "glued_patches"
ANSWER_TYPE = "D"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    point, patch, value = e.form("point"), e.form("patch"), e.form("value")
    member, assigns, glue = e.form("member"), e.form("assigns"), e.form("glue")
    return Compiled(
        (
            Total("covered", ((point, ("x",)),), ((member, ("x", "p")),)),
            Total("defined_on_patch", ((member, ("x", "p")),), ((assigns, ("p", "x", "v")),)),
            Closure("within_patch", ((assigns, ("p", "x", "v")),), ((member, ("x", "p")),)),
            Total("glue_total", ((point, ("x",)),), ((glue, ("x", "v")),)),
            Closure("glue_restricts", ((assigns, ("p", "x", "v")),), ((glue, ("x", "v")),)),
            Functional("one_assign", assigns, 2),
            Functional("one_glue", glue, 1),
            Closure("member_typed", ((member, ("x", "p")),), ((point, ("x",)), (patch, ("p",)))),
            Closure("assigns_typed", ((assigns, ("p", "x", "v")),), ((patch, ("p",)), (point, ("x",)),
                                                                        (value, ("v",)))),
            Closure("glue_typed", ((glue, ("x", "v")),), ((point, ("x",)), (value, ("v",)))),
        ),
    )
