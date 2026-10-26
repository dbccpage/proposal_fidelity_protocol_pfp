"""Internal observation: contexts, profiles, observational equivalence.

Classification: metatheory apparatus computing object-language facts.

A *context* is a judgment form together with a slot tuple in which at least
one slot is a hole (``None``); the remaining slots name admitted data.
Plugging datum ``d`` into a context fills every hole with ``d``.

The *profile* of a datum is the set of contexts whose plugging is derivable.
With no admitted inference rules other than the uniform all-tuples rule,
derivability is: membership in the admitted instances, or coverage by a
uniform rule.

Two data are *observationally collapsed* when their profiles are equal, and
*internally separable* (declared sense: behavioral separation by positive
derivability) when their profiles differ.
"""

from __future__ import annotations

from itertools import product
from typing import Iterator, Optional

from .model import Inst, Pair, Regime

Slot = Optional[int]
Context = tuple[int, tuple[Slot, ...]]


def slot_tuples(arity: int, n_data: int) -> Iterator[tuple[Slot, ...]]:
    """All slot tuples of the given arity over ``n_data`` data, in a fixed
    deterministic order (hole first, then data by index)."""
    options: list[Slot] = [None] + list(range(n_data))
    yield from product(options, repeat=arity)


def contexts(r: Regime) -> tuple[Context, ...]:
    """All contexts of the regime, deterministically ordered."""
    out: list[Context] = []
    for f, arity in enumerate(r.forms):
        for slots in slot_tuples(arity, r.n_data()):
            if any(s is None for s in slots):
                out.append((f, slots))
    return tuple(out)


def plug(c: Context, d: int) -> Inst:
    f, slots = c
    return (f, tuple(d if s is None else s for s in slots))


def derivable(r: Regime, inst: Inst) -> bool:
    return inst[0] in r.rules or inst in r.insts


def profile(r: Regime, d: int) -> frozenset[Context]:
    return frozenset(c for c in contexts(r) if derivable(r, plug(c, d)))


def profiles(r: Regime) -> tuple[frozenset[Context], ...]:
    ctxs = contexts(r)
    return tuple(
        frozenset(c for c in ctxs if derivable(r, plug(c, d)))
        for d in range(r.n_data())
    )


def separable(r: Regime, i: int, j: int) -> bool:
    return profile(r, i) != profile(r, j)


def witness(r: Regime, i: int, j: int) -> Optional[Context]:
    """First context (deterministic order) distinguishing ``i`` from ``j``,
    or ``None`` if the pair is collapsed."""
    for c in contexts(r):
        if derivable(r, plug(c, i)) != derivable(r, plug(c, j)):
            return c
    return None


def collapsed_pairs(r: Regime) -> tuple[Pair, ...]:
    """All pairs ``i < j`` with equal profiles, lexicographically ordered.

    These are exactly the unresolved separation demands of the regime: an
    accepted regime satisfies all imposed requirements, so no collapsed pair
    is already required."""
    profs = profiles(r)
    n = r.n_data()
    return tuple(
        (i, j)
        for i in range(n)
        for j in range(i + 1, n)
        if profs[i] == profs[j]
    )


def satisfies(r: Regime) -> bool:
    """All imposed separation requirements hold."""
    profs = profiles(r)
    return all(profs[i] != profs[j] for (i, j) in sorted(r.reqs))
