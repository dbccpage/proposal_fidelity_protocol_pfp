from __future__ import annotations

from dataclasses import dataclass, field

from ..value_objects.domain_invariant_error import DomainInvariantError
from ..value_objects.identifier import Identifier
from .domain_event import DomainEvent


@dataclass(slots=True)
class EventStream:
    """In-memory append-only sequence of domain events for an aggregate."""

    aggregate_id: Identifier
    _events: list[DomainEvent] = field(default_factory=list)

    def append(self, event: DomainEvent) -> None:
        if event.aggregate_id != self.aggregate_id:
            raise DomainInvariantError(
                f"Cannot append event for aggregate {event.aggregate_id} to stream for {self.aggregate_id}"
            )
        if self._events and event.version.value <= self._events[-1].version.value:
            raise DomainInvariantError(
                f"Event version {event.version.value} must be strictly greater than preceding {self._events[-1].version.value}"
            )
        self._events.append(event)

    def events(self) -> tuple[DomainEvent, ...]:
        return tuple(self._events)

    def __len__(self) -> int:
        return len(self._events)
