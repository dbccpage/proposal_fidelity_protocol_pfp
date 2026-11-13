"""Frozen harness types for the proposal-evaluation-authorization fold.

AuthorityEffect: None.

Proposal is Supply-shaped: recording it changes no admitted state.
EvalResult carries raw minima, retained iso classes, and mu1/mu2 costs.
It is never Tie, UniqueClass, UniqueDelta, or None.  License is not an
Event, has no revoke API, and does not select among tied classes by an
integer index.  Node carries history, regime, and an optional license.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, cast

from derivation.candidates import Delta
from derivation.iso import CanonKey
from derivation.model import (
    AdmitDatum,
    AdmitForm,
    AdmitInst,
    AdmitRuleAll,
    Event,
    Impose,
    Regime,
    Supply,
)

SEALED_EVENT_TYPES: tuple[type[object], ...] = (
    Supply,
    AdmitDatum,
    AdmitForm,
    AdmitInst,
    AdmitRuleAll,
    Impose,
)


class HarnessError(ValueError):
    """Named refusal from this harness."""


class LicenseSelectorError(HarnessError):
    """An integer index is not a selector among tied classes."""


class LicenseIsNotEventError(HarnessError):
    """A License is not one of the six sealed Event constructors."""


class PresentAsAdmitError(HarnessError):
    """A Proposal is not an admission."""


class SeventhEventError(HarnessError):
    """A constructor outside the six sealed Event kinds is refused."""


class GradeIsNotLicenseError(HarnessError):
    """A partial-Decide grade stamp is not a License."""


class UniqueDeltaAutoApplyError(HarnessError):
    """A unique minimum remains a proposal."""


class EvaluationPersistedEventError(HarnessError):
    """Evaluation does not persist Events onto the declared base."""


class LeftoverIsNotDemandError(HarnessError):
    """Collapsed pairs after a licensed apply are observations."""


@dataclass(frozen=True)
class Proposal:
    """Supply-shaped offering.  Recording it changes no admitted state."""

    token: str
    offerings: tuple[Delta, ...] = ()


@dataclass(frozen=True)
class RetainedClass:
    """One inhabited iso class of minimum responses."""

    key: CanonKey
    members: tuple[Delta, ...]

    def __post_init__(self) -> None:
        if not self.members:
            raise ValueError("a retained class must be inhabited")
        if len(set(self.members)) != len(self.members):
            raise ValueError("a retained class cannot duplicate a member")


@dataclass(frozen=True)
class EvalResult:
    """Evaluation payload.  Never a grade, never a license, never None."""

    measure: str
    cost: tuple[int, int] | None
    raw_minima: tuple[Delta, ...]
    retained: tuple[RetainedClass, ...]
    found: bool
    max_items: int
    max_arity: int

    def __post_init__(self) -> None:
        if self.measure not in ("mu1", "mu2"):
            raise ValueError(f"unknown measure: {self.measure}")
        if self.max_items < 0 or self.max_arity < 0:
            raise ValueError("bounds cannot be negative")
        if self.found and not self.retained:
            raise ValueError("a found evaluation must retain at least one class")
        if self.found and self.cost is None:
            raise ValueError("a found evaluation must record a cost")
        if not self.found and self.retained:
            raise ValueError("an unfound evaluation cannot retain classes")
        keys = tuple(item.key for item in self.retained)
        if keys != tuple(sorted(keys)):
            raise ValueError("retained classes must be sorted by sealed key")
        if len(set(keys)) != len(keys):
            raise ValueError("retained classes must have distinct keys")


@dataclass(frozen=True)
class License:
    """Metatheoretic authorization record.  Not an Event.

    ``authorized`` is a subset of retained iso-class keys.  There is no
    integer-index selector field and no revoke API.
    """

    granter: str
    scope: str
    authorized: tuple[CanonKey, ...]

    def __post_init__(self) -> None:
        if len(set(self.authorized)) != len(self.authorized):
            raise ValueError("authorized keys must be distinct")
        if tuple(sorted(self.authorized)) != self.authorized:
            raise ValueError("authorized keys must be in sealed-key order")


@dataclass(frozen=True)
class Node:
    """A regime together with the history that replays to it."""

    history: tuple[Event, ...]
    regime: Regime
    license: License | None = None


def jsonable(value: object) -> object:
    """Nested lists/ints for timestamp-free JSON."""
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value
    raise TypeError(f"not JSON-safe: {type(value)!r}")


def present(regime: Regime, proposal: Proposal) -> Regime:
    """Supply-shaped: the regime is unchanged."""
    del proposal
    return regime


def as_admit(proposal: Proposal) -> AdmitDatum:
    """Refused: present-as-admit is not a sealed transition."""
    raise PresentAsAdmitError(
        f"proposal {proposal.token!r} is not an admission"
    )


def as_event(license: License) -> Event:
    """Refused: a License is not an Event."""
    raise LicenseIsNotEventError(
        f"license granter {license.granter!r} is not an Event"
    )


def make_license(
    *,
    granter: str,
    scope: str,
    authorized: tuple[CanonKey, ...],
    **rejected: object,
) -> License:
    """Build a License.  Extra fields, including an integer index, are refused."""
    if rejected:
        raise LicenseSelectorError(
            "unknown license field: " + ", ".join(sorted(str(name) for name in rejected))
        )
    return License(granter=granter, scope=scope, authorized=authorized)


def key_by_index(retained: Sequence[CanonKey], index: int) -> CanonKey:
    """Refused: an integer index is not a tied-class selector."""
    del retained, index
    raise LicenseSelectorError(
        "an integer index is not a tied-class selector"
    )


def license_from_grade(stamp: object) -> License:
    """Refused: a grade stamp is not a License."""
    del stamp
    raise GradeIsNotLicenseError(
        "a partial-Decide grade stamp is not a License"
    )


def apply_unique_delta(node: Node, result: EvalResult) -> Node:
    """Refused: uniqueness is not authorization."""
    del node, result
    raise UniqueDeltaAutoApplyError("a unique minimum remains a proposal")


def leftover_as_demand(pairs: tuple[tuple[int, int], ...]) -> None:
    """Refused: leftover collapsed pairs are not a next demand."""
    del pairs
    raise LeftoverIsNotDemandError(
        "leftover collapsed pairs are observations, not a next demand"
    )


def append_sealed_event(
    history: tuple[Event, ...], event: object
) -> tuple[Event, ...]:
    """Append one of the six sealed Event kinds; refuse any extra."""
    if type(event) not in SEALED_EVENT_TYPES:
        raise SeventhEventError(
            f"refused constructor {type(event).__name__}"
        )
    return history + (cast(Event, event),)
