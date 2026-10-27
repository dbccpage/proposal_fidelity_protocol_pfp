"""Polarized Morphisms for the Operadic Triad.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence, Tuple

from pfp.domain.operad.errors import (
    OperadRoleViolationError,
    ProhibitedEvaluationError,
    ProhibitedRepairError,
)
from pfp.domain.operad.polarity import Polarity


@dataclass(frozen=True)
class Finding:
    """An interrogation finding or unmet proof obligation emitted by O^-."""

    finding_id: str
    description: str
    severity: str = "OBSTRUCTION"
    rule_id: str = "PRIME_00"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.finding_id == other.finding_id
            and self.description == other.description
            and self.severity == other.severity
            and self.rule_id == other.rule_id
        )


@dataclass(frozen=True)
class CandidatePatch:
    """A candidate code or state repair patch emitted by O_repair."""

    patch_id: str
    target: str
    diff: str
    rationale: str = ""

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.patch_id == other.patch_id
            and self.target == other.target
            and self.diff == other.diff
            and self.rationale == other.rationale
        )


@dataclass(frozen=True)
class ConstructiveMorphism:
    """Constructive morphism (O^+) mapping requirements to candidate artifacts.

    Enforces role purity: cannot act as interrogative or repair morphism.
    """

    name: str
    input_types: Tuple[str, ...]
    output_type: str
    polarity: Polarity = Polarity.CONSTRUCTIVE

    def __post_init__(self) -> None:
        if self.polarity is not Polarity.CONSTRUCTIVE:
            raise OperadRoleViolationError(
                f"ConstructiveMorphism {self.name} declared invalid polarity {self.polarity}"
            )
        object.__setattr__(self, "input_types", tuple(self.input_types))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.name == other.name
            and self.input_types == other.input_types
            and self.output_type == other.output_type
            and self.polarity == other.polarity
        )

    @property
    def arity(self) -> int:
        return len(self.input_types)

    def propose(self, requirements: Mapping[str, Any]) -> dict[str, Any]:
        """Propose candidate artifact from requirements."""
        return {
            "morphism": self.name,
            "status": "CANDIDATE",
            "output_type": self.output_type,
            "payload": dict(requirements),
        }


@dataclass(frozen=True)
class InterrogativeMorphism:
    """Interrogative morphism (O^-) mapping candidates to findings.

    Enforces Law 4 (Detection-Repair Orthogonality): Strictly forbidden from
    returning patches. Calling emit_patch or attempting to return a patch raises
    ProhibitedRepairError.
    """

    name: str
    input_types: Tuple[str, ...]
    output_type: str
    polarity: Polarity = Polarity.INTERROGATIVE

    def __post_init__(self) -> None:
        if self.polarity is not Polarity.INTERROGATIVE:
            raise OperadRoleViolationError(
                f"InterrogativeMorphism {self.name} declared invalid polarity {self.polarity}"
            )
        object.__setattr__(self, "input_types", tuple(self.input_types))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.name == other.name
            and self.input_types == other.input_types
            and self.output_type == other.output_type
            and self.polarity == other.polarity
        )

    @property
    def arity(self) -> int:
        return len(self.input_types)

    def interrogate(
        self, candidate: Any, context: Mapping[str, Any] | None = None
    ) -> Sequence[Finding]:
        """Examine candidate and emit findings or unmet obligations."""
        findings: list[Finding] = []
        if isinstance(candidate, dict):
            # Check for defect markers or prohibited fields
            if candidate.get("has_defect", False):
                findings.append(
                    Finding(
                        finding_id=f"{self.name}-finding-01",
                        description=str(candidate.get("defect_reason", "Defect identified")),
                        severity="OBSTRUCTION",
                    )
                )
            if "patch" in candidate or "diff" in candidate:
                raise ProhibitedRepairError(
                    f"Interrogative morphism {self.name} intercepted patch payload; "
                    "O^- is strictly forbidden from handling or generating repair patches"
                )
        return tuple(findings)

    def emit_patch(self, *args: Any, **kwargs: Any) -> Any:
        """Strictly prohibited: O^- cannot emit repair patches."""
        raise ProhibitedRepairError(
            f"Interrogative morphism {self.name} attempted to emit a patch; "
            "Law 4 strictly forbids O^- from emitting patches"
        )


@dataclass(frozen=True)
class RepairMorphism:
    """Corrective repair morphism (O_repair) mapping subjects and findings to patches.

    Enforces Law 3 (Zero Self-Promoted Authority): Strictly forbidden from evaluating
    correctness or issuing admission verdicts. Calling evaluate or issuing verdicts
    raises ProhibitedEvaluationError.
    """

    name: str
    input_types: Tuple[str, ...]
    output_type: str
    polarity: Polarity = Polarity.CORRECTIVE

    def __post_init__(self) -> None:
        if self.polarity is not Polarity.CORRECTIVE:
            raise OperadRoleViolationError(
                f"RepairMorphism {self.name} declared invalid polarity {self.polarity}"
            )
        object.__setattr__(self, "input_types", tuple(self.input_types))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.name == other.name
            and self.input_types == other.input_types
            and self.output_type == other.output_type
            and self.polarity == other.polarity
        )

    @property
    def arity(self) -> int:
        return len(self.input_types)

    def repair(
        self, subject: Any, findings: Sequence[Finding]
    ) -> CandidatePatch:
        """Generate candidate repair patch addressing findings."""
        reasons = "; ".join(f.description for f in findings)
        return CandidatePatch(
            patch_id=f"patch-{self.name}",
            target=str(subject),
            diff=f"--- a/{subject}\n+++ b/{subject}\n# Repaired by {self.name} for: {reasons}",
            rationale=f"Automated remediation of {len(findings)} findings",
        )

    def evaluate(self, *args: Any, **kwargs: Any) -> Any:
        """Strictly prohibited: O_repair cannot evaluate correctness."""
        raise ProhibitedEvaluationError(
            f"Repair morphism {self.name} attempted to evaluate correctness; "
            "Law 3 strictly forbids O_repair from issuing verdicts or evaluations"
        )

    def admit(self, *args: Any, **kwargs: Any) -> Any:
        """Strictly prohibited: O_repair cannot issue admission verdicts."""
        raise ProhibitedEvaluationError(
            f"Repair morphism {self.name} attempted to issue admission decision; "
            "Law 3 strictly forbids O_repair from issuing admission decisions"
        )


__all__ = [
    "CandidatePatch",
    "ConstructiveMorphism",
    "Finding",
    "InterrogativeMorphism",
    "RepairMorphism",
]
