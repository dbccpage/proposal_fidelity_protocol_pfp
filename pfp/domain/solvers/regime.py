"""Admitted regimes, admission events, observation, and replay.

Classification: Domain Solvers State Model.
Governing Invariant: Value Object Exact-Type Equality Invariant (RULE_VALUE_OBJECT_EXACT_TYPE_EQUALITY_001).
AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from itertools import permutations, product
from typing import Optional, Union

from .errors import NonAdmissible, SolverRefusal

Args = tuple[int, ...]
Inst = tuple[int, Args]
Pair = tuple[int, int]


class AdmissionError(SolverRefusal):
    """An event is ill-formed relative to the current regime."""


@dataclass(frozen=True)
class Regime:
    """Admitted state Value Object.

    data: admitted presentation tokens.
    forms: admitted judgment forms; entry a at index f means form f has arity a >= 1.
    insts: admitted judgment instances (form, args).
    rules: forms carrying the uniform all-tuples rule.
    reqs: persistent separation requirements (i, j) with i < j.
    """

    data: tuple[str, ...]
    forms: tuple[int, ...]
    insts: frozenset[Inst]
    rules: frozenset[int]
    reqs: frozenset[Pair]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.data == other.data
            and self.forms == other.forms
            and self.insts == other.insts
            and self.rules == other.rules
            and self.reqs == other.reqs
        )

    def n_data(self) -> int:
        return len(self.data)


EMPTY = Regime((), (), frozenset(), frozenset(), frozenset())


@dataclass(frozen=True)
class AdmitDatum:
    token: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.token == other.token


@dataclass(frozen=True)
class AdmitForm:
    arity: int

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.arity == other.arity


@dataclass(frozen=True)
class AdmitInst:
    form: int
    args: tuple[int, ...]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.form == other.form and self.args == other.args


@dataclass(frozen=True)
class AdmitRuleAll:
    form: int

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.form == other.form


@dataclass(frozen=True)
class Impose:
    i: int
    j: int

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.i == other.i and self.j == other.j


@dataclass(frozen=True)
class Supply:
    token: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.token == other.token


Event = Union[AdmitDatum, AdmitForm, AdmitInst, AdmitRuleAll, Impose, Supply]


def step(r: Regime, event: Event) -> Regime:
    """State transition under an event."""
    if isinstance(event, Supply):
        return r
    if isinstance(event, AdmitDatum):
        return Regime(r.data + (event.token,), r.forms, r.insts, r.rules, r.reqs)
    if isinstance(event, AdmitForm):
        if event.arity < 1:
            raise AdmissionError("ZERO_ARITY", "form arity must be positive")
        return Regime(r.data, r.forms + (event.arity,), r.insts, r.rules, r.reqs)
    if isinstance(event, AdmitInst):
        if event.form >= len(r.forms):
            raise AdmissionError("UNKNOWN_FORM", f"unknown form {event.form}")
        if len(event.args) != r.forms[event.form]:
            raise AdmissionError("WRONG_ARITY", "argument length does not match arity")
        for a in event.args:
            if not 0 <= a < r.n_data():
                raise AdmissionError("UNKNOWN_DATUM", f"unknown datum {a}")
        inst: Inst = (event.form, tuple(event.args))
        return Regime(r.data, r.forms, r.insts | {inst}, r.rules, r.reqs)
    if isinstance(event, AdmitRuleAll):
        if event.form >= len(r.forms):
            raise AdmissionError("UNKNOWN_FORM", f"unknown form {event.form}")
        return Regime(r.data, r.forms, r.insts, r.rules | {event.form}, r.reqs)
    if isinstance(event, Impose):
        if not (0 <= event.i < r.n_data() and 0 <= event.j < r.n_data()):
            raise AdmissionError("UNKNOWN_DATUM", "datum out of range in requirement")
        if event.i == event.j:
            raise AdmissionError("REFLEXIVE_REQ", "cannot impose separation on equal data")
        pair: Pair = (min(event.i, event.j), max(event.i, event.j))
        return Regime(r.data, r.forms, r.insts, r.rules, r.reqs | {pair})
    raise TypeError(f"unknown event: {event!r}")


def replay(events: Sequence[Event], base: Regime = EMPTY) -> Regime:
    """Fold events from base (default EMPTY)."""
    r = base
    for ev in events:
        r = step(r, ev)
    return r


# ---------------------------------------------------------------------------
# Candidate deltas and item grammar
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NewDatum:
    def __eq__(self, other: object) -> bool:
        return type(self) is type(other)


@dataclass(frozen=True)
class NewForm:
    arity: int

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.arity == other.arity


@dataclass(frozen=True)
class NewInst:
    form: int
    args: Args

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.form == other.form and self.args == other.args


@dataclass(frozen=True)
class NewRuleAll:
    form: int

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.form == other.form


Item = Union[NewDatum, NewForm, NewInst, NewRuleAll]
Delta = tuple[Item, ...]


def item_key(it: Item) -> tuple[int, int, Args]:
    if isinstance(it, NewDatum):
        return (0, 0, ())
    if isinstance(it, NewForm):
        return (1, it.arity, ())
    if isinstance(it, NewRuleAll):
        return (2, it.form, ())
    return (3, it.form, it.args)


def canonical_delta(items: tuple[Item, ...] | Sequence[Item]) -> Delta:
    return tuple(sorted(items, key=item_key))


def mu1(delta: Delta) -> int:
    return len(delta)


def mu2(delta: Delta) -> tuple[int, int]:
    return (
        len(delta),
        sum(it.arity for it in delta if isinstance(it, NewForm)),
    )


def delta_events(base: Regime, delta: Delta) -> tuple[Event, ...]:
    events: list[Event] = []
    n = base.n_data()
    for it in delta:
        if isinstance(it, NewDatum):
            events.append(AdmitDatum(f"w{n}"))
            n += 1
        elif isinstance(it, NewForm):
            events.append(AdmitForm(it.arity))
        elif isinstance(it, NewRuleAll):
            events.append(AdmitRuleAll(it.form))
        else:
            events.append(AdmitInst(it.form, it.args))
    return tuple(events)


def apply_delta(base: Regime, delta: Delta) -> Regime:
    return replay(delta_events(base, delta), base)


# ---------------------------------------------------------------------------
# Internal observation
# ---------------------------------------------------------------------------

Slot = Optional[int]
Context = tuple[int, tuple[Slot, ...]]


def slot_tuples(arity: int, n_data: int) -> Iterator[tuple[Slot, ...]]:
    options: list[Slot] = [None] + list(range(n_data))
    yield from product(options, repeat=arity)


def contexts(r: Regime) -> tuple[Context, ...]:
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
    return tuple(profile(r, d) for d in range(r.n_data()))


def separable(r: Regime, i: int, j: int) -> bool:
    return profile(r, i) != profile(r, j)


# ---------------------------------------------------------------------------
# Isomorphism & Automorphism
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IsoWitness:
    pi: tuple[int, ...]
    phi: tuple[int, ...]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.pi == other.pi and self.phi == other.phi


def isomorphisms(a: Regime, b: Regime) -> Iterator[IsoWitness]:
    if a.n_data() != b.n_data() or len(a.forms) != len(b.forms) or sorted(a.forms) != sorted(b.forms):
        return
    n = a.n_data()
    m = len(a.forms)
    phi_candidates = [
        p for p in permutations(range(m))
        if all(a.forms[i] == b.forms[p[i]] for i in range(m))
    ]
    for phi in phi_candidates:
        if frozenset(phi[f] for f in a.rules) != b.rules:
            continue
        for pi in permutations(range(n)):
            mapped_insts = frozenset(
                (phi[f], tuple(pi[arg] for arg in args)) for f, args in a.insts
            )
            if mapped_insts != b.insts:
                continue
            mapped_reqs = frozenset(
                (min(pi[i], pi[j]), max(pi[i], pi[j])) for i, j in a.reqs
            )
            if mapped_reqs != b.reqs:
                continue
            yield IsoWitness(pi, phi)


def isomorphic(a: Regime, b: Regime) -> bool:
    return next(isomorphisms(a, b), None) is not None


__all__ = [
    "AdmissionError",
    "AdmitDatum",
    "AdmitForm",
    "AdmitInst",
    "AdmitRuleAll",
    "Context",
    "Delta",
    "EMPTY",
    "Event",
    "Impose",
    "Inst",
    "IsoWitness",
    "Item",
    "NewDatum",
    "NewForm",
    "NewInst",
    "NewRuleAll",
    "Pair",
    "Regime",
    "Slot",
    "Supply",
    "apply_delta",
    "canonical_delta",
    "contexts",
    "delta_events",
    "derivable",
    "isomorphic",
    "isomorphisms",
    "item_key",
    "mu1",
    "mu2",
    "plug",
    "profile",
    "profiles",
    "replay",
    "separable",
    "slot_tuples",
    "step",
]
