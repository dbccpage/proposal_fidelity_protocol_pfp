"""Pure domain models for Genesis Crosswalk & Anchor Verification (Prompt 29, 38).

AuthorityEffect: None.
ZERO-FLOAT Law: Pure discrete representation; zero floats.
Clean Architecture: Zero outward dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GenesisStagePin:
    """Master cryptographic stage pin locking Genesis byte-level reference state."""

    commit_hash: str = "e28f49abea3310ae4a9dc3d17ecb9ab55b267938"

    def is_valid_pin(self) -> bool:
        return self.commit_hash == "e28f49abea3310ae4a9dc3d17ecb9ab55b267938"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.commit_hash == other.commit_hash


@dataclass(frozen=True)
class GenesisStage:
    """Genesis stage entry in the 101-stage crosswalk."""

    level: int
    title: str
    obligation: str
    counterexample: str
    primary_opcode: Optional[int] = None
    is_apparatus: bool = False

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.level,
            self.title,
            self.obligation,
            self.counterexample,
            self.primary_opcode,
            self.is_apparatus,
        ) == (
            other.level,
            other.title,
            other.obligation,
            other.counterexample,
            other.primary_opcode,
            other.is_apparatus,
        )


@dataclass(frozen=True)
class InvariantTriad:
    """Invariant triad required for every Genesis stage block."""

    obligation: str
    counterexample: str
    extension_interface: str

    @property
    def is_complete(self) -> bool:
        return bool(
            self.obligation.strip()
            and self.counterexample.strip()
            and self.extension_interface.strip()
        )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.obligation,
            self.counterexample,
            self.extension_interface,
        ) == (
            other.obligation,
            other.counterexample,
            other.extension_interface,
        )
