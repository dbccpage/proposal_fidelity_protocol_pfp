"""Admitted regimes, admission events, and replay.

Classification (assumption discipline):

* ``Regime`` and ``Event`` are metatheory apparatus.
* A regime's ``data`` entries record *presentation tokens*.  Presentation
  identity (token equality) is visible only to the metatheory; the object
  language never gains access to it unless an admitted judgment supplies an
  internal distinction.
* ``Supply`` is an external presentation event and provably does not change
  the admitted state (see ``step``).
* State changes happen only through explicit admission events
  (``AdmitDatum``, ``AdmitForm``, ``AdmitInst``, ``AdmitRuleAll``) or an
  externally imposed requirement (``Impose``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Union

Args = tuple[int, ...]
Inst = tuple[int, Args]
Pair = tuple[int, int]


class AdmissionError(ValueError):
    """An event is ill-formed relative to the current regime."""


@dataclass(frozen=True)
class Regime:
    """Admitted state.

    ``data``:  admitted data in admission order (entries are presentation
               tokens; internal identity is the index).
    ``forms``: admitted judgment forms; entry ``a`` at index ``f`` means form
               ``f`` has arity ``a >= 1``.
    ``insts``: admitted judgment instances ``(form, args)``.
    ``rules``: forms carrying the uniform all-tuples rule (every well-formed
               instance of the form counts as derivable).
    ``reqs``:  externally imposed persistent separation requirements
               ``(i, j)`` with ``i < j``.
    """

    data: tuple[str, ...]
    forms: tuple[int, ...]
    insts: frozenset[Inst]
    rules: frozenset[int]
    reqs: frozenset[Pair]

    def n_data(self) -> int:
        return len(self.data)


EMPTY = Regime((), (), frozenset(), frozenset(), frozenset())


@dataclass(frozen=True)
class Supply:
    """External presentation of a token.  Not an admission."""

    token: str


@dataclass(frozen=True)
class AdmitDatum:
    """Admission of a presented token as a datum.

    Re-admission of an already admitted token is a designation of the
    existing datum, not a duplication (declared metatheoretic convention:
    presentation identity dedups admissions).
    """

    token: str


@dataclass(frozen=True)
class AdmitForm:
    arity: int


@dataclass(frozen=True)
class AdmitInst:
    form: int
    args: Args


@dataclass(frozen=True)
class AdmitRuleAll:
    form: int


@dataclass(frozen=True)
class Impose:
    """External requirement: data ``i`` and ``j`` must be internally
    separable.  Requirements are persistent constraints."""

    i: int
    j: int


Event = Union[Supply, AdmitDatum, AdmitForm, AdmitInst, AdmitRuleAll, Impose]


def step(r: Regime, e: Event) -> Regime:
    """Apply one event.  Deterministic; raises ``AdmissionError`` on
    ill-formed admissions."""
    if isinstance(e, Supply):
        return r
    if isinstance(e, AdmitDatum):
        if e.token in r.data:
            return r
        return Regime(r.data + (e.token,), r.forms, r.insts, r.rules, r.reqs)
    if isinstance(e, AdmitForm):
        if e.arity < 1:
            raise AdmissionError(f"form arity must be >= 1, got {e.arity}")
        return Regime(r.data, r.forms + (e.arity,), r.insts, r.rules, r.reqs)
    if isinstance(e, AdmitInst):
        if not (0 <= e.form < len(r.forms)):
            raise AdmissionError(f"unknown form {e.form}")
        if len(e.args) != r.forms[e.form]:
            raise AdmissionError(
                f"form {e.form} has arity {r.forms[e.form]}, "
                f"got {len(e.args)} arguments"
            )
        if not all(0 <= a < len(r.data) for a in e.args):
            raise AdmissionError(f"instance arguments out of range: {e.args}")
        return Regime(
            r.data, r.forms, r.insts | {(e.form, e.args)}, r.rules, r.reqs
        )
    if isinstance(e, AdmitRuleAll):
        if not (0 <= e.form < len(r.forms)):
            raise AdmissionError(f"unknown form {e.form}")
        return Regime(r.data, r.forms, r.insts, r.rules | {e.form}, r.reqs)
    # Impose
    if not (0 <= e.i < e.j < len(r.data)):
        raise AdmissionError(f"requirement out of range: ({e.i}, {e.j})")
    return Regime(r.data, r.forms, r.insts, r.rules, r.reqs | {(e.i, e.j)})


def replay(history: Sequence[Event], base: Regime = EMPTY) -> Regime:
    """Replay a history from ``base`` (genesis by default).

    This is the replay rule: every certified regime must equal the replay of
    its recorded history."""
    r = base
    for e in history:
        r = step(r, e)
    return r


def certify(history: Sequence[Event], claimed: Regime) -> bool:
    """Check a claimed regime against its recorded history."""
    return replay(history) == claimed
