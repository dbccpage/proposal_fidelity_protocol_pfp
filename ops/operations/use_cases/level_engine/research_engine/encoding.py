# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Hosting a finite structure in the sealed grammar, and back.

* each element becomes a datum (``Supply`` then ``AdmitDatum``);
* each sort becomes a unary form, with one instance per element of the sort;
* each relation symbol of k sorts becomes a k-ary form; tuples are instances.

The history uses sealed events only and is certified by sealed ``replay``.
Sealed admission refuses ill-formed tuples (wrong arity, absent element):
that refusal is recorded as ``NON_ADMISSIBLE`` with the sealed message.

Decoding is defined only on the image.  A datum, form or instance that the
encoding did not create has no old meaning and is refused by name
(``NON_DESCENT_*``), never given a default.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .errors import NonAdmissible, NonDescent
from .exact.q import Q
from .sealed import (
    AdmitDatum,
    AdmitForm,
    AdmitInst,
    Event,
    Regime,
    Supply,
    admission_error_type,
    replay,
)
from .structure import FiniteStructure, RelSym


@dataclass(frozen=True)
class Encoding:
    structure: FiniteStructure
    history: tuple[Event, ...]
    regime: Regime
    form_of: tuple[tuple[str, int], ...]   # sort or symbol name -> form index

    def form(self, name: str) -> int:
        for nm, f in self.form_of:
            if nm == name:
                return f
        raise KeyError(name)

    def n_claim_forms(self) -> int:
        return len(self.form_of)


def token(fs: FiniteStructure, e: int) -> str:
    s, k = fs.sort_of(e)
    return f"{s}{k}"


def hosting_history(fs: FiniteStructure) -> tuple[tuple[Event, ...], tuple[tuple[str, int], ...]]:
    events: list[Event] = []
    for e in range(fs.n()):
        tok = token(fs, e)
        events.append(Supply(tok))
        events.append(AdmitDatum(tok))
    form_of: list[tuple[str, int]] = []
    for s, _ in fs.sorts:
        form_of.append((s, len(form_of)))
        events.append(AdmitForm(1))
    for r in fs.symbols:
        form_of.append((r.name, len(form_of)))
        events.append(AdmitForm(len(r.sorts)))
    fidx = dict(form_of)
    for s, _ in fs.sorts:
        for e in fs.elements(s):
            events.append(AdmitInst(fidx[s], (e,)))
    for name, args in sorted(fs.tuples):
        events.append(AdmitInst(fidx[name], tuple(args)))
    return tuple(events), tuple(form_of)


def encode(fs: FiniteStructure) -> Encoding:
    history, form_of = hosting_history(fs)
    refused = admission_error_type()
    try:
        regime = replay(history)
    except refused as err:
        raise NonAdmissible("NON_ADMISSIBLE", f"sealed admission refused: {err}") from err
    return Encoding(fs, history, regime, form_of)


def decode(e: Encoding) -> FiniteStructure:
    """The claim structure read back from the hosted regime."""
    return descend(e, e.regime)


def descend(e: Encoding, r: Regime) -> FiniteStructure:
    """Read ``r`` back as a claim structure, or refuse by name when ``r``
    contains anything outside the encoding's image."""
    fs = e.structure
    n = fs.n()
    nf = e.n_claim_forms()
    if r.n_data() > n:
        raise NonDescent("NON_DESCENT_DATUM", f"datum {n} is not an element of the claim")
    if len(r.forms) > nf:
        raise NonDescent("NON_DESCENT_FORM", f"form {nf} is not a claim form")
    if r.rules:
        raise NonDescent("NON_DESCENT_FORM", "a uniform rule has no claim meaning")
    names = dict((f, nm) for nm, f in e.form_of)
    sorts = {s for s, _ in fs.sorts}
    tuples: list[tuple[str, tuple[int, ...]]] = []
    members: dict[str, set[int]] = {s: set() for s in sorts}
    for f, args in r.insts:
        nm = names[f]
        if nm in sorts:
            members[nm].add(args[0])
        else:
            tuples.append((nm, args))
    for s in sorts:
        if members[s] != set(fs.elements(s)):
            raise NonDescent("NON_DESCENT_DATUM", f"sort {s} membership left the image")
    return FiniteStructure(fs.sorts, fs.symbols, tuple(sorted(tuples)), fs.values, fs.digests, fs.texts)


def value_of(e: Encoding, d: int) -> Q:
    v = e.structure.value(d) if 0 <= d < e.structure.n() else None
    if v is None:
        raise NonDescent("NON_DESCENT_VALUE", f"datum {d} carries no exact value")
    return v


@dataclass(frozen=True)
class DownCheck:
    old_image_cases: int
    non_descent_cases: int
    defaulted: int


Descender = Callable[[Encoding, Regime], FiniteStructure]


def certify_hosting(
    encodings: Iterable[Encoding],
    new_terms: Callable[[Encoding], Iterable[Regime]],
    descender: Descender = descend,
) -> DownCheck:
    """``d(u(x)) = x`` on every hosted fixture, and every new term refused.

    ``new_terms`` yields regimes extending an encoding with one term outside
    the image (a fresh datum, a witness form, a witness instance).  A new
    term that descends instead of being refused is counted as ``defaulted``.
    """
    old = nd = dflt = 0
    for e in encodings:
        if descender(e, e.regime) != e.structure.with_tuples(e.structure.tuples):
            raise NonDescent("RR-NON-DESCENT", "decode(encode(x)) != x")
        old += 1
        for r in new_terms(e):
            try:
                descender(e, r)
            except NonDescent:
                nd += 1
            else:
                dflt += 1
    return DownCheck(old, nd, dflt)


def symbols_of(fs: FiniteStructure) -> tuple[RelSym, ...]:
    return fs.symbols
