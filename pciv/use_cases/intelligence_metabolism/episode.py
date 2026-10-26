"""Native obstruction segmentation through an injected domain port."""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Sequence

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_prompt_civilization.domain.intelligence_metabolism.models import (
    ObstructionEpisodeV1,
)
from omega_engine_prompt_civilization.domain.intelligence_metabolism.ports import (
    MetabolismKernelPort,
)


def wire(value: Any) -> Any:
    """Preserve fraction type: source zero-string checks distinguish Fraction(0)."""
    if isinstance(value, Fraction):
        return {"fraction": str(value)}
    if isinstance(value, dict):
        return {key: wire(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [wire(item) for item in value]
    return value


def _fraction(value: Any) -> Any:
    if isinstance(value, dict) and set(value) == {"fraction"}:
        return Fraction(value["fraction"])
    return value


class EpisodeSegmenter:
    def __init__(self, kernel: MetabolismKernelPort) -> None:
        self.kernel = kernel

    def segment_run(
        self, run_id: str, steps: Sequence[dict[str, Any]]
    ) -> Result[list[ObstructionEpisodeV1], Refusal]:
        result = self.kernel.execute(
            wire({"operation": "segment", "run_id": run_id, "steps": steps})
        )
        if isinstance(result, Err):
            return result
        return Ok(
            [
                ObstructionEpisodeV1(
                    **{
                        key: _fraction(value) if key.startswith(("phi_1_", "gamma_2_")) else value
                        for key, value in episode.items()
                    }
                )
                for episode in result.value
            ]
        )
