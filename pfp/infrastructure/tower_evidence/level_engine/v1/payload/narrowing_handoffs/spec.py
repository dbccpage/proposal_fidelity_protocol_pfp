"""Delegation replayed in declared order: the principal holds its declared
scope; a handoff may be made only by a holder, and only with a subset of
what the delegator holds at that moment (an agent handing itself scope can
narrow it, never widen it); a recipient then holds exactly what it was
last handed; and every routed task falls inside its agent's final scope.

The claim: agents, permissions, handoffs (in declared order: the order of
delegation) and tasks, ``principal(a)``, ``starts_with(p)`` (the
principal's declared scope), ``from(h, a)``, ``to(h, a)``, ``hands(h, p)``
and ``routes(t, a, p)`` (task ``t`` is routed to agent ``a`` needing
``p``).

Relational clauses, carried by derivability over the hosted claim:
``principal_given``, ``one_principal``, ``from_given``, ``one_from``,
``to_given``, ``one_to`` and ``routes_typed``.

Decoded clauses, decided outside the grammar, over the replay:
``no_expansion`` (a holder never hands more than it holds: the refused
case, an agent widening its own authority), ``rooted`` (every delegator
holds something when it hands) and ``tasks_in_scope``.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from engine.encoding import Encoding
from engine.kinds import Closure, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture
from engine.structure import FiniteStructure
from payload.shared import rows

CHALLENGE_ID = "narrowing_handoffs"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT: tuple[str, ...] = ()
CLAUSES = ("no_expansion", "rooted", "tasks_in_scope")


def replay(fs: FiniteStructure) -> tuple[dict[int, set[int]], list[tuple[bool, bool]]]:
    principal = [a for (a,) in rows(fs, "principal")]
    held: dict[int, set[int]] = {principal[0]: {p for (p,) in rows(fs, "starts_with")}} if principal else {}
    frm = {h: a for h, a in rows(fs, "from")}
    to = {h: a for h, a in rows(fs, "to")}
    steps = []
    for h in fs.elements("handoff"):
        granted = {p for hh, p in rows(fs, "hands") if hh == h}
        src, dst = frm.get(h), to.get(h)
        rooted = src in held
        steps.append((rooted, granted <= held.get(src, set()) if src is not None else False))
        if dst is not None and (not principal or dst != principal[0]):
            held[dst] = set(granted)
    return held, steps


def no_expansion(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(subset or not rooted for rooted, subset in replay(fs)[1])


def rooted(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(r for r, _ in replay(fs)[1])


def tasks_in_scope(fs: FiniteStructure, _o: Oracle) -> bool:
    held = replay(fs)[0]
    return all(p in held.get(a, set()) for _, a, p in rows(fs, "routes"))


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"held": sorted((a, sorted(ps)) for a, ps in replay(fs)[0].items())}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    agent, perm, handoff, task = e.form("agent"), e.form("perm"), e.form("handoff"), e.form("task")
    principal, frm, to, routes = e.form("principal"), e.form("from"), e.form("to"), e.form("routes")
    return Compiled(
        (
            Total("principal_given", (), ((principal, ("a",)),)),
            Functional("one_principal", principal, 0),
            Total("from_given", ((handoff, ("h",)),), ((frm, ("h", "a")),)),
            Functional("one_from", frm, 1),
            Total("to_given", ((handoff, ("h",)),), ((to, ("h", "a")),)),
            Functional("one_to", to, 1),
            Closure("routes_typed", ((routes, ("t", "a", "p")),), ((task, ("t",)), (agent, ("a",)), (perm, ("p",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("no_expansion", no_expansion), ("rooted", rooted), ("tasks_in_scope", tasks_in_scope))),
    )
