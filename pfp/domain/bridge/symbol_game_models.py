from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from omega_engine_pfp.domain.entities.packet_envelope import PacketEnvelopeV2
from omega_engine_pfp.domain.models import ObstructionScore


@dataclass(frozen=True)
class SceneBeat:
    """A single dramatic and technical dialogue beat in a scene."""

    speaker: str
    cue: str
    dialogue: str
    operator_tag: str
    cochain: Optional[Any] = None


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
