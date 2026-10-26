"""Inspect and close interrupted bouts under an explicit single-writer assumption.

Reconciliation records CRASHED_UNKNOWN; it never retries an in-flight model call.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.domain.native import NativeOperationPort

from ..domain.bout_journal import (
    BOUT_TERMINAL,
    JOURNAL_LINE_UNREADABLE,
    BoutJournalEntryV1,
    BoutJournalPort,
    UnterminatedBoutV1,
    crashed_unknown_entry,
    unterminated_bouts,
)

_LOCUS = "omega_engine_woland.use_cases.bout_recovery"


@dataclass(frozen=True)
class BoutJournalInspectionV1:
    total_entries: int
    terminal_entries: int
    unfinished_bouts: tuple[UnterminatedBoutV1, ...]
    unreadable_entries: tuple[BoutJournalEntryV1, ...]
    authority_effect: str = "None"

    @property
    def reconciliation_allowed(self) -> bool:
        return not self.unreadable_entries

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "reconciliation_allowed": self.reconciliation_allowed}


def inspect_bout_journal(journal: BoutJournalPort, *, native_support: NativeOperationPort) -> Result[BoutJournalInspectionV1, Refusal]:
    """Read without writing; preserve damaged-line identities for operator inspection."""
    try:
        read = journal.read_all()
        if isinstance(read, Err):
            return read
        if not isinstance(read, Ok):
            raise TypeError("journal read did not return a typed result")
        entries = tuple(read.value)
        if any(type(entry) is not BoutJournalEntryV1 for entry in entries):
            raise TypeError("journal contains an invalid entry")
        return Ok(
            BoutJournalInspectionV1(
                total_entries=len(entries),
                terminal_entries=sum(entry.kind == BOUT_TERMINAL for entry in entries),
                unfinished_bouts=unterminated_bouts(entries, native_support=native_support),
                unreadable_entries=tuple(
                    entry for entry in entries if entry.kind == JOURNAL_LINE_UNREADABLE
                ),
            )
        )
    except Exception as exc:
        return Err(Refusal("BOUT_JOURNAL_INSPECTION_FAILED", str(exc), _LOCUS))


def reconcile_crashed_bouts(
    journal: BoutJournalPort,
    *,
    native_support: NativeOperationPort,
) -> Result[tuple[UnterminatedBoutV1, ...], Refusal]:
    """Close unfinished bouts once, before new work, with no other live writer.

    A damaged line could hide a terminal record, so automatic closure refuses
    and leaves bytes intact for inspection. A failed append retains earlier
    closures; the next explicit call inventories the remaining open bouts.
    """
    inspection = inspect_bout_journal(journal, native_support=native_support)
    if isinstance(inspection, Err):
        return inspection
    if not inspection.value.reconciliation_allowed:
        return Err(
            Refusal(
                "BOUT_RECONCILE_CORRUPT",
                "journal has unreadable lines; inspect and repair the journal before reconciliation",
                _LOCUS,
            )
        )
    closed: list[UnterminatedBoutV1] = []
    for bout in inspection.value.unfinished_bouts:
        try:
            appended = journal.append(crashed_unknown_entry(bout, native_support=native_support))
            if isinstance(appended, Err):
                raise ValueError(appended.error.code)
            if not isinstance(appended, Ok):
                raise TypeError("journal append did not return a typed result")
        except Exception as exc:
            return Err(
                Refusal(
                    "BOUT_RECONCILE_INCOMPLETE",
                    f"closed {len(closed)} bout(s) before the journal refused: {exc}",
                    _LOCUS,
                )
            )
        closed.append(bout)
    return Ok(tuple(closed))


__all__ = ["BoutJournalInspectionV1", "inspect_bout_journal", "reconcile_crashed_bouts"]
