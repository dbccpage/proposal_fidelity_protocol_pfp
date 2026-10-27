# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A family of finite sets over a finite order of stages: each element lies
at one stage, and restricts to one element at every stage below its own.
Restrictions compose.  A subfamily is closed under restriction, and each
element carries a label, a set of stages at or below its own, which must
be the recomputed one: the stages where the element's restriction (itself,
at its own stage) lies in the subfamily.  The subfamily is exactly the set
of elements labelled true at their own stage.

The claim: stages and elements (each in declared order), ``below(q, p)``
(stage ``q`` lies strictly below ``p``; the order is given closed under
chains), ``at(x, p)``, ``restricts(x, q, y)`` (``x`` restricts to ``y`` at
stage ``q``), ``in_sub(x)`` and ``label(x, q)`` (``q`` lies in ``x``'s
label).

Relational clauses, carried by derivability over the hosted claim:

* the family: ``below_typed``, ``below_transitive``, ``below_strict``,
  ``at_given``, ``one_at``, ``at_typed``, ``restriction_total`` (every
  element restricts to every stage below its own), ``restriction_from``,
  ``restriction_down``, ``restriction_lands``, ``one_restriction`` and
  ``restrictions_compose``;
* the subfamily: ``sub_typed`` and ``sub_closed`` (closed under
  restriction);
* the labels: ``label_typed``, ``label_forward`` and ``label_back`` (below
  its own stage, a label holds a stage exactly when the restriction there
  lies in the subfamily);
* the pullback: ``true_on_sub`` and ``pullback`` (an element lies in the
  subfamily exactly when its label holds its own stage: the refused case is
  a label read two-valued, true on an element whose restrictions lie in the
  subfamily while it does not).

Decoded clause, decided outside the grammar: ``label_within`` (every stage
of a label is its element's stage or below it; "one or the other" is not a
closure the grammar states).

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.kinds import Closure, Forbid, Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import rows

CHALLENGE_ID = "recomputed_labels"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT: tuple[str, ...] = ()
CLAUSES = ("label_within",)


def label_within(fs: FiniteStructure, _o: Oracle) -> bool:
    stage: dict[int, list[int]] = {}
    for x, p in rows(fs, "at"):
        stage.setdefault(x, []).append(p)
    below = set(rows(fs, "below"))
    for x, q in rows(fs, "label"):
        own = stage.get(x, [])
        if len(own) != 1 or (q != own[0] and (q, own[0]) not in below):
            return False
    return True


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    stage, element = e.form("stage"), e.form("element")
    below, at, res, sub, label = e.form("below"), e.form("at"), e.form("restricts"), e.form("in_sub"), e.form(
        "label")
    return Compiled(
        (
            Closure("below_typed", ((below, ("q", "p")),), ((stage, ("q",)), (stage, ("p",)))),
            Closure("below_transitive", ((below, ("r", "q")), (below, ("q", "p"))), ((below, ("r", "p")),)),
            Forbid("below_strict", ((below, ("p", "p")),)),
            Total("at_given", ((element, ("x",)),), ((at, ("x", "p")),)),
            Functional("one_at", at, 1),
            Closure("at_typed", ((at, ("x", "p")),), ((element, ("x",)), (stage, ("p",)))),
            Total("restriction_total", ((at, ("x", "p")), (below, ("q", "p"))), ((res, ("x", "q", "y")),)),
            Total("restriction_from", ((res, ("x", "q", "y")),), ((at, ("x", "p")),)),
            Closure("restriction_down", ((res, ("x", "q", "y")), (at, ("x", "p"))), ((below, ("q", "p")),)),
            Closure("restriction_lands", ((res, ("x", "q", "y")),), ((at, ("y", "q")),)),
            Functional("one_restriction", res, 2),
            Closure("restrictions_compose", ((res, ("x", "q", "y")), (res, ("y", "r", "z"))),
                    ((res, ("x", "r", "z")),)),
            Closure("sub_typed", ((sub, ("x",)),), ((element, ("x",)),)),
            Closure("sub_closed", ((sub, ("x",)), (res, ("x", "q", "y"))), ((sub, ("y",)),)),
            Closure("label_typed", ((label, ("x", "q")),), ((element, ("x",)), (stage, ("q",)))),
            Closure("label_forward", ((res, ("x", "q", "y")), (sub, ("y",))), ((label, ("x", "q")),)),
            Closure("label_back", ((label, ("x", "q")), (res, ("x", "q", "y"))), ((sub, ("y",)),)),
            Closure("true_on_sub", ((sub, ("x",)), (at, ("x", "p"))), ((label, ("x", "p")),)),
            Closure("pullback", ((label, ("x", "p")), (at, ("x", "p"))), ((sub, ("x",)),)),
        ),
        decoded=(DecodedClause("label_within", label_within, EXACT),),
    )
