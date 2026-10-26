# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A finite two-player table of exact payoffs, and joint moves claimed stable:
no player gains by changing only their own move.

The claim: players (the first moves first), moves, values,
``owns(p, m)``, ``pays(a, b, u, v)`` (as in the joint payoffs level) and
``stable(a, b)`` (the joint move ``(a, b)`` is claimed stable).

Relational clauses, carried by derivability over the hosted claim:
``moves_given``, ``pays_owned``, ``stable_owned`` (a claimed joint move is
made of the players' own moves), ``table_complete`` (every deviation can be
evaluated), ``one_payoff`` and ``typed``.

Decoded clause, decided over exact values outside the grammar: ``no_gain``
(for each claimed joint move and each player, no change of that player's
move alone pays that player strictly more).  A profitable deviation refutes
the claim.  Its Lean certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..joint_payoffs.spec import Row, table_rows
from ..shared import certificates, lean_list, lean_q, position, render, rows

CHALLENGE_ID = "stable_profiles"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "StableProfiles"
EXACT = ("py.exact.q",)
CLAUSES = ("no_gain",)


def own_moves(fs: FiniteStructure) -> tuple[list[int], list[int]]:
    """Each player's moves, by position."""
    first, second = fs.elements("player")[:2]
    mine = [(p, position(fs, "move", m)) for p, m in rows(fs, "owns")]
    return [k for p, k in mine if p == first and k is not None], [k for p, k in mine if p == second and k is not None]


def claimed(fs: FiniteStructure) -> list[tuple[int, int]]:
    out = []
    for a, b in rows(fs, "stable"):
        i, j = position(fs, "move", a), position(fs, "move", b)
        if i is not None and j is not None:
            out.append((i, j))
    return out


def no_gain(fs: FiniteStructure, _o: Oracle) -> bool:
    table = table_rows(fs, "pays")
    if table is None:
        return False
    paid = dict(table)
    firsts, seconds = own_moves(fs)
    for i, j in claimed(fs):
        here = paid.get((i, j))
        if here is None:
            return False
        if any((there := paid.get((k, j))) is None or there[0] > here[0] for k in firsts):
            return False
        if any((there := paid.get((i, k))) is None or there[1] > here[1] for k in seconds):
            return False
    return True


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"claimed": [list(c) for c in claimed(fs)]}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "no_gain")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    player, move, val = e.form("player"), e.form("move"), e.form("val")
    owns, pays, stable = e.form("owns"), e.form("pays"), e.form("stable")
    first, second = fx.structure.elements("player")[:2]
    return Compiled(
        (
            Total("moves_given", ((player, ("p",)),), ((owns, ("p", "m")),)),
            Closure("pays_owned", ((pays, ("a", "b", "u", "v")),), ((owns, (first, "a")), (owns, (second, "b")))),
            Closure("stable_owned", ((stable, ("a", "b")),), ((owns, (first, "a")), (owns, (second, "b")))),
            Total("table_complete", ((owns, (first, "a")), (owns, (second, "b"))), ((pays, ("a", "b", "u", "v")),)),
            Functional("one_payoff", pays, 2),
            Closure("typed", ((pays, ("a", "b", "u", "v")),), ((move, ("a",)), (move, ("b",)), (val, ("u",)), (val, ("v",)))),
        ),
        decoded=(DecodedClause("no_gain", no_gain, EXACT),),
    )


LEAN_DEFS = (
    "/-- A joint move (by positions) and the two payoffs. -/",
    "abbrev Row := Prod (Prod Nat Nat) (Prod QN QN)",
    "",
    "/-- The payoffs at a joint move, if the table has them. -/",
    "def paid (table : List Row) (jm : Prod Nat Nat) : Option (Prod QN QN) :=",
    "  (table.find? fun t => decide (t.1 = jm)).map (fun t => t.2)",
    "",
    "/-- `x` is at most `y`. -/",
    "def atMost (x y : QN) : Bool := !QN.pos (x - y)",
    "",
    "/-- No player gains by changing only their own move. -/",
    "def noGain (table : List Row) (firsts seconds : List Nat) (claims : List (Prod Nat Nat)) : Bool :=",
    "  claims.all fun c =>",
    "    match paid table c with",
    "    | none => false",
    "    | some h =>",
    "      (firsts.all fun k => match paid table (k, c.2) with",
    "        | none => false",
    "        | some t => atMost t.1 h.1) &&",
    "      (seconds.all fun k => match paid table (c.1, k) with",
    "        | none => false",
    "        | some t => atMost t.2 h.2)",
    "",
)
LEAN_CALLS = {"no_gain": "noGain table_{f} firsts_{f} seconds_{f} claims_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    table = table_rows(fs, "pays")
    assert table is not None
    firsts, seconds = own_moves(fs)

    def text(rs: list[Row]) -> str:
        return lean_list([f"(({i}, {j}), ({lean_q(x)}, {lean_q(y)}))" for (i, j), (x, y) in rs])

    return [("table", "List Row", text(table)), ("firsts", "List Nat", lean_list([str(k) for k in firsts])),
            ("seconds", "List Nat", lean_list([str(k) for k in seconds])),
            ("claims", "List (Prod Nat Nat)", lean_list([f"({i}, {j})" for i, j in claimed(fs)]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clause of `stable_profiles`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
