# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Trials over a sealed corpus, and an interval recomputed from counts: the
corpus still hashes to its seal, every trial draws a corpus item and no item
twice, the stated successes, trial count and point are the recounted ones,
and the interval is the declared exact interval for a proportion at the
stated level.

A corpus item is named ``c<k>`` by its place; the corpus's content is the
canonical JSON list ``[[name, text], ...]`` in declared order, and its seal
is the SHA-256 of that text: a declared convention.  The interval is
``[max(0, p - h), min(1, p + h)]`` for the point ``p = k/n`` and the half
width ``h``, and it holds at level ``1 - a`` exactly when
``1 <= a * 4 * n * h * h`` (the second-moment bound for a proportion, whose
variance is at most ``1/(4n)``).  Every quantity is an exact rational.

The claim: items (each carrying its content as a text), one seal (carrying
a digest, an exact 32-byte value), trials, and one element each for the
successes, the trial count, the point, the half width, the alpha and the
two ends of the interval (each carrying its value); ``draws(t, i)``,
``succeeded(t)`` and ``failed(t)``.

Relational clauses, carried by derivability over the hosted claim:
``count_given`` (the refused case: a point estimate with no trial count),
``draw_given``, ``one_draw``, ``draws_items`` and ``one_result``.

Decoded clauses, decided outside the grammar: ``well_formed``,
``corpus_sealed``, ``draws_distinct``, ``counts_exact`` and
``interval_exact``.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.exact.digest import digest_of
from operations.use_cases.level_engine.research_engine.exact.q import ONE, ZERO, Q
from operations.use_cases.level_engine.research_engine.kinds import Closure, Forbid, Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..lists import nat
from ..shared import rows

CHALLENGE_ID = "counted_trials"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q", "py.exact.digest")
CLAUSES = ("well_formed", "corpus_sealed", "draws_distinct", "counts_exact", "interval_exact")
FIGURES = ("successes", "count", "point", "half_width", "alpha", "low", "high")


def figure(fs: FiniteStructure, name: str) -> Q | None:
    els = fs.elements(name)
    return fs.value(els[0]) if len(els) == 1 else None


def corpus(fs: FiniteStructure) -> list[list[str]] | None:
    got = [(f"c{k}", fs.text(i)) for k, i in enumerate(fs.elements("item"))]
    return None if any(t is None or t == "" for _, t in got) else [[n, str(t)] for n, t in got]


def drawn(fs: FiniteStructure) -> list[int]:
    return [i for t in fs.elements("trial") for tt, i in rows(fs, "draws") if tt == t]


def tally(fs: FiniteStructure) -> tuple[int, int]:
    """The recount: (successes, trials)."""
    wins = {t for (t,) in rows(fs, "succeeded")}
    trials = fs.elements("trial")
    return sum(1 for t in trials if t in wins), len(trials)


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    wins, losses = {t for (t,) in rows(fs, "succeeded")}, {t for (t,) in rows(fs, "failed")}
    half, alpha = figure(fs, "half_width"), figure(fs, "alpha")
    seals = fs.elements("seal")
    return (corpus(fs) is not None and len(seals) == 1 and fs.digest(seals[0]) is not None
            and all((t in wins) != (t in losses) for t in fs.elements("trial"))
            and all(figure(fs, f) is not None for f in FIGURES)
            and all(nat(fs, fs.elements(f)[0]) >= 0 for f in ("successes", "count"))
            and half is not None and half > ZERO and alpha is not None and ZERO < alpha < ONE)


def corpus_sealed(fs: FiniteStructure, _o: Oracle) -> bool:
    c, seals = corpus(fs), fs.elements("seal")
    return c is not None and len(seals) == 1 and fs.digest(seals[0]) == digest_of(c)


def draws_distinct(fs: FiniteStructure, _o: Oracle) -> bool:
    got = drawn(fs)
    return len(set(got)) == len(got)


def counts_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    k, n = tally(fs)
    return (n > 0 and figure(fs, "successes") == Q(k) and figure(fs, "count") == Q(n)
            and figure(fs, "point") == Q.of(k, n))


def interval_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    _, n = tally(fs)
    p, h, a = figure(fs, "point"), figure(fs, "half_width"), figure(fs, "alpha")
    lo, hi = figure(fs, "low"), figure(fs, "high")
    if p is None or h is None or a is None or lo is None or hi is None:
        return False
    return (lo == max(ZERO, p - h) and hi == min(ONE, p + h)
            and ONE <= a * Q(4) * Q(n) * h * h)


def describe(fs: FiniteStructure) -> dict[str, object]:
    k, n = tally(fs)
    c = corpus(fs)
    return {"successes": k, "trials": n, "seal": None if c is None else "sha256:" + digest_of(c).hex()}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    item, trial, point, count = e.form("item"), e.form("trial"), e.form("point"), e.form("count")
    draws, succeeded, failed = e.form("draws"), e.form("succeeded"), e.form("failed")
    return Compiled(
        (
            Total("count_given", ((point, ("p",)),), ((count, ("n",)),)),
            Total("draw_given", ((trial, ("t",)),), ((draws, ("t", "i")),)),
            Functional("one_draw", draws, 1),
            Closure("draws_items", ((draws, ("t", "i")),), ((item, ("i",)),)),
            Forbid("one_result", ((succeeded, ("t",)), (failed, ("t",)))),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("corpus_sealed", corpus_sealed), ("draws_distinct", draws_distinct),
            ("counts_exact", counts_exact), ("interval_exact", interval_exact))),
    )
