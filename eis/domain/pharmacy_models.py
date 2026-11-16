from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class ConstraintType(str, Enum):  # noqa: UP042
    PROJECT_OUT = "ProjectOut"
    RESTRAIN = "Restrain"
    ENFORCE = "Enforce"


class Operatorizability(str, Enum):  # noqa: UP042
    REPAIRABLE = "repairable"
    FATAL = "fatal"


class RuntimeAction(str, Enum):  # noqa: UP042
    REPAIR = "repair"
    ABORT = "abort"


class Severity(str, Enum):  # noqa: UP042
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class PharmacyStatus(str, Enum):  # noqa: UP042
    CANDIDATE = "candidate"
    PROVISIONAL = "provisional"
    ADMITTED = "admitted"
    REJECTED = "rejected"
    #: The defect this antibody guards against never existed -- the detector was
    #: wrong. Distinct from REJECTED, which judges a real defect not worth
    #: guarding. A retired antibody is named, not deleted.
    RETIRED = "retired"


VALID_ANTIBODY_SCOPES = frozenset({"prompt_line", "family", "society", "civilization"})
PHARMACY_STATUS_SELF_ADMITTED = "PHARMACY_SELF_ADMITTED"
PHARMACY_STATUS_UNKNOWN = "PHARMACY_STATUS_UNKNOWN"
PHARMACY_AUTHORITY_EFFECT_NON_NONE = "PHARMACY_AUTHORITY_EFFECT_NON_NONE"


@dataclass(frozen=True)
class LearningEvidencePreimageV1:
    """Exact byte preimage binding prompt, candidate failure, and host checker output."""

    prompt_id: str
    prompt_utf8_bytes: bytes
    candidate_reply_bytes: bytes
    failure_class: str
    failed_predicates: tuple[str, ...]
    checker_id: str
    checker_output_bytes: bytes
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if type(self.prompt_id) is not str or not self.prompt_id.strip():
            raise ValueError("PHARMACY_PROMPT_ID_REQUIRED: prompt_id must be a non-empty string")
        if type(self.prompt_utf8_bytes) is not bytes:
            raise TypeError("prompt_utf8_bytes must be exact bytes")
        if type(self.candidate_reply_bytes) is not bytes:
            raise TypeError("candidate_reply_bytes must be exact bytes")
        if type(self.checker_output_bytes) is not bytes:
            raise TypeError("checker_output_bytes must be exact bytes")
        if type(self.failure_class) is not str or not self.failure_class.strip():
            raise ValueError("failure_class must be a non-empty string")
        if type(self.checker_id) is not str or not self.checker_id.strip():
            raise ValueError("checker_id must be a non-empty string")
        predicates = tuple(str(p) for p in self.failed_predicates)
        object.__setattr__(self, "failed_predicates", predicates)
        if not self.checker_output_bytes and not predicates:
            raise ValueError("MISSING_HOST_REPRODUCTION: checker_output_bytes or failed_predicates required")
        if self.authority_effect != "None":
            raise ValueError(f"{PHARMACY_AUTHORITY_EFFECT_NON_NONE}:{self.authority_effect!r}")


def compute_learning_evidence_sha256(preimage: LearningEvidencePreimageV1) -> str:
    """Hash exact prompt bytes, candidate failure bytes, and host checker output bytes."""
    if type(preimage) is not LearningEvidencePreimageV1:
        raise TypeError("preimage must be an exact LearningEvidencePreimageV1")
    payload = {
        "candidate_reply_b64": base64.b64encode(preimage.candidate_reply_bytes).decode("ascii"),
        "candidate_reply_sha256": hashlib.sha256(preimage.candidate_reply_bytes).hexdigest(),
        "checker_id": preimage.checker_id,
        "checker_output_b64": base64.b64encode(preimage.checker_output_bytes).decode("ascii"),
        "checker_output_sha256": hashlib.sha256(preimage.checker_output_bytes).hexdigest(),
        "failed_predicates": sorted(preimage.failed_predicates),
        "failure_class": preimage.failure_class,
        "prompt_b64": base64.b64encode(preimage.prompt_utf8_bytes).decode("ascii"),
        "prompt_id": preimage.prompt_id,
        "prompt_sha256": hashlib.sha256(preimage.prompt_utf8_bytes).hexdigest(),
        "schema": "pfp.eis.learning_evidence.v1",
    }
    raw = (
        b"pfp.eis.learning_evidence.v1\x00"
        + json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    )
    return hashlib.sha256(raw).hexdigest()


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
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    source_run_id: str = ""
    source_task_id: str = ""
    scope: dict[str, Any] | None = None
    guidance_text: str = ""
    rule_sha256: str = ""
    supersedes: str = ""
    admission: dict[str, Any] | None = None
    suspended: bool = False
    revoked: bool = False
    source_prompt_id: str | None = None
    scope_level: str = "prompt_line"
    family_id: str | None = None
    society_id: str | None = None
    civilization_id: str | None = None
    thymus_receipt_sha256: str | None = None
    producer_actor: str = ""

    def __post_init__(self) -> None:
        # The status is a bare `str` on the wire, so the enum alone is advisory.
        # Rejecting unknown values here makes it load-bearing: a typo, or a
        # status invented by a future writer, fails at construction instead of
        # silently becoming a state no consumer knows how to gate on.
        if type(self.source_run_id) is not str or type(self.source_task_id) is not str:
            raise ValueError("PHARMACY_SOURCE_ID_INVALID")
        if self.pharmacy_status not in {member.value for member in PharmacyStatus}:
            raise ValueError(f"{PHARMACY_STATUS_UNKNOWN}:{self.pharmacy_status!r}")
        if self.scope_level not in VALID_ANTIBODY_SCOPES:
            raise ValueError(f"PHARMACY_SCOPE_LEVEL_INVALID:{self.scope_level!r}")
        for attr in (
            "source_prompt_id",
            "family_id",
            "society_id",
            "civilization_id",
            "thymus_receipt_sha256",
        ):
            val = getattr(self, attr)
            if val is not None and type(val) is not str:
                raise ValueError(f"PHARMACY_FIELD_TYPE_INVALID:{attr}")
        if type(self.producer_actor) is not str:
            raise ValueError("PHARMACY_FIELD_TYPE_INVALID:producer_actor")
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
        source_prompt_id: str | None = None,
        scope_level: str = "prompt_line",
        family_id: str | None = None,
        society_id: str | None = None,
        civilization_id: str | None = None,
        producer_actor: str = "",
        guidance_text: str = "",
        scope: dict[str, Any] | None = None,
        rule_sha256: str = "",
    ) -> Antibody:
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
            source_prompt_id=source_prompt_id,
            scope_level=scope_level,
            family_id=family_id,
            society_id=society_id,
            civilization_id=civilization_id,
            producer_actor=producer_actor,
            guidance_text=guidance_text,
            scope=scope,
            rule_sha256=rule_sha256,
            pharmacy_status=PharmacyStatus.CANDIDATE.value,
            authority_effect="None",
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
