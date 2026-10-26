"""
models.py
=========

Swarm Immune System & Pharmacy Domain Value Objects.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict


class ConstraintType(str, Enum):
    PROJECT_OUT = "ProjectOut"
    RESTRAIN = "Restrain"
    ENFORCE = "Enforce"


class Operatorizability(str, Enum):
    REPAIRABLE = "repairable"
    FATAL = "fatal"


class RuntimeAction(str, Enum):
    REPAIR = "repair"
    ABORT = "abort"


class Severity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class PharmacyStatus(str, Enum):
    CANDIDATE = "candidate"
    ADMITTED = "admitted"
    REJECTED = "rejected"
    #: The defect this antibody guards against never existed -- the detector was
    #: wrong. Distinct from REJECTED, which judges a real defect not worth
    #: guarding. A retired antibody is named, not deleted.
    RETIRED = "retired"


class AntibodyCustodyTier(str, Enum):
    CANDIDATE = "Candidate"
    PROVISIONAL = "Provisional"
    HUMAN_ADMITTED = "HumanAdmitted"
    REVOKED = "Revoked"
    RETIRED = "Retired"


PHARMACY_STATUS_UNKNOWN = "PHARMACY_STATUS_UNKNOWN"
PHARMACY_AUTHORITY_EFFECT_NON_NONE = "PHARMACY_AUTHORITY_EFFECT_NON_NONE"

RETIRED_PHANTOM_IDS = frozenset({
    "ab_syntax_error_e033d14a",
    "ab_syntax_error_4cb62bc5",
    "ab_syntax_error_bb7045c0",
})


@dataclass
class Antibody:
    """Immutable antibody entity protecting swarms against known failure modes."""

    antibody_id: str
    failure_class: str = "SyntaxAnomaly"
    target_pattern: str = ""
    constraint_type: str = "ProjectOut"
    operatorizability: str = "repairable"
    action: str = "repair"
    severity: str = "P1"
    description: str = ""
    negative_fixture: str = ""
    positive_fixture: str = ""
    times_seen: int = 1
    evidence_sha256: str = ""
    pharmacy_status: str = "candidate"
    authority_effect: str = "None"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    defect_description: str = ""
    occurrences: int = 0
    is_active: bool = False
    def __post_init__(self) -> None:
        # The status is a bare `str`, so the enum alone is advisory. Rejecting
        # unknown values here makes it load-bearing.
        if self.pharmacy_status not in {member.value for member in PharmacyStatus}:
            raise ValueError(f"{PHARMACY_STATUS_UNKNOWN}:{self.pharmacy_status!r}")
        if self.defect_description and self.pharmacy_status in {PharmacyStatus.ADMITTED.value, "admitted"}:
            raise ValueError("CANDIDATE_ONLY_UPON_CREATION: Harvested defect antibody must have CANDIDATE status")
        if self.authority_effect != "None":
            raise ValueError(
                f"{PHARMACY_AUTHORITY_EFFECT_NON_NONE}:{self.authority_effect!r}"
            )

    def record_occurrence(self) -> None:
        self.occurrences += 1
        self.times_seen += 1

    @classmethod
    def farm(
        cls,
        *,
        antibody_id: str,
        failure_class: str = "SyntaxAnomaly",
        target_pattern: str = "",
        constraint_type: str = "ProjectOut",
        operatorizability: str = "repairable",
        action: str = "repair",
        severity: str = "P1",
        description: str = "",
        negative_fixture: str = "",
        positive_fixture: str = "",
        times_seen: int = 1,
        evidence_sha256: str = "",
        defect_description: str = "",
    ) -> "Antibody":
        """Build an antibody harvested from an observed defect.

        **There is no `pharmacy_status` parameter.** Harvesting cannot express
        admission, so no caller can write a non-CANDIDATE status through this
        path. This seeder previously hardcoded ``pharmacy_status="admitted"``
        here, which let a local defect-harvesting run mint its own evidence:
        the detector fired, therefore the detector was right. Enforcement now
        lives in the signature rather than in a convention.

        Observing a defect is evidence that a detector fired. It is not evidence
        that the detector is sound, and admission is a separate human act.
        """
        if antibody_id in RETIRED_PHANTOM_IDS:
            raise ValueError(f"PARSER_BUG_PHANTOM_RETIRED: {antibody_id} has been permanently retired")

        return cls(
            antibody_id=antibody_id,
            failure_class=failure_class,
            target_pattern=target_pattern,
            constraint_type=constraint_type,
            operatorizability=operatorizability,
            action=action,
            severity=severity,
            description=description or defect_description,
            negative_fixture=negative_fixture,
            positive_fixture=positive_fixture,
            times_seen=times_seen,
            evidence_sha256=evidence_sha256,
            pharmacy_status=PharmacyStatus.CANDIDATE.value,
            authority_effect="None",
            defect_description=defect_description,
            occurrences=0,
            is_active=False,
        )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.antibody_id == other.antibody_id
            and self.failure_class == other.failure_class
            and self.target_pattern == other.target_pattern
            and self.constraint_type == other.constraint_type
            and self.operatorizability == other.operatorizability
            and self.action == other.action
            and self.severity == other.severity
            and self.description == other.description
            and self.negative_fixture == other.negative_fixture
            and self.positive_fixture == other.positive_fixture
            and self.times_seen == other.times_seen
            and self.evidence_sha256 == other.evidence_sha256
            and self.pharmacy_status == other.pharmacy_status
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.antibody_id,
                self.failure_class,
                self.target_pattern,
                self.constraint_type,
                self.operatorizability,
                self.action,
                self.severity,
                self.description,
                self.negative_fixture,
                self.positive_fixture,
                self.times_seen,
                self.evidence_sha256,
                self.pharmacy_status,
                self.authority_effect,
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
