"""Contexts of items with a local rule, and a family of local choices of
labels that must agree wherever two contexts share an item.

The claim: items, contexts, labels, ``member(c, x)`` (item ``x`` is in
context ``c``), ``differ(c)`` or ``equal(c)`` (the local rule: the chosen
labels are pairwise distinct, or all the same), and ``chooses(c, x, l)``
(context ``c``'s choice gives item ``x`` the label ``l``).

Relational clauses, carried by derivability over the hosted claim:
``members_given`` (every context has an item), ``chosen`` (every member is
given a label in its context), ``one_choice`` and ``choice_typed`` (a
choice is for a member, and is a label).

Decoded clauses, decided outside the grammar (they need distinctness, which
the grammar's requirements cannot state): ``local_rules`` (every context has
exactly one rule, and its choice follows it) and ``overlaps_agree`` (two
contexts that share an item give it the same label, over every pair of
contexts, not only neighbours).  A family that follows every local rule and
disagrees on an overlap is refused.  Their Lean certificates are re-decided
by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from engine.encoding import Encoding
from engine.kinds import Closure, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from engine.structure import FiniteStructure
from payload.shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "overlap_choices"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "OverlapChoices"
EXACT: tuple[str, ...] = ()
CLAUSES = ("local_rules", "overlaps_agree")
NO_RULE, DIFFER, EQUAL, BOTH = 0, 1, 2, 3


def contexts(fs: FiniteStructure) -> list[tuple[list[int], int]]:
    """Each context's items (by position, in declared item order) and rule."""
    out = []
    differ = {c for (c,) in rows(fs, "differ")}
    equal = {c for (c,) in rows(fs, "equal")}
    for c in fs.elements("context"):
        items = sorted(k for cc, x in rows(fs, "member") if cc == c and (k := position(fs, "item", x)) is not None)
        out.append((items, (DIFFER if c in differ else 0) + (EQUAL if c in equal else 0)))
    return out


def choices(fs: FiniteStructure) -> list[tuple[int, int, int]]:
    """(context, item, label) by positions."""
    out = []
    for c, x, lab in rows(fs, "chooses"):
        i, j, k = position(fs, "context", c), position(fs, "item", x), position(fs, "label", lab)
        if i is not None and j is not None and k is not None:
            out.append((i, j, k))
    return sorted(out)


def local_rules(fs: FiniteStructure, _o: Oracle) -> bool:
    got = {(i, j): k for i, j, k in choices(fs)}
    for i, (items, rule) in enumerate(contexts(fs)):
        labels = [got.get((i, j)) for j in items]
        if rule not in (DIFFER, EQUAL) or None in labels:
            return False
        if rule == DIFFER and len(set(labels)) != len(labels):
            return False
        if rule == EQUAL and len(set(labels)) != 1:
            return False
    return True


def overlaps_agree(fs: FiniteStructure, _o: Oracle) -> bool:
    ch = choices(fs)
    return all(a[2] == b[2] for a in ch for b in ch if a[1] == b[1])


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"choices": [list(c) for c in choices(fs)]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "local_rules")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    context, label = e.form("context"), e.form("label")
    member, chooses = e.form("member"), e.form("chooses")
    return Compiled(
        (
            Total("members_given", ((context, ("c",)),), ((member, ("c", "x")),)),
            Total("chosen", ((member, ("c", "x")),), ((chooses, ("c", "x", "l")),)),
            Functional("one_choice", chooses, 2),
            Closure("choice_typed", ((chooses, ("c", "x", "l")),), ((member, ("c", "x")), (label, ("l",)))),
        ),
        decoded=(DecodedClause("local_rules", local_rules, EXACT), DecodedClause("overlaps_agree", overlaps_agree, EXACT)),
    )


LEAN_DEFS = (
    "/-- The label a context's choice gives an item, if any. -/",
    "def labelOf (ch : List (Prod Nat (Prod Nat Nat))) (c x : Nat) : Option Nat :=",
    "  (ch.find? fun t => t.1 == c && t.2.1 == x).map (fun t => t.2.2)",
    "",
    "/-- Every context has one rule (1 distinct, 2 all the same) and its choice follows it. -/",
    "def localRules (cs : List (Prod (List Nat) Nat)) (ch : List (Prod Nat (Prod Nat Nat))) : Bool :=",
    "  (List.range cs.length).all fun i =>",
    "    let c := cs.getD i ([], 0)",
    "    let ls := c.1.map (fun x => labelOf ch i x)",
    "    ls.all (fun l => l.isSome) &&",
    "      (if c.2 == 1 then ls.all (fun l => ls.count l == 1)",
    "       else if c.2 == 2 then ls.all (fun l => l == ls.headD none)",
    "       else false)",
    "",
    "/-- Two choices that give one item a label give it the same label. -/",
    "def overlapsAgree (ch : List (Prod Nat (Prod Nat Nat))) : Bool :=",
    "  ch.all fun a => ch.all fun b => a.2.1 != b.2.1 || a.2.2 == b.2.2",
    "",
)
LEAN_CALLS = {"local_rules": "localRules contexts_{f} choices_{f}", "overlaps_agree": "overlapsAgree choices_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    cs = [f"({lean_list([str(j) for j in items])}, {rule})" for items, rule in contexts(fs)]
    ch = [f"({i}, ({j}, {k}))" for i, j, k in choices(fs)]
    return [("contexts", "List (Prod (List Nat) Nat)", lean_list(cs)),
            ("choices", "List (Prod Nat (Prod Nat Nat))", lean_list(ch))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The clauses of `overlap_choices`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
