# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Two independent implementations of rounding a rational to an integer,
pinned here (half up; half to even), run on the same canonical inputs: the
claimed outputs are what each implementation returns, a case whose outputs
differ is recorded as a disagreement and never merged, and every agreeing
case is merged exactly once with its output.

The claim: implementations (each carrying its pinned number: 0 half up, 1
half to even), cases (each carrying its input, an exact rational) and
integers (each carrying an integer value); ``side_a(i)`` and ``side_b(i)``
(which implementation stands on each side), ``out_a(c, n)``, ``out_b(c,
n)``, ``merged(c, n)`` and ``disagrees(c)``.

Relational clauses, carried by derivability over the hosted claim:
``independent`` (the two sides are different implementations),
``sides_given``, ``one_side_a``, ``one_side_b``, ``outputs_given``,
``one_out_a``, ``one_out_b`` and ``one_merge``.

Decoded clauses, decided outside the grammar: ``well_formed`` (pinned
numbers, integer outputs), ``outputs_exact`` (each claimed output is what
its implementation returns), ``no_silent_merge`` (no case whose outputs
differ is merged: the refused case) and ``disagreements_recorded`` (the
disagreements are exactly the differing cases, and every agreeing case is
merged with its output).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import Q
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Forbid, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import rows

CHALLENGE_ID = "differential_pairs"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "outputs_exact", "no_silent_merge", "disagreements_recorded")


def half_up(x: Q) -> int:
    return (2 * x.num + x.den) // (2 * x.den)


def half_even(x: Q) -> int:
    whole = x.num // x.den
    rest = x - Q(whole)
    if rest > Q(1, 2) or (rest == Q(1, 2) and whole % 2 == 1):
        return whole + 1
    return whole


IMPLS: tuple[Callable[[Q], int], ...] = (half_up, half_even)


def _int(fs: FiniteStructure, e: int) -> int | None:
    v = fs.value(e)
    return v.num if v is not None and v.den == 1 else None


def impl(fs: FiniteStructure, relation: str) -> Callable[[Q], int] | None:
    got = [i for (i,) in rows(fs, relation)]
    k = _int(fs, got[0]) if len(got) == 1 else None
    return IMPLS[k] if k is not None and 0 <= k < len(IMPLS) else None


def runs(fs: FiniteStructure) -> list[tuple[int, int, int, int | None, int | None]] | None:
    """(case, recomputed a, recomputed b, claimed a, claimed b) per case."""
    fa, fb = impl(fs, "side_a"), impl(fs, "side_b")
    if fa is None or fb is None:
        return None
    oa = {c: _int(fs, n) for c, n in rows(fs, "out_a")}
    ob = {c: _int(fs, n) for c, n in rows(fs, "out_b")}
    out = []
    for c in fs.elements("case"):
        x = fs.value(c)
        if x is None:
            return None
        out.append((c, fa(x), fb(x), oa.get(c), ob.get(c)))
    return out


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    return runs(fs) is not None and all(_int(fs, n) is not None for n in fs.elements("integer"))


def outputs_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    got = runs(fs)
    return got is not None and all((a, b) == (ca, cb) for _, a, b, ca, cb in got)


def no_silent_merge(fs: FiniteStructure, _o: Oracle) -> bool:
    got = runs(fs)
    merged = {c for c, _ in rows(fs, "merged")}
    return got is not None and not any(c in merged for c, a, b, _, _ in got if a != b)


def disagreements_recorded(fs: FiniteStructure, _o: Oracle) -> bool:
    got = runs(fs)
    if got is None:
        return False
    merged = {c: _int(fs, n) for c, n in rows(fs, "merged")}
    recorded = {c for (c,) in rows(fs, "disagrees")}
    return recorded == {c for c, a, b, _, _ in got if a != b} and merged == {c: a for c, a, b, _, _ in got if a == b}


def describe(fs: FiniteStructure) -> dict[str, object]:
    got = runs(fs)
    return {"runs": None if got is None else [[a, b] for _, a, b, _, _ in got]}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    case = e.form("case")
    sa, sb, oa, ob, merged = e.form("side_a"), e.form("side_b"), e.form("out_a"), e.form("out_b"), e.form("merged")
    return Compiled(
        (
            Forbid("independent", ((sa, ("i",)), (sb, ("i",)))),
            Total("sides_given", (), ((sa, ("i",)), (sb, ("j",)))),
            Functional("one_side_a", sa, 0),
            Functional("one_side_b", sb, 0),
            Total("outputs_given", ((case, ("c",)),), ((oa, ("c", "x")), (ob, ("c", "y")))),
            Functional("one_out_a", oa, 1),
            Functional("one_out_b", ob, 1),
            Functional("one_merge", merged, 1),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("outputs_exact", outputs_exact), ("no_silent_merge", no_silent_merge),
            ("disagreements_recorded", disagreements_recorded))),
    )
