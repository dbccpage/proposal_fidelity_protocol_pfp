"""Driven ports and immutable application results for the OEOS kernel.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ContextManager, Protocol

from ..domain import (
    CapabilitySnapshotV1,
    EncryptedArtifactRefV1,
    HarnessEventV1,
    TaskAggregateV1,
    TaskEnvelopeV1,
    TaskInvariantError,
    TaskStateV1,
    require_sha256_digest,
)


class TaskStoreError(RuntimeError):
    """Typed persistence refusal safe to cross the application boundary."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}:{message}")


class SecurityPortError(RuntimeError):
    """Typed refusal emitted by a security adapter at a driven port."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}:{message}")


class CheckoutLeaseRefusal(SecurityPortError):
    """A mutation lease could not be established or replayed safely."""


class CheckoutLeaseModeV1(str, Enum):
    READ_ONLY_NONCLAIM = "READ_ONLY_NONCLAIM"
    MUTATION_EXCLUSIVE = "MUTATION_EXCLUSIVE"


@dataclass(frozen=True, slots=True)
class CheckoutLeaseEvidenceV1:
    mode: CheckoutLeaseModeV1
    claimed: bool
    repository: str
    repository_head_sha: str
    lease_digest: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if type(self.mode) is not CheckoutLeaseModeV1:
            raise TaskInvariantError("INVALID_LEASE_EVIDENCE", "lease mode differs")
        if type(self.claimed) is not bool:
            raise TaskInvariantError("INVALID_LEASE_EVIDENCE", "claimed type differs")
        if self.claimed is not (self.mode is CheckoutLeaseModeV1.MUTATION_EXCLUSIVE):
            raise TaskInvariantError(
                "INVALID_LEASE_EVIDENCE", "claim and mode disagree"
            )
        if type(self.repository) is not str or not self.repository:
            raise TaskInvariantError("INVALID_LEASE_EVIDENCE", "repository differs")
        if (
            type(self.repository_head_sha) is not str
            or len(self.repository_head_sha) != 40
            or any(
                character not in "0123456789abcdef"
                for character in self.repository_head_sha
            )
        ):
            raise TaskInvariantError("INVALID_LEASE_EVIDENCE", "HEAD differs")
        _require_digest(self.lease_digest, "lease_digest")
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN", "lease evidence grants no authority"
            )

    def to_canonical(self) -> dict[str, object]:
        return {
            "authority_effect": self.authority_effect,
            "claimed": self.claimed,
            "lease_digest": self.lease_digest,
            "mode": self.mode.value,
            "repository": self.repository,
            "repository_head_sha": self.repository_head_sha,
        }


class CheckoutLeaseGuardPort(Protocol):
    @property
    def evidence(self) -> CheckoutLeaseEvidenceV1: ...

    def assert_held(self) -> None: ...


class CheckoutLeasePort(Protocol):
    def claim(
        self, envelope: TaskEnvelopeV1
    ) -> ContextManager[CheckoutLeaseGuardPort]: ...

    def diagnostic(self) -> dict[str, object]: ...


class KeyProtectorPort(Protocol):
    @property
    def protector_id(self) -> str: ...

    @property
    def fixture_only(self) -> bool: ...

    def protect(self, plaintext: bytes, *, entropy: bytes) -> bytes: ...

    def unprotect(self, protected: bytes, *, entropy: bytes) -> bytes: ...

    def diagnostic(self) -> dict[str, object]: ...


class EncryptedArtifactStorePort(Protocol):
    def put(
        self, payload: bytes, *, artifact_schema: str
    ) -> EncryptedArtifactRefV1: ...

    def get(self, reference: EncryptedArtifactRefV1) -> bytes: ...

    def diagnostic(self) -> dict[str, object]: ...


class ExecutionDispositionV1(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    NEEDS_INPUT = "NEEDS_INPUT"
    REFUSED = "REFUSED"
    FAILED = "FAILED"
    STATUS_UNKNOWN = "STATUS_UNKNOWN"


def _require_digest(value: object, field: str) -> None:
    require_sha256_digest(value, field)


@dataclass(frozen=True, slots=True)
class ExecutionResultV1:
    disposition: ExecutionDispositionV1
    result_digest: str
    route_plan_digest: str
    inner_receipt_digests: tuple[str, ...] = ()
    output_artifact_digests: tuple[str, ...] = ()
    finding_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.disposition) is not ExecutionDispositionV1:
            raise TaskInvariantError(
                "INVALID_EXECUTION_RESULT", "disposition type differs"
            )
        _require_digest(self.result_digest, "result_digest")
        _require_digest(self.route_plan_digest, "route_plan_digest")
        for name, values in (
            ("inner_receipt_digests", self.inner_receipt_digests),
            ("output_artifact_digests", self.output_artifact_digests),
        ):
            if type(values) is not tuple:
                raise TaskInvariantError(
                    "INVALID_EXECUTION_RESULT", f"{name} type differs"
                )
            for value in values:
                _require_digest(value, name)
            if tuple(sorted(set(values))) != values:
                raise TaskInvariantError(
                    "INVALID_EXECUTION_RESULT", f"{name} must be sorted and unique"
                )
        if type(self.finding_codes) is not tuple or any(
            type(value) is not str or not value for value in self.finding_codes
        ):
            raise TaskInvariantError("INVALID_EXECUTION_RESULT", "finding codes differ")
        if tuple(sorted(set(self.finding_codes))) != self.finding_codes:
            raise TaskInvariantError(
                "INVALID_EXECUTION_RESULT", "finding codes must be sorted and unique"
            )

    def to_canonical(self) -> dict[str, object]:
        return {
            "disposition": self.disposition.value,
            "finding_codes": list(self.finding_codes),
            "inner_receipt_digests": list(self.inner_receipt_digests),
            "output_artifact_digests": list(self.output_artifact_digests),
            "result_digest": self.result_digest,
            "route_plan_digest": self.route_plan_digest,
        }


@dataclass(frozen=True, slots=True)
class VerificationResultV1:
    accepted: bool
    verifier_id: str
    verifier_digest: str
    evidence_digest: str
    finding_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.accepted) is not bool:
            raise TaskInvariantError(
                "INVALID_VERIFICATION", "accepted must be exact bool"
            )
        if type(self.verifier_id) is not str or not self.verifier_id:
            raise TaskInvariantError("INVALID_VERIFICATION", "verifier_id differs")
        _require_digest(self.verifier_digest, "verifier_digest")
        _require_digest(self.evidence_digest, "evidence_digest")
        if type(self.finding_codes) is not tuple or any(
            type(value) is not str or not value for value in self.finding_codes
        ):
            raise TaskInvariantError("INVALID_VERIFICATION", "finding codes differ")
        if tuple(sorted(set(self.finding_codes))) != self.finding_codes:
            raise TaskInvariantError(
                "INVALID_VERIFICATION", "finding codes must be sorted and unique"
            )

    def to_canonical(self) -> dict[str, object]:
        return {
            "accepted": self.accepted,
            "evidence_digest": self.evidence_digest,
            "finding_codes": list(self.finding_codes),
            "verifier_digest": self.verifier_digest,
            "verifier_id": self.verifier_id,
        }


class CancellationProbe(Protocol):
    def is_cancellation_requested(self) -> bool: ...


class TaskExecutorPort(Protocol):
    def execute(
        self, task: TaskAggregateV1, cancellation: CancellationProbe
    ) -> ExecutionResultV1: ...

    def diagnostic(self) -> dict[str, object]: ...


class IndependentVerifierPort(Protocol):
    def verify(
        self, task: TaskAggregateV1, result: ExecutionResultV1
    ) -> VerificationResultV1: ...

    def diagnostic(self) -> dict[str, object]: ...


class CapabilitySnapshotPort(Protocol):
    def snapshot(self) -> CapabilitySnapshotV1: ...

    def diagnostic(self) -> dict[str, object]: ...


class TaskStorePort(Protocol):
    def create(self, task: TaskAggregateV1) -> tuple[TaskAggregateV1, bool]: ...

    def save(self, task: TaskAggregateV1, *, expected_version: int) -> None: ...

    def load(self, task_id: str) -> TaskAggregateV1 | None: ...

    def events(self, task_id: str) -> tuple[HarnessEventV1, ...]: ...

    def tasks_in_state(self, state: TaskStateV1) -> tuple[str, ...]: ...

    def diagnostic(self) -> dict[str, object]: ...


__all__ = [
    "CancellationProbe",
    "CapabilitySnapshotPort",
    "CheckoutLeaseEvidenceV1",
    "CheckoutLeaseGuardPort",
    "CheckoutLeaseModeV1",
    "CheckoutLeasePort",
    "CheckoutLeaseRefusal",
    "ExecutionDispositionV1",
    "ExecutionResultV1",
    "EncryptedArtifactStorePort",
    "IndependentVerifierPort",
    "KeyProtectorPort",
    "SecurityPortError",
    "TaskExecutorPort",
    "TaskStoreError",
    "TaskStorePort",
    "VerificationResultV1",
]
