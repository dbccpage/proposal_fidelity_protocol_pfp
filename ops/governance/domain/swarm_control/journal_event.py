"""Journal Event Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any
from .packet_state import PacketState


@dataclass(frozen=True)
class JournalEvent:
    seq: int
    event_type: str
    packet_id: str
    to_state: PacketState
    schema_version: str = "1"
    payload: Mapping[str, Any] = field(default_factory=dict)
