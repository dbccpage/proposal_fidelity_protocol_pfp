# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""One merged append-only log of events with scalar clocks: every parent is
an event of the log appended before the event naming it, a clock exceeds
each parent's clock, and at each node the clocks strictly increase in log
order.

The claim: entries and nodes (each in declared order; the logged entries,
in declared order, are the log), each entry carrying its clock as a value,
``logged(e)`` (entry ``e`` was appended to the log), ``at(e, n)`` (event
``e`` happened at node ``n``) and ``parent(e, p)``.

Relational clauses, carried by derivability over the hosted claim:
``parents_logged`` (a parent is an event of the log), ``at_given``,
``one_node`` and ``parent_typed``.

Decoded clauses, decided outside the grammar: ``well_formed`` (clocks are
naturals on every logged entry), ``parents_earlier`` (a parent was appended
before the event naming it: the refused case is an event naming a future
parent), ``clocks_rise`` (an event's clock exceeds each parent's) and
``node_order`` (at each node, clocks strictly increase in log order).  The
last three are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import certificates, lean_list, render, rows

CHALLENGE_ID = "ordered_log"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "OrderedLog"
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "parents_earlier", "clocks_rise", "node_order")
LEAN_CLAUSES = CLAUSES[1:]


def log(fs: FiniteStructure) -> list[int]:
    got = {e for (e,) in rows(fs, "logged")}
    return [e for e in fs.elements("entry") if e in got]


def clock(fs: FiniteStructure, e: int) -> int:
    v = fs.value(e)
    return v.num if v is not None and v.den == 1 and v.num >= 0 else -1


def events(fs: FiniteStructure) -> list[tuple[int, int, list[int]]]:
    """(node position, clock, parent log positions) in log order; -1 for a
    parent off the log."""
    lg = log(fs)
    nodes = fs.elements("node")
    at = {e: nodes.index(n) for e, n in rows(fs, "at") if n in nodes}
    out = []
    for e in lg:
        ps = sorted(lg.index(p) if p in lg else -1 for x, p in rows(fs, "parent") if x == e)
        out.append((at.get(e, -1), clock(fs, e), ps))
    return out


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    return bool(log(fs)) and all(clock(fs, e) >= 0 for e in log(fs))


def parents_earlier(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(0 <= p < k for k, (_, _, ps) in enumerate(events(fs)) for p in ps)


def clocks_rise(fs: FiniteStructure, _o: Oracle) -> bool:
    ev = events(fs)
    return all(ev[p][1] < c for _, c, ps in ev for p in ps if 0 <= p < len(ev))


def node_order(fs: FiniteStructure, _o: Oracle) -> bool:
    last: dict[int, int] = {}
    for n, c, _ in events(fs):
        if n in last and not last[n] < c:
            return False
        last[n] = c
    return True


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"events": [[n, c, ps] for n, c, ps in events(fs)]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, LEAN_CLAUSES, verdicts, "node_order")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    entry = e.form("entry")
    logged, at, parent = e.form("logged"), e.form("at"), e.form("parent")
    return Compiled(
        (
            Closure("parents_logged", ((parent, ("e", "p")),), ((logged, ("p",)),)),
            Total("at_given", ((logged, ("e",)),), ((at, ("e", "n")),)),
            Functional("one_node", at, 1),
            Closure("parent_typed", ((parent, ("e", "p")),), ((entry, ("e",)), (entry, ("p",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("parents_earlier", parents_earlier), ("clocks_rise", clocks_rise),
            ("node_order", node_order))),
    )


LEAN_DEFS = (
    "/-- An event: its node, its clock, and its parents' log positions. -/",
    "abbrev Ev := Prod Nat (Prod Nat (List Nat))",
    "",
    "def parentsEarlier (es : List Ev) : Bool :=",
    "  (List.range es.length).all fun k => (es.getD k (0, (0, []))).2.2.all fun p => p < k",
    "",
    "def clocksRise (es : List Ev) : Bool :=",
    "  es.all fun e => e.2.2.all fun p => (es.getD p (0, (0, []))).2.1 < e.2.1",
    "",
    "def nodeOrder (es : List Ev) : Bool :=",
    "  (List.range es.length).all fun j => (List.range j).all fun i =>",
    "    (es.getD i (0, (0, []))).1 != (es.getD j (0, (0, []))).1 ||",
    "      (es.getD i (0, (0, []))).2.1 < (es.getD j (0, (0, []))).2.1",
    "",
)
LEAN_CALLS = {"parents_earlier": "parentsEarlier events_{f}", "clocks_rise": "clocksRise events_{f}",
              "node_order": "nodeOrder events_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    ev = events(fs)
    assert all(n >= 0 and c >= 0 and all(p >= 0 for p in ps) for n, c, ps in ev)
    return [("events", "List Ev", lean_list([f"({n}, ({c}, {lean_list([str(p) for p in ps])}))"
                                            for n, c, ps in ev]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The order clauses of `ordered_log`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
