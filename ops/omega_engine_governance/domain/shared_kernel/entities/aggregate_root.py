"""Strongly-Typed Domain Aggregate Root Base.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from ..events.domain_event import DomainEvent
from ..value_objects.domain_invariant_error import DomainInvariantError
from ..value_objects.identifier import Identifier
from ..value_objects.sequence_number import SequenceNumber
from .entity import Entity

ID = TypeVar("ID", bound=Identifier)


@dataclass(slots=True, eq=False)
class AggregateRoot(Entity[ID], Generic[ID]):
    """Aggregate root base managing domain event emission, aggregate ID enforcement, and optimistic versioning."""

    version: SequenceNumber = field(default_factory=lambda: SequenceNumber(0))
    _uncommitted_events: list[DomainEvent] = field(
        default_factory=list, init=False, repr=False
    )

    def record_event(self, event: DomainEvent) -> None:
        """Record uncommitted domain event ensuring aggregate ID match and monotonic versioning."""
        if event.aggregate_id != self.id:
            raise DomainInvariantError(
                "AGGREGATE_ID_MISMATCH",
                f"Event aggregate_id {event.aggregate_id} does not match AggregateRoot id {self.id}",
            )
        expected_version = self.version.next()
        if event.version != expected_version:
            raise DomainInvariantError(
                "EVENT_VERSION_MISMATCH",
                f"Expected event version {expected_version}, got {event.version}",
            )
        self._uncommitted_events.append(event)
        self.version = expected_version

    def uncommitted_events(self) -> tuple[DomainEvent, ...]:
        """Return tuple of uncommitted domain events recorded on this aggregate."""
        return tuple(self._uncommitted_events)

    def clear_events(self) -> None:
        """Clear uncommitted domain events."""
        self._uncommitted_events.clear()
