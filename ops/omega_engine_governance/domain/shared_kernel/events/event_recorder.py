from __future__ import annotations

from typing import Protocol

from .domain_event import DomainEvent


class EventRecorder(Protocol):
    """Protocol for entities or aggregates that record domain events."""

    def record_event(self, event: DomainEvent) -> None:
        ...

    def uncommitted_events(self) -> tuple[DomainEvent, ...]:
        ...

    def clear_events(self) -> None:
        ...
