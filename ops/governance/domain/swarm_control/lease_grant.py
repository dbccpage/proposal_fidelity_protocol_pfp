"""Lease Grant Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LeaseGrant:
    packet_id: str
    paths: tuple[str, ...] = ()
    exclusive_resources: tuple[str, ...] = ()
