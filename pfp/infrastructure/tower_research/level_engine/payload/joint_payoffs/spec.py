# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A finite two-player table of exact payoffs, and claims of what joint moves
yield, evaluated on the table.

The claim: players (the first moves first), moves, values,
``owns(p, m)`` (move ``m`` is one of player ``p``'s moves),
``pays(a, b, u, v)`` (when the first player moves ``a`` and the second
``b``, they are paid ``u`` and ``v``) and ``claims(a, b, u, v)`` (a record
says that joint move pays ``u`` and ``v``).

Relational clauses, carried by derivability over the hosted claim:
``moves_given`` (each player has a move), ``pays_owned`` and
``claims_owned`` (every joint move in the table or in a claim is made of the
players' own moves: an undefined joint move has no payoff),
``table_complete`` (every joint move of declared moves is paid),
``one_payoff`` and ``typed``.

Decoded clause, decided over exact values outside the grammar:
``claims_match`` (each claim's payoffs are the table's at its joint move).
Its Lean certificates are re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.exact.q import Q
from operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import certificates, lean_list, lean_q, position, render, rows

CHALLENGE_ID = "joint_payoffs"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "JointPayoffs"
EXACT = ("py.exact.q",)
CLAUSES = ("claims_match",)
Row = tuple[tuple[int, int], tuple[Q, Q]]


def table_rows(fs: FiniteStructure, name: str) -> list[Row] | None:
    """``name``'s rows as ((first move, second move), (first pay, second pay)),
    moves by position; ``None`` when a value is undecodable."""
    out = []
    for a, b, u, v in rows(fs, name):
        i, j, x, y = position(fs, "move", a), position(fs, "move", b), fs.value(u), fs.value(v)
        if i is None or j is None or x is None or y is None:
            return None
        out.append(((i, j), (x, y)))
    return out


def claims_match(fs: FiniteStructure, _o: Oracle) -> bool:
    table, claims = table_rows(fs, "pays"), table_rows(fs, "claims")
    if table is None or claims is None:
        return False
    paid = dict(table)
    return all(paid.get(at) == pay for at, pay in claims)


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"joint_moves_paid": len(rows(fs, "pays")), "claims": len(rows(fs, "claims"))}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "claims_match")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    player, move, val = e.form("player"), e.form("move"), e.form("val")
    owns, pays, claims = e.form("owns"), e.form("pays"), e.form("claims")
    first, second = fx.structure.elements("player")[:2]
    return Compiled(
        (
            Total("moves_given", ((player, ("p",)),), ((owns, ("p", "m")),)),
            Closure("pays_owned", ((pays, ("a", "b", "u", "v")),), ((owns, (first, "a")), (owns, (second, "b")))),
            Closure("claims_owned", ((claims, ("a", "b", "u", "v")),),
                    ((owns, (first, "a")), (owns, (second, "b")))),
            Total("table_complete", ((owns, (first, "a")), (owns, (second, "b"))), ((pays, ("a", "b", "u", "v")),)),
            Functional("one_payoff", pays, 2),
            Closure("typed", ((pays, ("a", "b", "u", "v")),), ((move, ("a",)), (move, ("b",)), (val, ("u",)), (val, ("v",)))),
        ),
        decoded=(DecodedClause("claims_match", claims_match, EXACT),),
    )


LEAN_DEFS = (
    "/-- A joint move (by positions) and the two payoffs. -/",
    "abbrev Row := Prod (Prod Nat Nat) (Prod QN QN)",
    "",
    "/-- Each claim's payoffs are the table's at its joint move. -/",
    "def claimsMatch (table claims : List Row) : Bool :=",
    "  claims.all fun c => table.any fun t => decide (t.1 = c.1) && decide (t.2 = c.2)",
    "",
)
LEAN_CALLS = {"claims_match": "claimsMatch table_{f} claims_{f}"}


def _rows_text(rs: list[Row]) -> str:
    return lean_list([f"(({i}, {j}), ({lean_q(x)}, {lean_q(y)}))" for (i, j), (x, y) in rs])


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    table, claims = table_rows(fs, "pays"), table_rows(fs, "claims")
    assert table is not None and claims is not None
    return [("table", "List Row", _rows_text(table)), ("claims", "List Row", _rows_text(claims))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clause of `joint_payoffs`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
