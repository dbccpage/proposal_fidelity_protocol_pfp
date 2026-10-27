# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A release manifest: every claim in scope is covered, either linked to a
declared test or held as a typed unresolved obligation; the obligation
types are closed; every link resolves; the declared frontier is exactly
the claims with no test; and the release certifies nothing about itself.

The claim: claims, tests, obligation kinds and one release (each in
declared order), each kind carrying its place in the closed list (0 open,
1 conjecture, 2 blocked, 3 out of scope; any other value is untyped) as a
value; ``evidence(c, t)``, ``held(c, k)`` (claim ``c`` is held open as an
obligation of kind ``k``), ``frontier(c)``, ``self_certified(r)`` and
``grants_authority(r)``.

Relational clauses, carried by derivability over the hosted claim:
``not_self_certified`` and ``no_authority`` (the refused case: a release
that certifies itself or declares an authority effect),
``evidence_resolves``, ``held_in_scope``, ``frontier_in_scope`` and
``frontier_untested``.

Decoded clauses, decided outside the grammar: ``covered`` (every claim has
a test or an obligation), ``types_closed`` (every obligation's kind is one
of the four) and ``frontier_complete`` (every claim with no test is on the
frontier).  Whether a named test tests its claim is not decided.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.kinds import Closure, Forbid, Oracle
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import rows

CHALLENGE_ID = "scoped_release"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q",)
CLAUSES = ("covered", "types_closed", "frontier_complete")
KINDS = 4


def tested(fs: FiniteStructure) -> set[int]:
    return {c for c, _ in rows(fs, "evidence")}


def covered(fs: FiniteStructure, _o: Oracle) -> bool:
    held = {c for c, _ in rows(fs, "held")}
    return all(c in tested(fs) or c in held for c in fs.elements("claim"))


def types_closed(fs: FiniteStructure, _o: Oracle) -> bool:
    def ok(k: int) -> bool:
        v = fs.value(k)
        return v is not None and v.den == 1 and 0 <= v.num < KINDS

    return all(ok(k) for _, k in rows(fs, "held"))


def frontier_complete(fs: FiniteStructure, _o: Oracle) -> bool:
    front = {c for (c,) in rows(fs, "frontier")}
    return {c for c in fs.elements("claim") if c not in tested(fs)} <= front


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"frontier": sorted(c for c in fs.elements("claim") if c not in tested(fs))}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    claim, test = e.form("claim"), e.form("test")
    evidence, held, frontier = e.form("evidence"), e.form("held"), e.form("frontier")
    selfc, auth = e.form("self_certified"), e.form("grants_authority")
    return Compiled(
        (
            Forbid("not_self_certified", ((selfc, ("r",)),)),
            Forbid("no_authority", ((auth, ("r",)),)),
            Closure("evidence_resolves", ((evidence, ("c", "t")),), ((claim, ("c",)), (test, ("t",)))),
            Closure("held_in_scope", ((held, ("c", "k")),), ((claim, ("c",)),)),
            Closure("frontier_in_scope", ((frontier, ("c",)),), ((claim, ("c",)),)),
            Forbid("frontier_untested", ((frontier, ("c",)), (evidence, ("c", "t")))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("covered", covered), ("types_closed", types_closed), ("frontier_complete", frontier_complete))),
    )
