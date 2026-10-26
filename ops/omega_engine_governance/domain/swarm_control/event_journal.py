"""Write-once Append Journal (1 class).

AuthorityEffect: None.
"""

from __future__ import annotations

from .journal_event import JournalEvent


class EventJournal:
    """Write-once append journal. No in-place rewrite API."""

    def __init__(self) -> None:
        self._events: list[JournalEvent] = []

    def append(self, event: JournalEvent) -> None:
        if self._events and event.seq != self._events[-1].seq + 1:
            raise ValueError(
                f"SEQUENCE_GAP:expected={self._events[-1].seq + 1} got={event.seq}"
            )
        if not self._events and event.seq != 0:
            raise ValueError(f"SEQUENCE_GAP:expected=0 got={event.seq}")
        if any(e.seq == event.seq for e in self._events):
            raise ValueError(f"SEQUENCE_DUPLICATE:{event.seq}")
        self._events.append(event)

    def events(self) -> tuple[JournalEvent, ...]:
        return tuple(self._events)

    def rewrite_forbidden(self) -> None:
        """Documented non-API: journals have no rewrite method."""
        raise AttributeError("JOURNAL_REWRITE_FORBIDDEN")
