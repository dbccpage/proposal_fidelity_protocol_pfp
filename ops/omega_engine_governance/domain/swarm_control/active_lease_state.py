"""Active Lease State.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ActiveLeaseState:
    packet_id: str
    paths: tuple[str, ...]
    exclusive_resources: tuple[str, ...]
    stacked_under: str | None = None
