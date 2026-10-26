from __future__ import annotations

from abc import ABC
from dataclasses import dataclass

from ..value_objects.identifier import Identifier
from ..value_objects.temporal import TimestampUtc


@dataclass(frozen=True, slots=True)
class Command(ABC):
    """Abstract base command representing user or agent intent."""

    command_id: Identifier
    issued_at: TimestampUtc
    issuer_id: Identifier
