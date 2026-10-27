# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Two finite endpoints that exchange kinds of message: a joint step fires
when one endpoint sends a kind and the other receives the same kind, and
both move.  Every joint state reachable from the two starts is decided.

The claim: the first endpoint's states (``here``), the second's
(``there``), kinds, ``here_start(s)``, ``there_start(t)``,
``here_final(s)``, ``there_final(t)``, ``here_send(s, k, n)``,
``here_receive(s, k, n)``, ``there_send(t, k, n)`` and
``there_receive(t, k, n)`` (from a state, sending or receiving kind ``k``
leads to ``n``).

Relational clauses, carried by derivability over the hosted claim:
``starts_given``, ``one_here_start``, ``one_there_start`` and determinism
(``one_here_send``, ``one_here_receive``, ``one_there_send``,
``one_there_receive``: at most one move per state, action and kind).

Decoded clauses, decided outside the grammar by exploring the reachable
joint states breadth first: ``no_mutual_wait`` (no reachable joint state
where both endpoints wait only to receive), ``sends_matched`` (whatever one
endpoint may send there, the other can receive), ``never_stuck`` (every
reachable joint state has a joint step, or both endpoints are final) and
``end_reached`` (some reachable joint state has both endpoints final).
Their Lean certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import certificates, lean_list, position, render, rows

CHALLENGE_ID = "dual_endpoints"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "DualEndpoints"
EXACT: tuple[str, ...] = ()
CLAUSES = ("no_mutual_wait", "sends_matched", "never_stuck", "end_reached")
Move = tuple[int, int, int]


@dataclass(frozen=True)
class Endpoint:
    start: int
    final: frozenset[int]
    send: tuple[Move, ...]
    receive: tuple[Move, ...]


def endpoint(fs: FiniteStructure, side: str) -> Endpoint:
    def p(e: int, sort: str) -> int:
        k = position(fs, sort, e)
        return -1 if k is None else k

    starts = [p(s, side) for (s,) in rows(fs, f"{side}_start")]

    def moves(action: str) -> tuple[Move, ...]:
        return tuple(sorted((p(s, side), p(k, "kind"), p(n, side)) for s, k, n in rows(fs, f"{side}_{action}")))

    return Endpoint(starts[0] if starts else -1, frozenset(p(s, side) for (s,) in rows(fs, f"{side}_final")),
                    moves("send"), moves("receive"))


def _offers(ms: tuple[Move, ...], state: int) -> dict[int, int]:
    return {k: n for s, k, n in ms if s == state}


def explore(fs: FiniteStructure) -> dict[str, bool]:
    """The four verdicts over every reachable joint state."""
    a, b = endpoint(fs, "here"), endpoint(fs, "there")
    start = (a.start, b.start)
    seen, queue = {start}, [start]
    out = {"no_mutual_wait": True, "sends_matched": True, "never_stuck": True, "end_reached": False}
    while queue:
        p, q = queue.pop(0)
        ps, pr, qs, qr = _offers(a.send, p), _offers(a.receive, p), _offers(b.send, q), _offers(b.receive, q)
        if pr and qr and not ps and not qs:
            out["no_mutual_wait"] = False
        if not (set(ps) <= set(qr) and set(qs) <= set(pr)):
            out["sends_matched"] = False
        steps = [(ps[k], qr[k]) for k in ps if k in qr] + [(pr[k], qs[k]) for k in qs if k in pr]
        both = p in a.final and q in b.final
        out["end_reached"] = out["end_reached"] or both
        if not steps and not both:
            out["never_stuck"] = False
        for st in steps:
            if st not in seen:
                seen.add(st)
                queue.append(st)
    return out


def _clause(name: str) -> DecodedClause:
    def fn(fs: FiniteStructure, _o: Oracle) -> bool:
        return explore(fs)[name]

    return DecodedClause(name, fn, EXACT)


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"verdicts": explore(fs)}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "end_reached")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    return Compiled(
        (
            Total("starts_given", (), ((e.form("here_start"), ("s",)), (e.form("there_start"), ("t",)))),
            Functional("one_here_start", e.form("here_start"), 0),
            Functional("one_there_start", e.form("there_start"), 0),
            Functional("one_here_send", e.form("here_send"), 2),
            Functional("one_here_receive", e.form("here_receive"), 2),
            Functional("one_there_send", e.form("there_send"), 2),
            Functional("one_there_receive", e.form("there_receive"), 2),
        ),
        decoded=tuple(_clause(c) for c in CLAUSES),
    )


LEAN_DEFS = (
    "/-- A move: state, kind, next state. -/",
    "abbrev Move := Prod Nat (Prod Nat Nat)",
    "",
    "/-- An endpoint: start, final states, sends, receives. -/",
    "structure End where",
    "  start : Nat",
    "  final : List Nat",
    "  send : List Move",
    "  recv : List Move",
    "",
    "def offers (ms : List Move) (s : Nat) : List (Prod Nat Nat) := (ms.filter fun m => m.1 == s).map fun m => m.2",
    "",
    "def steps (a b : End) (j : Prod Nat Nat) : List (Prod Nat Nat) :=",
    "  let ps := offers a.send j.1; let pr := offers a.recv j.1",
    "  let qs := offers b.send j.2; let qr := offers b.recv j.2",
    "  (ps.filterMap fun x => (qr.find? fun y => y.1 == x.1).map fun y => (x.2, y.2)) ++",
    "    (qs.filterMap fun y => (pr.find? fun x => x.1 == y.1).map fun x => (x.2, y.2))",
    "",
    "/-- The reachable joint states, breadth first, with `fuel` rounds. -/",
    "def reach (a b : End) : Nat -> List (Prod Nat Nat) -> List (Prod Nat Nat)",
    "  | 0, seen => seen",
    "  | fuel + 1, seen =>",
    "    let next := seen.foldl (fun acc j => (steps a b j).foldl (fun acc s => if acc.contains s then acc else acc ++ [s]) acc) seen",
    "    reach a b fuel next",
    "",
    "def states (a b : End) (fuel : Nat) : List (Prod Nat Nat) := reach a b fuel [(a.start, b.start)]",
    "",
    "def noMutualWait (a b : End) (fuel : Nat) : Bool :=",
    "  (states a b fuel).all fun j =>",
    "    !(!(offers a.recv j.1).isEmpty && !(offers b.recv j.2).isEmpty && (offers a.send j.1).isEmpty && (offers b.send j.2).isEmpty)",
    "",
    "def sendsMatched (a b : End) (fuel : Nat) : Bool :=",
    "  (states a b fuel).all fun j =>",
    "    (offers a.send j.1).all (fun x => (offers b.recv j.2).any fun y => y.1 == x.1) &&",
    "    (offers b.send j.2).all (fun y => (offers a.recv j.1).any fun x => x.1 == y.1)",
    "",
    "def bothFinal (a b : End) (j : Prod Nat Nat) : Bool := a.final.contains j.1 && b.final.contains j.2",
    "",
    "def neverStuck (a b : End) (fuel : Nat) : Bool :=",
    "  (states a b fuel).all fun j => !(steps a b j).isEmpty || bothFinal a b j",
    "",
    "def endReached (a b : End) (fuel : Nat) : Bool := (states a b fuel).any (bothFinal a b)",
    "",
)
LEAN_CALLS = {"no_mutual_wait": "noMutualWait here_{f} there_{f} fuel_{f}",
              "sends_matched": "sendsMatched here_{f} there_{f} fuel_{f}",
              "never_stuck": "neverStuck here_{f} there_{f} fuel_{f}", "end_reached": "endReached here_{f} there_{f} fuel_{f}"}


def _end_text(e: Endpoint) -> str:
    def ms(xs: tuple[Move, ...]) -> str:
        return lean_list([f"({s}, ({k}, {n}))" for s, k, n in xs])

    return (f"{{ start := {e.start}, final := {lean_list([str(x) for x in sorted(e.final)])}, "
            f"send := {ms(e.send)}, recv := {ms(e.receive)} }}")


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    a, b = endpoint(fs, "here"), endpoint(fs, "there")
    assert a.start >= 0 and b.start >= 0
    fuel = len(fs.elements("here")) * len(fs.elements("there"))
    return [("here", "End", _end_text(a)), ("there", "End", _end_text(b)), ("fuel", "Nat", str(fuel))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The clauses of `dual_endpoints`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
