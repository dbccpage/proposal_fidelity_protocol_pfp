"""Obstruction Ledger Adapter."""

from __future__ import annotations

from typing import Any

from ...domain.shared_kernel import AuthorityEffect
from ...domain.entities import ObstructionLedgerEvent


class ObstructionLedgerAdapter:
    """Adapter tracking discrete transitions on the obstruction lattice."""

    def __init__(self) -> None:
        self._events: list[ObstructionLedgerEvent] = []

    def record_transition(
        self,
        *,
        step: int,
        obstruction_id: str,
        disposition: str,
        magnitude: float,
        witness: str,
    ) -> ObstructionLedgerEvent:
        event = ObstructionLedgerEvent(
            step=step,
            obstruction_id=obstruction_id,
            disposition=disposition,
            magnitude=magnitude,
            witness=witness,
        )
        self._events.append(event)
        return event

    def get_events(self) -> tuple[ObstructionLedgerEvent, ...]:
        return tuple(self._events)
