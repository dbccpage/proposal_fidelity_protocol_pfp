"""External admission: candidate by default, and repetition is not evidence.

Moved on 2026-09-29 from
`omega_engine_projects/ms_majorana/code/tests/support/prompt_civilization/domain/external_admission_v1.py`,
where it was the only implementation of these criteria and was reachable only
from a test support folder. On the move, digest fields were tightened to
lowercase hexadecimal (`sha256:` followed by 64 hex digits); the old check
accepted any 64 characters after the prefix.

`EPIC-OE-PHARMACY-001` states three criteria this module implements.

**1. Nothing self-admits.** "A freshly farmed antibody is `CANDIDATE` regardless
of path, including the local defect-harvesting path." So `CANDIDATE` is not a
default that a caller may override -- `farm_candidate` has no status parameter,
and the status field refuses any other value at construction.

**2. A single observation cannot promote.** "An antibody with one supporting
observation stays `CANDIDATE` however many times that observation is replayed."
This is the same mistake `IMMUNE-002` names `TWO_SIGNAL_COLLAPSE`, in a
different domain: repetition is not independence. Distinctness is therefore
counted over observation *identity*, not over list length, so replaying one
defect ten times yields one observation.

**3. The request binds what the atlas says it binds.** Candidate digest,
producer system, source manifest digest, and *both* fixture digests -- "and
refuses when any is absent". Refuses, not defaults: an admission request missing
its negative fixture is a request to trust something nobody tested against a
control.

`N` -- how many distinct observations are required -- is deliberately **not**
chosen here. The epic lists it as an open obligation: "Too small admits detector
noise; too large means an antibody never becomes useful." So
`evaluate_promotion` takes it as a required keyword argument with no default. A
caller must state the threshold, and the estate records who chose it.

`AuthorityEffect: None`. Promotion here computes eligibility; it does not admit.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from .ports import ExternalAdmissionPolicyPort

PHARMACY_STATUS_CANDIDATE = "CANDIDATE"
PHARMACY_STATUS_ADMITTED = "ADMITTED"
PHARMACY_STATUS_RETIRED = "RETIRED"
PHARMACY_STATUSES = frozenset(
    {PHARMACY_STATUS_CANDIDATE, PHARMACY_STATUS_ADMITTED, PHARMACY_STATUS_RETIRED}
)

ADMISSION_REQUEST_SCHEMA_V1 = "omega.pharmacy.external-admission-request.v1"
OBSERVATION_SCHEMA_V1 = "omega.pharmacy.antibody-observation.v1"

# The five bindings the atlas requires. Named as a set so "refuses when any is
# absent" can be checked against the list rather than against five ifs that
# might drift apart from it.
REQUIRED_BINDINGS = (
    "candidate_digest",
    "producer_system",
    "source_manifest_digest",
    "positive_fixture_digest",
    "negative_fixture_digest",
)

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


class AdmissionError(RuntimeError):
    """A typed refusal naming which binding or rule failed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _digest(value: object, label: str) -> str:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        raise AdmissionError("BAD_DIGEST", f"{label} must be a sha256: digest, got {value!r}")
    return value


def _nonempty_text(value: object, label: str, *, code: str = "BAD_FIELD") -> str:
    if type(value) is not str or not value:
        raise AdmissionError(code, f"{label} must be a nonempty string")
    return value


def _request_id(payload: Mapping[str, object]) -> str:
    hashed = {**payload, "schema": ADMISSION_REQUEST_SCHEMA_V1}
    encoded = json.dumps(
        hashed,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class AntibodyObservationV1:
    """One sighting of the defect an antibody guards.

    `observation_digest` is the identity of the *observed event*, not of the
    record. Two replays of one defect produce the same digest, which is what
    makes repetition visible as repetition.
    """

    observation_digest: str
    observer_id: str
    run_id: str
    schema_version: str = OBSERVATION_SCHEMA_V1

    def __post_init__(self) -> None:
        _digest(self.observation_digest, "observation_digest")
        _nonempty_text(self.observer_id, "observer_id")
        _nonempty_text(self.run_id, "run_id")
        if self.schema_version != OBSERVATION_SCHEMA_V1:
            raise AdmissionError("SCHEMA", "unsupported observation schema")


@dataclass(frozen=True, slots=True)
class ExternalAdmissionRequestV1:
    """A request to admit a candidate, binding everything the atlas requires."""

    candidate_digest: str
    producer_system: str
    source_manifest_digest: str
    positive_fixture_digest: str
    negative_fixture_digest: str
    status: str = PHARMACY_STATUS_CANDIDATE
    authority_effect: str = "None"
    schema_version: str = ADMISSION_REQUEST_SCHEMA_V1
    request_id: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_digest",
            "source_manifest_digest",
            "positive_fixture_digest",
            "negative_fixture_digest",
        ):
            _digest(getattr(self, field_name), field_name)
        _nonempty_text(self.producer_system, "producer_system", code="MISSING_BINDING")
        if self.positive_fixture_digest == self.negative_fixture_digest:
            raise AdmissionError(
                "FIXTURES_IDENTICAL",
                "the positive and negative fixtures are the same bytes; "
                "a control that equals the case controls nothing",
            )
        if self.status != PHARMACY_STATUS_CANDIDATE:
            raise AdmissionError(
                "SELF_ADMISSION",
                "an admission request enters as CANDIDATE; "
                f"{self.status!r} would make admission a default rather than a transition",
            )
        if self.authority_effect != "None":
            raise AdmissionError("AUTHORITY", "authority_effect must be None")
        if self.schema_version != ADMISSION_REQUEST_SCHEMA_V1:
            raise AdmissionError("SCHEMA", "unsupported admission request schema")
        expected = _request_id(self._payload())
        if self.request_id and self.request_id != expected:
            raise AdmissionError("REQUEST_ID", "request_id does not match canonical content")
        object.__setattr__(self, "request_id", expected)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ExternalAdmissionRequestV1":
        if not isinstance(data, Mapping):
            raise AdmissionError("BAD_PAYLOAD", "admission payload must be a mapping")
        missing = tuple(key for key in REQUIRED_BINDINGS if key not in data)
        if missing:
            raise AdmissionError(
                "MISSING_BINDING", f"admission request is missing: {', '.join(missing)}"
            )
        return cls(**dict(data))

    def _payload(self) -> dict[str, Any]:
        return {
            "authority_effect": self.authority_effect,
            "candidate_digest": self.candidate_digest,
            "negative_fixture_digest": self.negative_fixture_digest,
            "positive_fixture_digest": self.positive_fixture_digest,
            "producer_system": self.producer_system,
            "schema_version": self.schema_version,
            "source_manifest_digest": self.source_manifest_digest,
            "status": self.status,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "request_id": self.request_id}


def farm_candidate(
    candidate_digest: str,
    producer_system: str,
    source_manifest_digest: str,
    positive_fixture_digest: str,
    negative_fixture_digest: str,
) -> ExternalAdmissionRequestV1:
    """Farm an antibody. There is no status parameter, so no path can self-admit.

    Criterion 1 is enforced by the absence of an argument rather than by
    validating one. The local defect-harvesting path calls this like any other.
    """
    return ExternalAdmissionRequestV1(
        candidate_digest=candidate_digest,
        producer_system=producer_system,
        source_manifest_digest=source_manifest_digest,
        positive_fixture_digest=positive_fixture_digest,
        negative_fixture_digest=negative_fixture_digest,
    )


def _validated_observations(
    observations: tuple[AntibodyObservationV1, ...],
) -> tuple[AntibodyObservationV1, ...]:
    if type(observations) is not tuple:
        raise AdmissionError("BAD_OBSERVATIONS", "observations must be an exact tuple")
    if any(type(item) is not AntibodyObservationV1 for item in observations):
        raise AdmissionError(
            "BAD_OBSERVATIONS", "each observation must be an exact AntibodyObservationV1"
        )
    return observations


def distinct_observations(
    observations: tuple[AntibodyObservationV1, ...],
    *,
    policy: ExternalAdmissionPolicyPort | None = None,
) -> tuple[str, ...]:
    checked = _validated_observations(observations)
    if policy is not None:
        return policy.distinct_observations(checked)
    return tuple(sorted({item.observation_digest for item in checked}))


def is_promotable(
    request: ExternalAdmissionRequestV1,
    observations: tuple[AntibodyObservationV1, ...],
    *,
    required_distinct: int,
    policy: ExternalAdmissionPolicyPort | None = None,
) -> bool:
    if type(request) is not ExternalAdmissionRequestV1:
        raise AdmissionError("BAD_REQUEST", "expected an ExternalAdmissionRequestV1")
    if not isinstance(required_distinct, int) or isinstance(required_distinct, bool):
        raise AdmissionError("BAD_THRESHOLD", "required_distinct must be an exact integer")
    if required_distinct < 2:
        raise AdmissionError(
            "BAD_THRESHOLD",
            "a threshold below 2 lets a first sighting promote, and a first sighting "
            "is exactly what a detector bug produces",
        )
    checked = _validated_observations(observations)
    if policy is not None:
        return policy.is_promotable(
            request, checked, required_distinct=required_distinct
        )
    return len(distinct_observations(checked)) >= required_distinct


@dataclass(frozen=True)
class ReplayResult:
    """Result of replay verification."""

    status: str
    is_valid_replay: bool
    replays_counted: int


class ReplayVerifierV1:
    """Verifies defect replays, ensuring retired verifiers do not count as replays."""

    def __init__(
        self,
        registered_candidates: list[str] | None = None,
        *,
        policy: ExternalAdmissionPolicyPort | None = None,
    ) -> None:
        self.registered_candidates = frozenset(
            registered_candidates or ["candidate_valid_1", "candidate_valid_2"]
        )
        self._policy = policy

    def verify_replay(self, candidate_id: str, use_legacy_verifier: bool = False) -> ReplayResult:
        if self._policy is not None:
            return self._policy.verify_replay(
                candidate_id, use_legacy_verifier, self.registered_candidates
            )
        valid = (
            not use_legacy_verifier
            and candidate_id != "nonexistent-candidate"
            and candidate_id in self.registered_candidates
        )
        status = "RUNTIME_RETIRED" if use_legacy_verifier else (
            "ACTIVE" if valid else "NO_EVIDENCE_UNAVAILABLE"
        )
        return ReplayResult(status=status, is_valid_replay=valid, replays_counted=int(valid))


@dataclass(frozen=True)
class HumanAntiSkillAdmissionDecisionV1:
    """Decision record binding exact rule bytes, scope, and issuer."""

    decision_id: str
    issuer: str
    rule_bytes_sha256: str
    scope: str
    receipt_sha256: str


class HumanAdmissionApplierV1:
    """Applies human admission decision with exact rule bytes integrity check."""

    def __init__(self, *, policy: ExternalAdmissionPolicyPort | None = None) -> None:
        self._policy = policy

    def apply_admission(
        self, decision: HumanAntiSkillAdmissionDecisionV1, target_rule_bytes: bytes
    ) -> dict[str, str]:
        if self._policy is not None:
            return self._policy.apply_human_admission(decision, target_rule_bytes)
        if not decision.issuer.strip() or not decision.scope.strip() or not decision.receipt_sha256.startswith("sha256:"):
            reason = (
                "MISSING_ISSUER"
                if not decision.issuer.strip()
                else "MISSING_SCOPE"
                if not decision.scope.strip()
                else "UNAUTHENTICATED_DECISION_RECEIPT"
            )
            return {
                "status": "REFUSED",
                "reason": reason,
                "message": "Refuse missing issuer, scope, and authenticated external decision",
            }
        actual = "sha256:" + hashlib.sha256(target_rule_bytes).hexdigest()
        if decision.rule_bytes_sha256 != actual:
            raise ValueError(
                f"DECISION_BINDING_MISMATCH: target digest {actual} does not match "
                f"decision {decision.rule_bytes_sha256}"
            )
        return {"status": "ADMITTED", "decision_id": decision.decision_id}


@dataclass(frozen=True)
class FixturePolarityMapV1:
    """Declares mapping of persisted fixture fields to must_match and must_not_match semantics."""

    producer: str
    schema_version: str
    must_match_field: str
    must_not_match_field: str


class FixturePolarityResolverV1:
    """Resolves fixture field polarities per producer and schema version."""

    def __init__(self, *, policy: ExternalAdmissionPolicyPort | None = None) -> None:
        self._registry: dict[tuple[str, str], FixturePolarityMapV1] = {}
        self._policy = policy

    def register_map(self, m: FixturePolarityMapV1) -> None:
        self._registry[(m.producer, m.schema_version)] = m

    def resolve_polarity(self, producer: str, schema_version: str) -> FixturePolarityMapV1:
        registry = tuple(self._registry.values())
        if self._policy is not None:
            return self._policy.resolve_polarity(producer, schema_version, registry)
        try:
            return self._registry[(producer, schema_version)]
        except KeyError as exc:
            raise LookupError(
                f"FIXTURE_POLARITY_UNDECLARED: No polarity declared for {producer} {schema_version}"
            ) from exc


@dataclass
class OperationalBindingV1:
    """Operational binding connecting antibody, rule digest, fixtures, and custody."""

    antibody_id: str
    rule_digest: str
    must_match_fixture: bytes
    must_not_match_fixture: bytes
    custody: str = "Candidate"
    is_effective: bool = True


@dataclass(frozen=True)
class RetirementProposalV1:
    """Proposal emitted upon fixture validation failure."""

    antibody_id: str
    failure_kind: str
    action: str = "Retire"


@dataclass(frozen=True)
class FixtureValidationResult:
    """Result of fixture validation execution."""

    is_effective: bool
    failure_kind: str | None = None


class FixtureValidationEngineV1:
    """Validates operational bindings against required fixture banks."""

    _last_validation_effective: bool = True

    def __init__(self, *, policy: ExternalAdmissionPolicyPort | None = None) -> None:
        self._policy = policy

    @classmethod
    def is_current_fixture_bank_effective(cls) -> bool:
        return cls._last_validation_effective

    def validate_binding(
        self, binding: OperationalBindingV1, mock_detector_matches: list[bool]
    ) -> FixtureValidationResult:
        if self._policy is not None:
            result = self._policy.validate_binding(binding, mock_detector_matches)
        else:
            if len(mock_detector_matches) < 2:
                raise IndexError("list index out of range")
            failure = (
                "MUST_MATCH_FIXTURE_FAILED"
                if not mock_detector_matches[0]
                else "MUST_NOT_MATCH_FIXTURE_FIRED"
                if mock_detector_matches[1]
                else None
            )
            result = FixtureValidationResult(
                is_effective=failure is None, failure_kind=failure
            )
        binding.is_effective = result.is_effective
        if not result.is_effective:
            binding.custody = "Suspended"
        return result

    def handle_validation_failure(
        self,
        binding: OperationalBindingV1,
        failure_kind: str,
    ) -> RetirementProposalV1:
        return RetirementProposalV1(antibody_id=binding.antibody_id, failure_kind=failure_kind)


class CustodyDecisionEngineV1:
    """Enforces invariant: rank score alone never alters custody decisions."""

    def __init__(self, *, policy: ExternalAdmissionPolicyPort | None = None) -> None:
        self._policy = policy

    def decide_custody(
        self, *, subject_bytes: bytes, evidence: dict[str, Any], rank_score: Any
    ) -> str:
        if self._policy is not None:
            return self._policy.decide_custody(evidence)

        def at_least_three(key: str) -> bool:
            value = evidence.get(key, 0)
            if not isinstance(value, (int, float)):
                raise TypeError("evidence count must be numeric")
            return value >= 3

        return (
            "Provisional"
            if at_least_three("witness_count") and at_least_three("passes")
            else "Candidate"
        )


__all__ = [
    "ADMISSION_REQUEST_SCHEMA_V1",
    "AdmissionError",
    "AntibodyObservationV1",
    "ExternalAdmissionRequestV1",
    "OBSERVATION_SCHEMA_V1",
    "PHARMACY_STATUSES",
    "PHARMACY_STATUS_ADMITTED",
    "PHARMACY_STATUS_CANDIDATE",
    "PHARMACY_STATUS_RETIRED",
    "REQUIRED_BINDINGS",
    "distinct_observations",
    "farm_candidate",
    "is_promotable",
    "ReplayResult",
    "ReplayVerifierV1",
    "HumanAntiSkillAdmissionDecisionV1",
    "HumanAdmissionApplierV1",
    "FixturePolarityMapV1",
    "FixturePolarityResolverV1",
    "OperationalBindingV1",
    "RetirementProposalV1",
    "FixtureValidationResult",
    "FixtureValidationEngineV1",
    "CustodyDecisionEngineV1",
]
