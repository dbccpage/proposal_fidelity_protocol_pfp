"""Turn Repository Port Protocol."""

from __future__ import annotations

from typing import Protocol

from ..aggregates.llm_turn_run_root import LlmTurnContentArtifactV1, LlmTurnRunRootV1
from ..entities.candidate_artifact import CandidateArtifactV1


class ITurnRepository(Protocol):
    """Protocol for LLM Turn Run persistence and retrieval."""

    def save_run_root(self, run_root: LlmTurnRunRootV1) -> None:
        ...

    def get_run_root(self, run_root_id: str) -> LlmTurnRunRootV1 | None:
        ...

    def save_content_artifact(self, artifact: LlmTurnContentArtifactV1) -> None:
        ...

    def get_content_artifact(self, artifact_id: str) -> LlmTurnContentArtifactV1 | None:
        ...

    def save_candidate_artifact(self, candidate: CandidateArtifactV1) -> None:
        ...

    def get_candidate_artifact(self, candidate_id: str) -> CandidateArtifactV1 | None:
        ...
