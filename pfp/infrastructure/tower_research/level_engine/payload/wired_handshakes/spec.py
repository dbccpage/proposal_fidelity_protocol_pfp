# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A component graph with named, directed, typed ports and wires: every wire
joins one output port to one input port of the same message type (which
end is the output is read from the port declarations, never from the
wire's order), each port is wired at most once, and every pair of
components wired in one direction is wired in the other as well.

The claim: components, ports, message types and wires (each in declared
order), ``port_of(p, c)``, ``sends(p)`` (an output port), ``receives(p)``
(an input port), ``carries(p, t)`` and ``joins(w, a, b)``.

Relational clauses, carried by derivability over the hosted claim:
``first_end_declared`` and ``second_end_declared`` (a wire's ends are
declared ports), ``not_two_outputs`` (the refused case: two output ports
joined), ``not_two_inputs``, ``same_type``, ``one_type``, ``one_owner`` and
``one_way_per_port`` (no port both sends and receives).

Decoded clauses, decided outside the grammar: ``wired_once`` (no port is
on two wire ends) and ``both_directions`` (for every flow from one
component to another there is a flow back).

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.kinds import Closure, Forbid, Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import rows

CHALLENGE_ID = "wired_handshakes"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT: tuple[str, ...] = ()
CLAUSES = ("wired_once", "both_directions")


def wired_once(fs: FiniteStructure, _o: Oracle) -> bool:
    ends = [e for _, a, b in rows(fs, "joins") for e in (a, b)]
    return len(set(ends)) == len(ends)


def flows(fs: FiniteStructure) -> set[tuple[int, int]]:
    owner = {p: c for p, c in rows(fs, "port_of")}
    out = {p for (p,) in rows(fs, "sends")}
    got = set()
    for _, a, b in rows(fs, "joins"):
        if (a in out) != (b in out) and a in owner and b in owner:
            src, sink = (a, b) if a in out else (b, a)
            got.add((owner[src], owner[sink]))
    return got


def both_directions(fs: FiniteStructure, _o: Oracle) -> bool:
    f = flows(fs)
    return all((b, a) in f for a, b in f)


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"flows": sorted(list(x) for x in flows(fs))}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    port_of, sends, receives, carries, joins = (e.form("port_of"), e.form("sends"), e.form("receives"),
                                                e.form("carries"), e.form("joins"))
    return Compiled(
        (
            Total("first_end_declared", ((joins, ("w", "a", "b")),), ((port_of, ("a", "c")),)),
            Total("second_end_declared", ((joins, ("w", "a", "b")),), ((port_of, ("b", "c")),)),
            Forbid("not_two_outputs", ((joins, ("w", "a", "b")), (sends, ("a",)), (sends, ("b",)))),
            Forbid("not_two_inputs", ((joins, ("w", "a", "b")), (receives, ("a",)), (receives, ("b",)))),
            Closure("same_type", ((joins, ("w", "a", "b")), (carries, ("a", "t"))), ((carries, ("b", "t")),)),
            Functional("one_type", carries, 1),
            Functional("one_owner", port_of, 1),
            Forbid("one_way_per_port", ((sends, ("p",)), (receives, ("p",)))),
        ),
        decoded=(DecodedClause("wired_once", wired_once, EXACT),
                 DecodedClause("both_directions", both_directions, EXACT)),
    )
