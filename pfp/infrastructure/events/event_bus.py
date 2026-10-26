"""In-Memory Event Bus and Transactional Outbox for Domain Events.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
import datetime
from typing import Any, Callable, List, Type

from ...domain.events import DomainEvent
from ...domain.ports.ports import IEventBus, IOutbox


@dataclass
class OutboxMessage:
    """Represents a staged event awaiting guaranteed dispatch."""

    message_id: str
    event_type: str
    aggregate_id: str
    aggregate_type: str
    payload: DomainEvent
    staged_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    dispatched: bool = False


class InMemoryEventBus:
    """In-process thread-safe event bus."""

    def __init__(self) -> None:
        self._handlers: dict[Type[DomainEvent], list[Callable[[DomainEvent], None]]] = defaultdict(list)
        self._recorded_events: list[DomainEvent] = []

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        """Register an event handler for a specific domain event type."""
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all registered subscribers."""
        self._recorded_events.append(event)
        # Dispatch to specific event type handlers
        for handler in self._handlers[type(event)]:
            handler(event)
        # Dispatch to base DomainEvent handlers if registered
        if type(event) is not DomainEvent:
            for handler in self._handlers[DomainEvent]:
                handler(event)

    @property
    def recorded_events(self) -> tuple[DomainEvent, ...]:
        """Returns all recorded events for verification/testing."""
        return tuple(self._recorded_events)

    def clear(self) -> None:
        """Clears the recorded event log."""
        self._recorded_events.clear()


class TransactionalOutbox:
    """In-memory transactional outbox staging domain events for atomic persistence."""

    def __init__(self, event_bus: IEventBus | None = None) -> None:
        self._event_bus = event_bus or InMemoryEventBus()
        self._staged: list[OutboxMessage] = []

    def stage_event(self, event: DomainEvent) -> None:
        """Stages a domain event in the outbox."""
        msg = OutboxMessage(
            message_id=event.event_id,
            event_type=type(event).__name__,
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            payload=event,
        )
        self._staged.append(msg)

    def dispatch_pending(self) -> int:
        """Dispatches all pending staged events to the event bus."""
        count = 0
        for msg in self._staged:
            if not msg.dispatched:
                self._event_bus.publish(msg.payload)
                msg.dispatched = True
                count += 1
        return count

    @property
    def pending_count(self) -> int:
        return sum(1 for m in self._staged if not m.dispatched)


__all__ = [
    "InMemoryEventBus",
    "OutboxMessage",
    "TransactionalOutbox",
]
