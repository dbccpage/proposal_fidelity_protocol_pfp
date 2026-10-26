"""Native Unicode motif mining through an injected domain port."""

from __future__ import annotations

from dataclasses import asdict
from typing import Sequence

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_prompt_civilization.domain.intelligence_metabolism.models import (
    MotifRecordV1,
    ObstructionEpisodeV1,
)
from omega_engine_prompt_civilization.domain.intelligence_metabolism.ports import (
    MetabolismKernelPort,
)

from .episode import wire


class MotifMiner:
    def __init__(self, kernel: MetabolismKernelPort) -> None:
        self.kernel = kernel

    def mine_motifs(
        self, episodes: Sequence[ObstructionEpisodeV1], max_n: int = 6
    ) -> Result[list[MotifRecordV1], Refusal]:
        result = self.kernel.execute(
            wire(
                {
                    "operation": "motifs",
                    "episodes": [asdict(episode) for episode in episodes],
                    "max_n": max_n,
                }
            )
        )
        if isinstance(result, Err):
            return result
        return Ok(
            [
                MotifRecordV1(**{**motif, "evidence_runs": tuple(motif["evidence_runs"])})
                for motif in result.value
            ]
        )
