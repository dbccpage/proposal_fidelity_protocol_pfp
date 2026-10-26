# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Challenges against a pinned check: the base fixture passes the check,
every challenge's mutant differs from the base, running the check on the
mutant changes its verdict to a refusal, and the recorded result is the
recomputed one.  The check is never the producer's own code: it is one of
three pinned here (non-decreasing, distinct, or a sum at most a bound).

The claim: lists (the first is the base, the rest are mutants, in declared
order), entries (each carrying a natural, placed by ``of(e, l)``; a list's
order is the declared order of its entries), one subject (carrying the
check's number: 0 non-decreasing, 1 distinct, 2 bounded sum) and at most
one bound (carrying the sum's bound); ``recorded_pass(l)`` and
``recorded_fail(l)``.

Relational clauses, carried by derivability over the hosted claim:
``entries_placed`` and ``one_list``.

Decoded clauses, decided outside the grammar: ``well_formed`` (one subject
among the three, a bound exactly for the bounded sum, one recorded result
per mutant), ``base_passes``, ``mutants_differ``, ``mutants_refused``
(running the check on each mutant refuses it: the refused case is a
negative fixture that still passes) and ``results_exact``.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..lists import entries, nat
from ..shared import rows

CHALLENGE_ID = "mutant_challenges"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "base_passes", "mutants_differ", "mutants_refused", "results_exact")


def subject(fs: FiniteStructure) -> Callable[[list[int]], bool] | None:
    subs, bounds = fs.elements("subject"), fs.elements("bound")
    if len(subs) != 1:
        return None
    kind = nat(fs, subs[0])
    if kind == 0 and not bounds:
        return lambda xs: all(a <= b for a, b in zip(xs, xs[1:]))
    if kind == 1 and not bounds:
        return lambda xs: len(set(xs)) == len(xs)
    if kind == 2 and len(bounds) == 1 and nat(fs, bounds[0]) >= 0:
        b = nat(fs, bounds[0])
        return lambda xs: sum(xs) <= b
    return None


def lists(fs: FiniteStructure) -> tuple[list[int], list[tuple[int, list[int]]]]:
    ls = fs.elements("list")
    base = entries(fs, ls[0]) if ls else []
    return base, [(m, entries(fs, m)) for m in ls[1:]]


def recorded(fs: FiniteStructure, m: int) -> str | None:
    got = [r for name, r in (("recorded_pass", "PASS"), ("recorded_fail", "FAIL")) for (x,) in rows(fs, name)
           if x == m]
    return got[0] if len(got) == 1 else None


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    base, muts = lists(fs)
    return (subject(fs) is not None and bool(muts) and all(recorded(fs, m) is not None for m, _ in muts)
            and -1 not in base and all(-1 not in xs for _, xs in muts))


def base_passes(fs: FiniteStructure, _o: Oracle) -> bool:
    s = subject(fs)
    return s is not None and s(lists(fs)[0])


def mutants_differ(fs: FiniteStructure, _o: Oracle) -> bool:
    base, muts = lists(fs)
    return all(xs != base for _, xs in muts)


def mutants_refused(fs: FiniteStructure, _o: Oracle) -> bool:
    s = subject(fs)
    return s is not None and all(not s(xs) for _, xs in lists(fs)[1])


def results_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    s = subject(fs)
    return s is not None and all(recorded(fs, m) == ("PASS" if s(xs) else "FAIL") for m, xs in lists(fs)[1])


def describe(fs: FiniteStructure) -> dict[str, object]:
    base, muts = lists(fs)
    return {"base": base, "mutants": [xs for _, xs in muts]}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    entry, of = e.form("entry"), e.form("of")
    return Compiled(
        (
            Total("entries_placed", ((entry, ("e",)),), ((of, ("e", "l")),)),
            Functional("one_list", of, 1),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("base_passes", base_passes), ("mutants_differ", mutants_differ),
            ("mutants_refused", mutants_refused), ("results_exact", results_exact))),
    )
