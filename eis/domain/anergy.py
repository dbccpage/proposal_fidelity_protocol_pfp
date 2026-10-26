"""Anergy monitor emitting proposals to TregSupervisor without automatic suspension.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnergyProposalV1:
    """Proposal emitted to TregSupervisor queue when false positive threshold is reached."""
    detector_id: str
    is_suspended: bool = False
    destination_queue: str = "TregSupervisor"


class AnergyMonitorV1:
    """Monitors benign hit frequencies and proposes anergy without self-suspending."""

    def __init__(self, anergy_threshold: int = 5) -> None:
        self.anergy_threshold = anergy_threshold
        self._counts: dict[str, int] = {}

    def record_benign_hit(self, detector_id: str) -> AnergyProposalV1 | None:
        self._counts[detector_id] = self._counts.get(detector_id, 0) + 1
        if self._counts[detector_id] >= self.anergy_threshold:
            return AnergyProposalV1(
                detector_id=detector_id,
                is_suspended=False,
                destination_queue="TregSupervisor",
            )
        return None
