# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A reported failure of a pinned property on generated input, replayable
from its seed and shrunk without changing the failure: the pinned generator
(a 32-bit linear congruential sequence started at the seed; the first draw
modulo ``L + 1`` is the length, each further draw modulo ``V + 1`` an
entry) regenerates the failing input, the property fails on it, every
shrink step removes one entry or lowers one by one and still fails, and no
single shrink step from the last list still fails.

The claim: bounds (the length bound, then the value bound), at most one
seed, a property (its kind, 0 "the sum is below k" or 1 "k does not
occur", then its ``k``), lists (the failing input, then the shrink trace in
order) and entries placed by ``of(e, l)``; every element carries a natural.

Relational clauses, carried by derivability over the hosted claim:
``entries_placed`` and ``one_list``.

Decoded clauses, decided outside the grammar: ``well_formed`` (bounds, the
property's kind and ``k``, naturals throughout, ``L <= 32``,
``V <= 1000``), ``seeded`` (the failure carries a seed: the refused case is
a failure with none, quarantined rather than accepted), ``replayed``,
``is_failure``, ``shrink_steps`` and ``shrunk``.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..lists import entries, nat

CHALLENGE_ID = "seeded_shrinks"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "seeded", "replayed", "is_failure", "shrink_steps", "shrunk")


def generate(seed: int, max_len: int, max_value: int) -> list[int]:
    state = seed % 2 ** 32

    def draw() -> int:
        nonlocal state
        state = (1664525 * state + 1013904223) % 2 ** 32
        return state

    length = draw() % (max_len + 1)
    return [draw() % (max_value + 1) for _ in range(length)]


def prop(fs: FiniteStructure) -> tuple[int, int]:
    ps = [nat(fs, e) for e in fs.elements("property")]
    return (ps[0], ps[1]) if len(ps) == 2 else (-1, -1)


def fails(p: tuple[int, int], xs: list[int]) -> bool:
    kind, k = p
    return sum(xs) >= k if kind == 0 else k in xs


def shrinks(xs: list[int]) -> list[list[int]]:
    out = [xs[:i] + xs[i + 1:] for i in range(len(xs))]
    out += [xs[:i] + [xs[i] - 1] + xs[i + 1:] for i in range(len(xs)) if xs[i] > 0]
    return out


def lists(fs: FiniteStructure) -> list[list[int]]:
    return [entries(fs, lst) for lst in fs.elements("list")]


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    b = [nat(fs, e) for e in fs.elements("bound")]
    kind, k = prop(fs)
    return (len(b) == 2 and 0 <= b[0] <= 32 and 0 <= b[1] <= 1000 and kind in (0, 1) and k >= 0
            and bool(lists(fs)) and all(-1 not in xs for xs in lists(fs)))


def seeded(fs: FiniteStructure, _o: Oracle) -> bool:
    return len(fs.elements("seed")) == 1 and nat(fs, fs.elements("seed")[0]) >= 0


def replayed(fs: FiniteStructure, _o: Oracle) -> bool:
    b = [nat(fs, e) for e in fs.elements("bound")]
    ls = lists(fs)
    return seeded(fs, _o) and len(b) == 2 and bool(ls) and generate(nat(fs, fs.elements("seed")[0]), b[0], b[1]) == ls[0]


def is_failure(fs: FiniteStructure, _o: Oracle) -> bool:
    ls = lists(fs)
    return bool(ls) and fails(prop(fs), ls[0])


def shrink_steps(fs: FiniteStructure, _o: Oracle) -> bool:
    ls = lists(fs)
    return all(b in shrinks(a) and fails(prop(fs), b) for a, b in zip(ls, ls[1:]))


def shrunk(fs: FiniteStructure, _o: Oracle) -> bool:
    ls = lists(fs)
    return bool(ls) and not any(fails(prop(fs), s) for s in shrinks(ls[-1]))


def describe(fs: FiniteStructure) -> dict[str, object]:
    b = [nat(fs, e) for e in fs.elements("bound")]
    seeds = fs.elements("seed")
    return {"generated": generate(nat(fs, seeds[0]), b[0], b[1]) if seeds and len(b) == 2 else None}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    entry, of = e.form("entry"), e.form("of")
    return Compiled(
        (
            Total("entries_placed", ((entry, ("e",)),), ((of, ("e", "l")),)),
            Functional("one_list", of, 1),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("seeded", seeded), ("replayed", replayed), ("is_failure", is_failure),
            ("shrink_steps", shrink_steps), ("shrunk", shrunk))),
    )
