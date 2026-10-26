"""Research Repository Port Protocol."""

from __future__ import annotations

from typing import Protocol

from ..aggregates.research_run_root import ResearchClaimV1, ResearchRunRootV1
from ..entities.source_artifact import SourceArtifactV1, SourceIntakeBundleV1


class IResearchRepository(Protocol):
    """Protocol for Research Claims and Intake persistence and retrieval."""

    def save_run_root(self, run_root: ResearchRunRootV1) -> None:
        ...

    def get_run_root(self, run_root_id: str) -> ResearchRunRootV1 | None:
        ...

    def save_claim(self, claim: ResearchClaimV1) -> None:
        ...

    def save_intake_bundle(self, bundle: SourceIntakeBundleV1) -> None:
        ...
