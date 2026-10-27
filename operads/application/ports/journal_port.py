"""Port for append-only event journal and idempotency records."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from operations.domain.rop.result import Result
from ...domain.errors.domain_errors import OeopDomainError
from ...domain.events.domain_events import DomainEventV3
from ...domain.value_objects.identifier import IdempotencyKey


class JournalPort(ABC):
    @abstractmethod
    def check_idempotency(
        self,
        key: IdempotencyKey,
        request_digest: str,
    ) -> Result[Optional[dict], OeopDomainError]:
        """Check if request with idempotency key was already executed."""
        pass

    @abstractmethod
    def append_events(
        self,
        stream_id: str,
        expected_version: Optional[int],
        events: Tuple[DomainEventV3, ...],
    ) -> Result[int, OeopDomainError]:
        """Append domain events to stream, returning new version."""
        pass
