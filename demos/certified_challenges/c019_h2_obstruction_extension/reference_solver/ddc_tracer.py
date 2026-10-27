"""Discrete Deformation Calculus (DDC) 8-Letter Operational Tracer for C019."""

from __future__ import annotations

import dataclasses
from typing import Any


@dataclasses.dataclass
class DdcStepReceipt:
    letter: str
    phase: str
    action: str
    metrics: dict[str, Any] = dataclasses.field(default_factory=dict)


class DdcOperationalTracer:
    VALID_LETTERS = {"E", "R", "C", "I", "Lambda", "D", "M", "T"}

    def __init__(self, challenge_id: str = "c019_h2_obstruction_extension") -> None:
        self.challenge_id = challenge_id
        self.trace: list[DdcStepReceipt] = []

    def record(self, letter: str, phase: str, action: str, **metrics: Any) -> DdcStepReceipt:
        if letter not in self.VALID_LETTERS:
            raise ValueError(f"Invalid DDC operational letter: {letter}")
        receipt = DdcStepReceipt(letter=letter, phase=phase, action=action, metrics=metrics)
        self.trace.append(receipt)
        return receipt

    def export_trace(self) -> list[dict[str, Any]]:
        return [dataclasses.asdict(r) for r in self.trace]
