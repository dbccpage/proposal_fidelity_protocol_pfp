from __future__ import annotations

from abc import ABC
from dataclasses import dataclass

from ..value_objects.digest import Digest
from ..value_objects.identifier import Identifier
from ..value_objects.sequence_number import SequenceNumber
from ..value_objects.temporal import TimestampUtc


@dataclass(frozen=True, slots=True)
class DomainEvent(ABC):
    """Abstract immutable domain event base class."""

    event_id: Identifier
    aggregate_id: Identifier
    event_type: str
    occurred_at: TimestampUtc
    version: SequenceNumber
    payload_digest: Digest
