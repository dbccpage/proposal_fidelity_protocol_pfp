"""Write-ahead journal vocabulary for Adversary bouts.

A bout writes ``BOUT_STARTED`` before any model call, ``SEAT_TURN_STARTED``
before each seat turn and ``SEAT_TURN_COMPLETED`` after it, and exactly one
``BOUT_TERMINAL`` when it ends. A process that dies in between (a power cut)
leaves a started bout with no terminal record. ``unterminated_bouts`` finds
those, and the caller records them as ``CRASHED_UNKNOWN``: the bout stopped, the
cause is not known, and a seat turn that was started but never completed may
have cost money. Nothing here infers a cause.

Supports: a restart sees every bout that did not end through the code path that
writes ``BOUT_TERMINAL``. Does not support: any claim about why it stopped, or
about cost of an in-flight call; reconciliation assumes a single writer.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Protocol

from operations.domain.rop.result import Refusal, Result

from .native import NativeOperationPort
from .native import value as native_value

BOUT_STARTED = "BOUT_STARTED"
SEAT_TURN_STARTED = "SEAT_TURN_STARTED"
SEAT_TURN_COMPLETED = "SEAT_TURN_COMPLETED"
BOUT_TERMINAL = "BOUT_TERMINAL"
JOURNAL_LINE_UNREADABLE = "JOURNAL_LINE_UNREADABLE"

ENTRY_KINDS = frozenset(
    {BOUT_STARTED, SEAT_TURN_STARTED, SEAT_TURN_COMPLETED, BOUT_TERMINAL, JOURNAL_LINE_UNREADABLE}
)

TERMINAL_COMPLETED = "COMPLETED"
TERMINAL_REFUSED = "REFUSED"
TERMINAL_UNEXPECTED_EXCEPTION = "UNEXPECTED_EXCEPTION"
TERMINAL_INTERRUPTED = "INTERRUPTED"
TERMINAL_CRASHED_UNKNOWN = "CRASHED_UNKNOWN"

TERMINAL_STATUSES = frozenset(
    {
        TERMINAL_COMPLETED,
        TERMINAL_REFUSED,
        TERMINAL_UNEXPECTED_EXCEPTION,
        TERMINAL_INTERRUPTED,
        TERMINAL_CRASHED_UNKNOWN,
    }
)


@dataclass(frozen=True)
class BoutJournalEntryV1:
    """One journal line. ``detail`` holds string pairs only, so it always serialises."""

    bout_id: str
    kind: str
    task_key: str = ""
    sequence: int = 0
    detail: tuple[tuple[str, str], ...] = ()
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.kind not in ENTRY_KINDS:
            raise ValueError(f"unknown journal entry kind {self.kind!r}")
        object.__setattr__(self, "bout_id", str(self.bout_id))
        object.__setattr__(self, "task_key", str(self.task_key))
        object.__setattr__(
            self, "detail", tuple((str(key), str(value)) for key, value in self.detail)
        )

    def detail_map(self) -> dict[str, str]:
        return dict(self.detail)


class BoutJournalPort(Protocol):
    """Where journal entries go. A failed append is a typed refusal, never an exception."""

    def append(self, entry: BoutJournalEntryV1) -> Result[None, Refusal]: ...

    def read_all(self) -> Result[tuple[BoutJournalEntryV1, ...], Refusal]: ...


@dataclass(frozen=True)
class UnterminatedBoutV1:
    """A bout that started and has no terminal record."""

    bout_id: str
    task_key: str
    seat_turns_started: int
    seat_turns_completed: int

    @property
    def in_flight_seat_turns(self) -> int:
        return max(0, self.seat_turns_started - self.seat_turns_completed)


def unterminated_bouts(entries: Iterable[BoutJournalEntryV1], *, native_support: NativeOperationPort) -> tuple[UnterminatedBoutV1, ...]:
    """Inventory unfinished bouts in Rust in order of first appearance."""
    return tuple(
        UnterminatedBoutV1(**item)
        for item in native_value(native_support, "unterminated", entries=[asdict(entry) for entry in entries])
    )


def crashed_unknown_entry(bout: UnterminatedBoutV1, *, native_support: NativeOperationPort) -> BoutJournalEntryV1:
    record = native_value(native_support, "crashed_entry", bout=asdict(bout))
    record["detail"] = tuple(tuple(pair) for pair in record["detail"])
    return BoutJournalEntryV1(**record)


__all__ = [
    "BOUT_STARTED",
    "BOUT_TERMINAL",
    "ENTRY_KINDS",
    "JOURNAL_LINE_UNREADABLE",
    "SEAT_TURN_COMPLETED",
    "SEAT_TURN_STARTED",
    "TERMINAL_COMPLETED",
    "TERMINAL_CRASHED_UNKNOWN",
    "TERMINAL_INTERRUPTED",
    "TERMINAL_REFUSED",
    "TERMINAL_STATUSES",
    "TERMINAL_UNEXPECTED_EXCEPTION",
    "BoutJournalEntryV1",
    "BoutJournalPort",
    "UnterminatedBoutV1",
    "crashed_unknown_entry",
    "unterminated_bouts",
]
