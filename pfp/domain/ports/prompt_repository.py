"""Prompt Repository Port Protocol."""

from __future__ import annotations

from typing import Protocol

from ..aggregates.prompt_artifact import EliminationReceiptV1, PromptArtifactV1


class IPromptRepository(Protocol):
    """Protocol for PromptArtifact persistence and retrieval."""

    def save_prompt_artifact(self, artifact: PromptArtifactV1) -> None:
        ...

    def get_prompt_artifact(self, artifact_id: str) -> PromptArtifactV1 | None:
        ...

    def save_elimination_receipt(self, receipt: EliminationReceiptV1) -> None:
        ...

    def get_elimination_receipt(self, receipt_id: str) -> EliminationReceiptV1 | None:
        ...
