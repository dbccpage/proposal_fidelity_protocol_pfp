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


PHARMACY_STATUS_SELF_ADMITTED = "PHARMACY_SELF_ADMITTED"
PHARMACY_STATUS_UNKNOWN = "PHARMACY_STATUS_UNKNOWN"
PHARMACY_AUTHORITY_EFFECT_NON_NONE = "PHARMACY_AUTHORITY_EFFECT_NON_NONE"


@dataclass(frozen=True)
class Antibody:
    antibody_id: str
    failure_class: str
    target_pattern: str
    constraint_type: str
    operatorizability: str
    action: str
    severity: str
    description: str
    negative_fixture: str
    positive_fixture: str
    times_seen: int = 1
    evidence_sha256: str = ""
    pharmacy_status: str = "candidate"
    authority_effect: str = "None"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_run_id: str = ""
    source_task_id: str = ""
    scope: dict[str, Any] | None = None
    guidance_text: str = ""
    rule_sha256: str = ""
    supersedes: str = ""
    admission: dict[str, Any] | None = None
    suspended: bool = False
    revoked: bool = False

    def __post_init__(self) -> None:
        # The status is a bare `str` on the wire, so the enum alone is advisory.
        # Rejecting unknown values here makes it load-bearing: a typo, or a
        # status invented by a future writer, fails at construction instead of
        # silently becoming a state no consumer knows how to gate on.
        if type(self.source_run_id) is not str or type(self.source_task_id) is not str:
            raise ValueError("PHARMACY_SOURCE_ID_INVALID")
        if self.pharmacy_status not in {member.value for member in PharmacyStatus}:
            raise ValueError(f"{PHARMACY_STATUS_UNKNOWN}:{self.pharmacy_status!r}")
        # The factory fences the usual path, but direct construction and
        # deserialization must not turn an observational record into authority.
        if self.authority_effect != "None":
            raise ValueError(f"{PHARMACY_AUTHORITY_EFFECT_NON_NONE}:{self.authority_effect!r}")

    @classmethod
    def farm(
        cls,
        *,
        antibody_id: str,
        failure_class: str,
        target_pattern: str,
        constraint_type: str,
        operatorizability: str,
        action: str,
        severity: str,
        description: str,
        negative_fixture: str,
        positive_fixture: str,
        times_seen: int = 1,
        evidence_sha256: str = "",
        source_run_id: str = "",
        source_task_id: str = "",
    ) -> "Antibody":
        """Build an antibody harvested from an observed defect.

        **There is no `pharmacy_status` parameter.** That is the whole point:
        harvesting cannot express admission, so no caller -- present or future,
        careful or not -- can write a non-CANDIDATE status through this path.
        Enforcement lives in the signature rather than in a convention that a
        later edit can quietly break, which is what happened the first time.

        Observing a defect is evidence that a detector fired. It is not evidence
        that the detector is sound, and admission is a separate human act.
        """
        return cls(
            antibody_id=antibody_id,
            failure_class=failure_class,
            target_pattern=target_pattern,
            constraint_type=constraint_type,
            operatorizability=operatorizability,
            action=action,
            severity=severity,
            description=description,
            negative_fixture=negative_fixture,
            positive_fixture=positive_fixture,
            times_seen=times_seen,
            evidence_sha256=evidence_sha256,
            source_run_id=source_run_id,
            source_task_id=source_task_id,
            pharmacy_status=PharmacyStatus.CANDIDATE.value,
            authority_effect="None",
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
