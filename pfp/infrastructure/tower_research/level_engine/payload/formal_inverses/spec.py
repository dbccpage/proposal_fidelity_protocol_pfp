# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A finite table of objects and arrows with a full composition table, a
declared class of weak arrows, and roofs: each roof inverts one leg
formally and keeps the other.  The table obeys the unit and bracketing
laws, the weak class holds every identity and is closed under composition,
and every roof inverts a weak arrow and is typed at its shared start.

The claim: objects and arrows (each in declared order), ``runs(a, s, t)``
(arrow ``a`` runs from ``s`` to ``t``), ``identity(o, a)``, ``compose(f, g,
h)`` (``h`` is ``g`` after ``f``: ``f`` first), ``weak(a)`` (``a`` is in
the weak class) and ``roof(w, f, b, c)`` (the roof that inverts ``w`` and
keeps ``f``, read as a formal arrow from ``b`` to ``c``).

Relational clauses, all carried by derivability over the hosted claim:

* the table: ``runs_given``, ``one_runs``, ``runs_typed``,
  ``identity_given``, ``one_identity``, ``identity_endo``,
  ``composable_total`` (every composable pair has a composite),
  ``one_composite``, ``chain_middle`` and ``chain_ends`` (a composite is
  typed), ``compose_typed``, ``left_unit``, ``right_unit`` and
  ``associative`` (the two bracketings of three arrows agree);
* the weak class: ``weak_typed``, ``weak_identities`` and
  ``weak_composes``;
* the roofs: ``inverts_weak`` (the inverted leg is weak: the refused case
  is a roof that inverts an arrow outside the class), ``roof_left`` (the
  inverted leg ends at the roof's start) and
  ``roof_right`` (the kept leg shares the inverted leg's start and ends at
  the roof's end).

Nothing is decided over values: the level is answered by derivability
alone.  Classes of roofs, and whether they compose, are not decided.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, Fixture

CHALLENGE_ID = "formal_inverses"
ANSWER_TYPE = "D"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    obj, arrow = e.form("object"), e.form("arrow")
    runs, ident, comp, weak, roof = e.form("runs"), e.form("identity"), e.form("compose"), e.form("weak"), e.form(
        "roof")
    return Compiled(
        (
            Total("runs_given", ((arrow, ("a",)),), ((runs, ("a", "s", "t")),)),
            Functional("one_runs", runs, 1),
            Closure("runs_typed", ((runs, ("a", "s", "t")),), ((arrow, ("a",)), (obj, ("s",)), (obj, ("t",)))),
            Total("identity_given", ((obj, ("o",)),), ((ident, ("o", "a")),)),
            Functional("one_identity", ident, 1),
            Closure("identity_endo", ((ident, ("o", "a")),), ((runs, ("a", "o", "o")),)),
            Total("composable_total", ((runs, ("f", "a", "b")), (runs, ("g", "b", "c"))),
                  ((comp, ("f", "g", "h")),)),
            Functional("one_composite", comp, 2),
            Total("chain_middle", ((comp, ("f", "g", "h")), (runs, ("f", "a", "b"))), ((runs, ("g", "b", "c")),)),
            Closure("chain_ends", ((comp, ("f", "g", "h")), (runs, ("f", "a", "b")), (runs, ("g", "b", "c"))),
                    ((runs, ("h", "a", "c")),)),
            Closure("compose_typed", ((comp, ("f", "g", "h")),), ((arrow, ("f",)), (arrow, ("g",)), (arrow, ("h",)))),
            Closure("left_unit", ((ident, ("o", "i")), (runs, ("f", "o", "t"))), ((comp, ("i", "f", "f")),)),
            Closure("right_unit", ((ident, ("o", "i")), (runs, ("f", "s", "o"))), ((comp, ("f", "i", "f")),)),
            Closure("associative", ((comp, ("f", "g", "u")), (comp, ("g", "h", "v")), (comp, ("u", "h", "x"))),
                    ((comp, ("f", "v", "x")),)),
            Closure("weak_typed", ((weak, ("a",)),), ((arrow, ("a",)),)),
            Closure("weak_identities", ((ident, ("o", "a")),), ((weak, ("a",)),)),
            Closure("weak_composes", ((weak, ("f",)), (weak, ("g",)), (comp, ("f", "g", "h"))), ((weak, ("h",)),)),
            Closure("inverts_weak", ((roof, ("w", "f", "b", "c")),), ((weak, ("w",)),)),
            Total("roof_left", ((roof, ("w", "f", "b", "c")),), ((runs, ("w", "s", "b")),)),
            Closure("roof_right", ((roof, ("w", "f", "b", "c")), (runs, ("w", "s", "b"))), ((runs, ("f", "s", "c")),)),
        ),
    )
