from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from omega_engine_pfp.domain import PacketEnvelopeV2


@dataclass(frozen=True)
class SceneBeat:
    """A single dramatic and technical dialogue beat in a scene."""

    speaker: str
    cue: str
    dialogue: str
    operator_tag: str
    cochain: Optional[Any] = None


@dataclass(frozen=True)
class ObstructionScore:
    gamma_2: float
    phi_1: float
    active_count: int
    active_obstruction_ids: Tuple[str, ...] = ()

    @property
    def is_exact(self) -> bool:
        return self.gamma_2 == 0.0 and self.phi_1 == 0.0 and self.active_count == 0

    def strictly_improves(self, prior: "ObstructionScore") -> bool:
        if self.phi_1 < prior.phi_1 and self.gamma_2 <= prior.gamma_2:
            return True
        if self.phi_1 <= prior.phi_1 and self.gamma_2 < prior.gamma_2:
            return True
        return (
            self.phi_1 <= prior.phi_1
            and self.gamma_2 <= prior.gamma_2
            and self.active_count < prior.active_count
        )


@dataclass(frozen=True)
class SymbolGameStepResult:
    step_index: int
    packet: PacketEnvelopeV2
    candidate_proposal: Dict[str, Any]
    obstruction_score: ObstructionScore
    prior_score: Optional[ObstructionScore]
    strict_descent_passed: bool
    scene_beats: Tuple[SceneBeat, ...] = ()
    status: str = "IN_PROGRESS"
    child_packet: Optional[PacketEnvelopeV2] = None
    action_taken: str = "CHILD_PACKET"

    @property
    def character_debates(self) -> Tuple[SceneBeat, ...]:
        return self.scene_beats
