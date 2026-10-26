"""Shared Kernel: Strongly-typed Domain Identifiers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar, Self

from ..exceptions import InvariantViolationError

_DEFAULT_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.:]{1,128}$")
DEFAULT_ID_REGEX = _DEFAULT_ID_REGEX


@dataclass(frozen=True, slots=True, eq=False)
class Identifier:
    """Base immutable, strongly-typed domain identifier Value Object."""

    value: str

    PATTERN: ClassVar[re.Pattern[str]] = _DEFAULT_ID_REGEX

    def __post_init__(self) -> None:
        cls_name = self.__class__.__name__
        if not isinstance(self.value, str):
            raise InvariantViolationError(
                f"{cls_name} must be a string, got {type(self.value).__name__}"
            )
        val = self.value.strip()
        if not val:
            raise InvariantViolationError(f"{cls_name} must not be empty or whitespace only")
        if not self.PATTERN.match(val):
            raise InvariantViolationError(
                f"Invalid {cls_name} {val!r}: must match pattern {self.PATTERN.pattern}"
            )
        if val != self.value:
            object.__setattr__(self, "value", val)

    @classmethod
    def from_str(cls: type[Self], val: str | Self) -> Self:
        if isinstance(val, cls):
            return val
        if type(val) is not str:
            raise InvariantViolationError(
                f"{cls.__name__}.from_str requires an exact str, got {type(val).__name__}"
            )
        return cls(val)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))


@dataclass(frozen=True, slots=True, eq=False)
class ObstructionId(Identifier):
    """Obstruction Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class DemandId(Identifier):
    """Demand item Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class TaskId(Identifier):
    """Task Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class ReceiptId(Identifier):
    """Receipt Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class PromptArtifactId(Identifier):
    """Prompt Artifact Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class CandidateId(Identifier):
    """Candidate Proposal Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class RunRootId(Identifier):
    """Run Root Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class ProducerId(Identifier):
    """Producer Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class CarrierId(Identifier):
    """Carrier graph Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class PatchArtifactId(Identifier):
    """Patch Artifact Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class ContentArtifactId(Identifier):
    """Content Artifact Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class ClaimId(Identifier):
    """Research Claim Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class HypothesisId(Identifier):
    """Hypothesis Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class IntakeBundleId(Identifier):
    """Intake Bundle Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class CorpusId(Identifier):
    """Evaluation Corpus Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class PolicyId(Identifier):
    """Routing Policy Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class SampleId(Identifier):
    """Corpus Sample Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class PacketId(Identifier):
    """Packet Envelope Identifier value object."""


@dataclass(frozen=True, slots=True, eq=False)
class EventId(Identifier):
    """Ledger and Process Event Identifier value object."""
