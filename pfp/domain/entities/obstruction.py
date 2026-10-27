from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from operads.canon import DdcLetter
from pfp.domain.shared_kernel.canonical import domain_digest, freeze
DdaLetter = DdcLetter




@dataclass(frozen=True, slots=True)
class ObstructionLedgerEvent:
    step: int
    obstruction_id: str
    disposition: str
    magnitude: float
    witness: str


class ObstructionLedger:
    """Maintain every active obstruction across accepted retractions."""

    def __init__(self) -> None:
        self._active: dict[str, float] = {}
        self._ever_seen: set[str] = set()
        self._events: list[ObstructionLedgerEvent] = []

    def reconcile(
        self,
        projection: ProjectionReceipt,
        *,
        step: int,
        witness: str,
    ) -> None:
        next_active = {
            item.obstruction_id: item.magnitude for item in projection.obstructions
        }
        for obstruction_id, magnitude in sorted(next_active.items()):
            if obstruction_id not in self._active:
                disposition = (
                    "REOPENED" if obstruction_id in self._ever_seen else "OPENED"
                )
                self._events.append(
                    ObstructionLedgerEvent(
                        step=step,
                        obstruction_id=obstruction_id,
                        disposition=disposition,
                        magnitude=magnitude,
                        witness=witness,
                    )
                )
                self._ever_seen.add(obstruction_id)
            elif magnitude != self._active[obstruction_id]:
                self._events.append(
                    ObstructionLedgerEvent(
                        step=step,
                        obstruction_id=obstruction_id,
                        disposition="UPDATED",
                        magnitude=magnitude,
                        witness=witness,
                    )
                )
        for obstruction_id, magnitude in sorted(self._active.items()):
            if obstruction_id not in next_active:
                self._events.append(
                    ObstructionLedgerEvent(
                        step=step,
                        obstruction_id=obstruction_id,
                        disposition="DISCHARGED",
                        magnitude=magnitude,
                        witness=witness,
                    )
                )
        self._active = next_active

    @property
    def active_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._active))

    @property
    def events(self) -> tuple[ObstructionLedgerEvent, ...]:
        return tuple(self._events)


@dataclass(frozen=True, slots=True)
class ProcessEvent:
    sequence: int
    event_type: str
    dda_letter: str
    input_state_hash: str
    output_state_hash: str
    details: Any
    parent_hash: str | None
    event_hash: str
    authority_effect: str = field(default="None")


def _event_hash_fields(event: ProcessEvent) -> dict[str, Any]:
    return {
        "sequence": event.sequence,
        "event_type": event.event_type,
        "dda_letter": event.dda_letter,
        "input_state_hash": event.input_state_hash,
        "output_state_hash": event.output_state_hash,
        "details": event.details,
        "parent_hash": event.parent_hash,
        "authority_effect": event.authority_effect,
    }


class ProcessEventLog:
    """Content-addressed parent chain without timestamps or mutable run IDs."""

    def __init__(self, parent_hash: str | None = None) -> None:
        self._events: list[ProcessEvent] = []
        self._parent_hash = parent_hash

    def append(
        self,
        event_type: str,
        dda_letter: DdaLetter,
        input_state_hash: str,
        output_state_hash: str,
        details: Any,
    ) -> ProcessEvent:
        parent_hash = self._events[-1].event_hash if self._events else self._parent_hash
        shell = ProcessEvent(
            sequence=len(self._events),
            event_type=event_type,
            dda_letter=dda_letter.value,
            input_state_hash=input_state_hash,
            output_state_hash=output_state_hash,
            details=freeze(details),
            parent_hash=parent_hash,
            event_hash="",
        )
        event_hash = domain_digest(
            "core.oesos.process-event.v1", _event_hash_fields(shell)
        )
        event = ProcessEvent(
            sequence=shell.sequence,
            event_type=shell.event_type,
            dda_letter=shell.dda_letter,
            input_state_hash=shell.input_state_hash,
            output_state_hash=shell.output_state_hash,
            details=shell.details,
            parent_hash=shell.parent_hash,
            event_hash=event_hash,
        )
        self._events.append(event)
        return event

    @property
    def events(self) -> tuple[ProcessEvent, ...]:
        return tuple(self._events)

    @property
    def root(self) -> str:
        return (
            self._events[-1].event_hash
            if self._events
            else domain_digest("core.oesos.process-event.v1", ())
        )


def verify_event_chain(
    events: tuple[ProcessEvent, ...],
    parent_hash: str | None = None,
) -> bool:
    parent = parent_hash
    previous_output: str | None = None
    stationary_letters = {
        DdaLetter.C.value,
        DdaLetter.R.value,
        DdaLetter.M.value,
        DdaLetter.I.value,
        DdaLetter.T.value,
    }
    for sequence, event in enumerate(events):
        if event.sequence != sequence or event.parent_hash != parent:
            return False
        if event.authority_effect != "None":
            return False
        if event.dda_letter not in {letter.value for letter in DdaLetter}:
            return False
        if previous_output is not None and event.input_state_hash != previous_output:
            return False
        if (
            event.dda_letter in stationary_letters
            and event.input_state_hash != event.output_state_hash
        ):
            return False
        expected = domain_digest(
            "core.oesos.process-event.v1", _event_hash_fields(event)
        )
        if event.event_hash != expected:
            return False
        parent = event.event_hash
        previous_output = event.output_state_hash
    return True
