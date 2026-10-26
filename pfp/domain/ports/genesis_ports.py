"""Domain protocols for Genesis Crosswalk & Anchor Verification (Prompt 29, 38).

AuthorityEffect: None.
Clean Architecture: Domain port protocols (@runtime_checkable).
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from ..genesis.models import GenesisStage, GenesisStagePin, InvariantTriad


@runtime_checkable
class IGenesisStageRegistry(Protocol):
    """Protocol for Genesis stage registry query and apparatus tracking."""

    def get_stage(self, level: int) -> GenesisStage | None:
        """Returns the GenesisStage at level n, or None if out of range."""
        ...

    def get_all_stages(self) -> Sequence[GenesisStage]:
        """Returns all 101 stages in the crosswalk."""
        ...

    def apparatus_stages(self) -> frozenset[int]:
        """Returns the set of 21 apparatus stages under Ruling D4 ({12, 17} U [82, 100])."""
        ...

    def verify_pin(self, candidate_pin: str) -> bool:
        """Verifies candidate pin against master pin e28f49abea3310ae4a9dc3d17ecb9ab55b267938."""
        ...


@runtime_checkable
class IGenesisCrosswalkOracle(Protocol):
    """Protocol for Genesis compendium text and anchor verification."""

    def validate_stage_block(self, level: int, raw_text: str) -> InvariantTriad:
        """Validates that a stage block contains complete InvariantTriad."""
        ...

    def check_claim_hygiene(self, text: str) -> Sequence[str]:
        """Returns detected forbidden hype words in text."""
        ...

    def verify_non_aliasing(self, text: str) -> bool:
        """Verifies non-aliasing boundaries between derivation lineages."""
        ...
