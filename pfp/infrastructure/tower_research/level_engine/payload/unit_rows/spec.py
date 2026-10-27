# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A row of exact pairs in a declared frame, claimed to have size one.

The claim: slots (the declared frame, in order), values, and
``entry(s, a, b)`` (the row's entry at slot ``s`` is the pair ``a + b i``).

Relational clauses, carried by derivability over the hosted claim:
``entries_given`` (every slot of the frame has an entry), ``one_entry`` and
``typed``.

Decoded clause, decided over exact values outside the grammar:
``unit_size`` (the size of the row, the sum over its entries of
``a * a + b * b``, is exactly one).  A sum of squares taken without the
mirror, ``a + b i`` times itself, is not a size: the row ``(1, i)`` would
have size zero under it and has size two.  Its Lean certificates are
re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.exact.q import ONE, ZERO, fmt_q
from operations.use_cases.level_engine.research_engine.exact.qi import QI
from operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import PAIR_DEFS, certificates, lean_list, lean_pair, pair_of, render, rows

CHALLENGE_ID = "unit_rows"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "UnitRows"
EXACT = ("py.exact.q", "py.exact.qi")
CLAUSES = ("unit_size",)


def row(fs: FiniteStructure) -> list[QI] | None:
    """The entries in the declared order of slots; ``None`` when one is
    missing, repeated or undecodable."""
    got: dict[int, QI] = {}
    for s, a, b in rows(fs, "entry"):
        z = pair_of(fs, a, b)
        if z is None or s in got:
            return None
        got[s] = z
    slots = fs.elements("slot")
    return [got[s] for s in slots] if all(s in got for s in slots) else None


def unit_size(fs: FiniteStructure, _o: Oracle) -> bool:
    r = row(fs)
    return r is not None and sum((z.norm2() for z in r), ZERO) == ONE


def describe(fs: FiniteStructure) -> dict[str, object]:
    r = row(fs)
    return {"size": None if r is None else fmt_q(sum((z.norm2() for z in r), ZERO))}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "unit_size")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    slot, val, entry = e.form("slot"), e.form("val"), e.form("entry")
    return Compiled(
        (
            Total("entries_given", ((slot, ("s",)),), ((entry, ("s", "a", "b")),)),
            Functional("one_entry", entry, 1),
            Closure("typed", ((entry, ("s", "a", "b")),), ((slot, ("s",)), (val, ("a",)), (val, ("b",)))),
        ),
        decoded=(DecodedClause("unit_size", unit_size, EXACT),),
    )


LEAN_DEFS = PAIR_DEFS + (
    "/-- The row has size exactly one. -/",
    "def unitSize (r : List Pair) : Bool := decide (rowSize r = 1)",
    "",
)
LEAN_CALLS = {"unit_size": "unitSize row_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    r = row(fs)
    assert r is not None
    return [("row", "List Pair", lean_list([lean_pair(z) for z in r]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clause of `unit_rows`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
