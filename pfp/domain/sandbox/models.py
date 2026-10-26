"""Pure domain models for Container Sandbox Seam & Process Boundary (Prompt 13).

AuthorityEffect: None.
ZERO-FLOAT Law: Timeouts and metrics expressed in Fraction or integer.
Clean Architecture: Zero outward dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any, Mapping, Tuple, Union


class ContainerProfile(Enum):
    """Execution profile for container sandbox boundary."""

    PROFILE_A_MOCK = "profile_a_mock"
    PROFILE_B_DOCKER = "profile_b_docker"


@dataclass(frozen=True)
class ProcessBoundaryConfig:
    """Configuration for isolated process execution seam."""

    profile: ContainerProfile
    workspace_root: str
    allowed_commands: Tuple[str, ...]
    max_memory_bytes: int
    timeout_seconds: Union[Fraction, int] = 5

    def __post_init__(self) -> None:
        if isinstance(self.timeout_seconds, float):
            raise TypeError("ZERO-FLOAT Law: timeout_seconds must be Fraction or int, not float")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.profile,
            self.workspace_root,
            self.allowed_commands,
            self.max_memory_bytes,
            self.timeout_seconds,
        ) == (
            other.profile,
            other.workspace_root,
            other.allowed_commands,
            other.max_memory_bytes,
            other.timeout_seconds,
        )


@dataclass(frozen=True)
class SeamExecutionResult:
    """Execution output from isolated process sandbox seam."""

    exit_code: int
    stdout_json: Mapping[str, Any]
    stderr_text: str
    session_digest: str

    @property
    def is_success(self) -> bool:
        return self.exit_code == 0

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (self.exit_code, self.session_digest, self.stderr_text) == (
            other.exit_code,
            other.session_digest,
            other.stderr_text,
        )
