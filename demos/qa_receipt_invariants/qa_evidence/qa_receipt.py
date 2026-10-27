"""Domain value objects for SoftwareQaReceiptV1 and strict-inspector evidence.

AuthorityEffect: Strictly 'None'
Governance: exact-type value-object equality.

hashlib and json stay in the domain because the receipt content digest is an
invariant of the sealed receipt, not an infrastructure adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Optional, Tuple

from qa_evidence.result import Err


class StrictVetoStatus(str, Enum):
    """Veto verdict of the strict inspector static and dynamic audit."""
    CLEAN = "CLEAN"
    VETOED = "VETOED"
    BLOCKED = "BLOCKED"


class ReceiptStatus(str, Enum):
    """Overall status of the Software QA Receipt."""
    PASSED = "PASSED"
    REFUSED = "REFUSED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class MutationRollbackFailure:
    """Typed failure: restored bytes do not match the baseline SHA-256."""

    message: str

    def __post_init__(self) -> None:
        if type(self.message) is not str or not self.message:
            raise ValueError("message must be a non-empty string")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, MutationRollbackFailure):
            return False
        return self.message == other.message

    def __hash__(self) -> int:
        return hash((type(self), self.message))


@dataclass(frozen=True)
class MutationJournalFailure:
    """Typed failure: mutation journal is corrupt, tampered, or incomplete."""

    message: str

    def __post_init__(self) -> None:
        if type(self.message) is not str or not self.message:
            raise ValueError("message must be a non-empty string")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, MutationJournalFailure):
            return False
        return self.message == other.message

    def __hash__(self) -> int:
        return hash((type(self), self.message))


@dataclass(frozen=True)
class MutationNotKilledFailure:
    """Typed failure: an applied production mutant survived its witness."""

    message: str

    def __post_init__(self) -> None:
        if type(self.message) is not str or not self.message:
            raise ValueError("message must be a non-empty string")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, MutationNotKilledFailure):
            return False
        return self.message == other.message

    def __hash__(self) -> int:
        return hash((type(self), self.message))


class MutationRollbackError(RuntimeError):
    """Edge exception for a rollback digest mismatch. Prefer refuse_mutation_rollback."""

    def __init__(self, message: str) -> None:
        self.failure = MutationRollbackFailure(message)
        super().__init__(self.failure.message)


class MutationJournalError(RuntimeError):
    """Edge exception for a corrupt mutation journal. Prefer refuse_mutation_journal."""

    def __init__(self, message: str) -> None:
        self.failure = MutationJournalFailure(message)
        super().__init__(self.failure.message)


class MutationNotKilledVeto(RuntimeError):
    """Edge exception when a mutant is not killed. Prefer refuse_mutation_not_killed."""

    def __init__(self, message: str) -> None:
        self.failure = MutationNotKilledFailure(message)
        super().__init__(self.failure.message)


def refuse_mutation_rollback(message: str) -> Err[MutationRollbackFailure]:
    """Return the rollback failure without using the exception as control flow."""
    return Err(MutationRollbackFailure(message))


def refuse_mutation_journal(message: str) -> Err[MutationJournalFailure]:
    """Return the journal failure without using the exception as control flow."""
    return Err(MutationJournalFailure(message))


def refuse_mutation_not_killed(message: str) -> Err[MutationNotKilledFailure]:
    """Return the survived-mutant failure without using the exception as control flow."""
    return Err(MutationNotKilledFailure(message))


def _canonical_json_bytes(data: object) -> bytes:
    """Serialize data with the receipt's deterministic sorted-key JSON profile."""
    return json.dumps(
        data,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


@dataclass(frozen=True)
class StrictAuditSummary:
    """Findings from strict inspector static AST and byte-level inspection."""
    strict_veto_status: StrictVetoStatus
    class_0_mock_ornaments_detected: int
    silent_skips_detected: int
    bare_returns_detected: int
    blanket_exceptions_detected: int
    ast_boundary_violations: int
    auto_repair_rounds_used: int
    veto_reasons: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if type(self.class_0_mock_ornaments_detected) is not int or self.class_0_mock_ornaments_detected < 0:
            raise ValueError("class_0_mock_ornaments_detected must be a non-negative int")
        if type(self.silent_skips_detected) is not int or self.silent_skips_detected < 0:
            raise ValueError("silent_skips_detected must be a non-negative int")
        if type(self.bare_returns_detected) is not int or self.bare_returns_detected < 0:
            raise ValueError("bare_returns_detected must be a non-negative int")
        if type(self.blanket_exceptions_detected) is not int or self.blanket_exceptions_detected < 0:
            raise ValueError("blanket_exceptions_detected must be a non-negative int")
        if type(self.ast_boundary_violations) is not int or self.ast_boundary_violations < 0:
            raise ValueError("ast_boundary_violations must be a non-negative int")
        if type(self.auto_repair_rounds_used) is not int or self.auto_repair_rounds_used < 0:
            raise ValueError("auto_repair_rounds_used must be a non-negative int")
        if self.auto_repair_rounds_used > 3:
            raise ValueError(f"auto_repair_rounds_used cannot exceed 3, got {self.auto_repair_rounds_used}")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, StrictAuditSummary):
            return False
        return (
            self.strict_veto_status == other.strict_veto_status
            and self.class_0_mock_ornaments_detected == other.class_0_mock_ornaments_detected
            and self.silent_skips_detected == other.silent_skips_detected
            and self.bare_returns_detected == other.bare_returns_detected
            and self.blanket_exceptions_detected == other.blanket_exceptions_detected
            and self.ast_boundary_violations == other.ast_boundary_violations
            and self.auto_repair_rounds_used == other.auto_repair_rounds_used
            and self.veto_reasons == other.veto_reasons
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.strict_veto_status,
            self.class_0_mock_ornaments_detected,
            self.silent_skips_detected,
            self.bare_returns_detected,
            self.blanket_exceptions_detected,
            self.ast_boundary_violations,
            self.auto_repair_rounds_used,
            self.veto_reasons,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "ast_boundary_violations": self.ast_boundary_violations,
            "auto_repair_rounds_used": self.auto_repair_rounds_used,
            "bare_returns_detected": self.bare_returns_detected,
            "blanket_exceptions_detected": self.blanket_exceptions_detected,
            "class_0_mock_ornaments_detected": self.class_0_mock_ornaments_detected,
            "silent_skips_detected": self.silent_skips_detected,
            "strict_veto_status": self.strict_veto_status.value,
            "veto_reasons": list(self.veto_reasons),
        }


@dataclass(frozen=True)
class ExaminerTestRecord:
    """Execution record for an individual Examiner Class 1-5 test."""
    test_node_id: str
    examiner_class: int  # 1..5; Class 0 is strictly forbidden
    classification_name: str  # e.g. "Invariant", "Negative Matrix", "Pinned Digest", "Golden Vector", "Mutation Target"
    status: str  # "PASSED", "FAILED"
    duration_ms: float
    detail: str = ""

    def __post_init__(self) -> None:
        if type(self.test_node_id) is not str or not self.test_node_id:
            raise ValueError("test_node_id must be a non-empty string")
        if type(self.examiner_class) is not int or self.examiner_class not in (1, 2, 3, 4, 5):
            raise ValueError(f"examiner_class must be in 1..5 (Class 0 strictly forbidden), got {self.examiner_class}")
        if type(self.classification_name) is not str or not self.classification_name:
            raise ValueError("classification_name must be a non-empty string")
        if type(self.status) is not str or not self.status:
            raise ValueError("status must be a non-empty string")
        if not isinstance(self.duration_ms, (int, float)) or self.duration_ms < 0:
            raise ValueError("duration_ms must be a non-negative float")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, ExaminerTestRecord):
            return False
        return (
            self.test_node_id == other.test_node_id
            and self.examiner_class == other.examiner_class
            and self.classification_name == other.classification_name
            and self.status == other.status
            and round(self.duration_ms, 2) == round(other.duration_ms, 2)
            and self.detail == other.detail
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.test_node_id,
            self.examiner_class,
            self.classification_name,
            self.status,
            round(self.duration_ms, 2),
            self.detail,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "classification_name": self.classification_name,
            "detail": self.detail,
            "duration_ms": round(self.duration_ms, 2),
            "examiner_class": self.examiner_class,
            "status": self.status,
            "test_node_id": self.test_node_id,
        }


@dataclass(frozen=True)
class MutationEvidenceRecord:
    """5-field custody record for one production code mutation."""
    mutant_id: str
    intent: str
    target: str
    anchor: str
    applied: str
    expectation: str  # "killed", "equivalent"
    status: str  # "killed", "survived", "equivalent", "ANCHOR", "RESTORE"
    failures: Tuple[str, ...] = field(default_factory=tuple)
    tests_run: Tuple[str, ...] = field(default_factory=tuple)
    restored: bool = True
    detail: str = ""

    def __post_init__(self) -> None:
        if type(self.mutant_id) is not str or not self.mutant_id:
            raise ValueError("mutant_id must be a non-empty string")
        if type(self.target) is not str or not self.target:
            raise ValueError("target must be a non-empty string")
        if type(self.anchor) is not str or not self.anchor:
            raise ValueError("anchor must be a non-empty string")
        if type(self.applied) is not str:
            raise TypeError("applied must be a string")
        if type(self.expectation) is not str:
            raise TypeError("expectation must be a string")
        if type(self.status) is not str:
            raise TypeError("status must be a string")
        if type(self.restored) is not bool:
            raise TypeError("restored must be an exact bool")

    @property
    def counts_toward_denominator(self) -> bool:
        return self.status in {"killed", "survived", "equivalent"}

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, MutationEvidenceRecord):
            return False
        return (
            self.mutant_id == other.mutant_id
            and self.intent == other.intent
            and self.target == other.target
            and self.anchor == other.anchor
            and self.applied == other.applied
            and self.expectation == other.expectation
            and self.status == other.status
            and self.failures == other.failures
            and self.tests_run == other.tests_run
            and self.restored == other.restored
            and self.detail == other.detail
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.mutant_id,
            self.intent,
            self.target,
            self.anchor,
            self.applied,
            self.expectation,
            self.status,
            self.failures,
            self.tests_run,
            self.restored,
            self.detail,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "anchor": self.anchor,
            "applied": self.applied,
            "detail": self.detail,
            "expectation": self.expectation,
            "failures": list(self.failures),
            "intent": self.intent,
            "mutant_id": self.mutant_id,
            "restored": self.restored,
            "status": self.status,
            "target": self.target,
            "tests_run": list(self.tests_run),
        }


@dataclass(frozen=True)
class RedGreenTransition:
    """Record verifying RED transition upon mutation and GREEN upon restoration."""
    mutant_id: str
    baseline_passed: bool
    mutated_failed: bool
    restored_passed: bool
    witness_tests_fired: Tuple[str, ...]
    digest_before: str
    digest_mutated: str
    digest_restored: str

    def __post_init__(self) -> None:
        if type(self.mutant_id) is not str or not self.mutant_id:
            raise ValueError("mutant_id must be a non-empty string")
        if (
            type(self.baseline_passed) is not bool
            or type(self.mutated_failed) is not bool
            or type(self.restored_passed) is not bool
        ):
            raise TypeError("transition booleans must be exact bool")
        if not (self.digest_before and self.digest_mutated and self.digest_restored):
            raise ValueError("digests must be non-empty SHA-256 strings")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, RedGreenTransition):
            return False
        return (
            self.mutant_id == other.mutant_id
            and self.baseline_passed == other.baseline_passed
            and self.mutated_failed == other.mutated_failed
            and self.restored_passed == other.restored_passed
            and self.witness_tests_fired == other.witness_tests_fired
            and self.digest_before == other.digest_before
            and self.digest_mutated == other.digest_mutated
            and self.digest_restored == other.digest_restored
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.mutant_id,
            self.baseline_passed,
            self.mutated_failed,
            self.restored_passed,
            self.witness_tests_fired,
            self.digest_before,
            self.digest_mutated,
            self.digest_restored,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "baseline_passed": self.baseline_passed,
            "digest_before": self.digest_before,
            "digest_mutated": self.digest_mutated,
            "digest_restored": self.digest_restored,
            "mutant_id": self.mutant_id,
            "mutated_failed": self.mutated_failed,
            "restored_passed": self.restored_passed,
            "witness_tests_fired": list(self.witness_tests_fired),
        }


@dataclass(frozen=True)
class SoftwareQaReceiptV1:
    """Scope-bound QA receipt recording test discrimination and gate findings.

    AuthorityEffect: Strictly 'None'.
    Schema: core.software-qa-receipt.v1
    """
    receipt_id: str
    timestamp: str  # ISO-8601 UTC
    commit_sha: str
    tree_dirty: bool
    target_scopes: Tuple[str, ...]
    status: ReceiptStatus
    strict_audit: StrictAuditSummary
    examiner_tests: Tuple[ExaminerTestRecord, ...]
    mutations: Tuple[MutationEvidenceRecord, ...]
    red_green_transitions: Tuple[RedGreenTransition, ...]
    tree_state_sha256: str
    schema_version: str = "core.software-qa-receipt.v1"
    authority_effect: str = "None"
    receipt_content_sha256: str = ""

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("authority_effect must strictly be 'None'")
        if self.schema_version != "core.software-qa-receipt.v1":
            raise ValueError(f"Invalid schema_version: {self.schema_version}")
        if type(self.receipt_id) is not str or not self.receipt_id:
            raise ValueError("receipt_id must be a non-empty string")
        if type(self.commit_sha) is not str:
            raise TypeError("commit_sha must be a string")
        if type(self.tree_dirty) is not bool:
            raise TypeError("tree_dirty must be an exact bool")
        if self.strict_audit.strict_veto_status != StrictVetoStatus.CLEAN and self.status == ReceiptStatus.PASSED:
            raise ValueError("status cannot be PASSED when strict_veto_status is not CLEAN")

    def _content_payload(self) -> dict[str, object]:
        return {
            "authority_effect": self.authority_effect,
            "commit_sha": self.commit_sha,
            "examiner_tests": [t.to_dict() for t in sorted(self.examiner_tests, key=lambda t: t.test_node_id)],
            "mutations": [m.to_dict() for m in sorted(self.mutations, key=lambda m: m.mutant_id)],
            "receipt_id": self.receipt_id,
            "red_green_transitions": [r.to_dict() for r in sorted(self.red_green_transitions, key=lambda r: r.mutant_id)],
            "schema_version": self.schema_version,
            "strict_audit": self.strict_audit.to_dict(),
            "status": self.status.value,
            "target_scopes": list(self.target_scopes),
            "timestamp": self.timestamp,
            "tree_dirty": self.tree_dirty,
            "tree_state_sha256": self.tree_state_sha256,
        }

    def compute_content_sha256(self) -> str:
        """Compute the SHA-256 digest of the deterministic receipt payload."""
        payload_bytes = _canonical_json_bytes(self._content_payload())
        return hashlib.sha256(payload_bytes).hexdigest()

    def to_dict(self) -> dict[str, object]:
        """Convert receipt to canonical dict including content hash."""
        d = self._content_payload()
        content_hash = self.receipt_content_sha256 or self.compute_content_sha256()
        d["receipt_content_sha256"] = content_hash
        return d

    def to_canonical_json(self) -> str:
        """Serialize the receipt with its deterministic sorted-key JSON profile."""
        return _canonical_json_bytes(self.to_dict()).decode("utf-8")

    def verify_integrity(self) -> Tuple[bool, Optional[str]]:
        """Verify internal cryptographic binding of receipt."""
        expected = self.compute_content_sha256()
        if not self.receipt_content_sha256:
            return False, "receipt_content_sha256 is empty"
        if self.receipt_content_sha256 != expected:
            return False, f"Digest mismatch: declared={self.receipt_content_sha256} vs computed={expected}"
        return True, None

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, SoftwareQaReceiptV1):
            return False
        return (
            self.receipt_id == other.receipt_id
            and self.schema_version == other.schema_version
            and self.timestamp == other.timestamp
            and self.commit_sha == other.commit_sha
            and self.tree_dirty == other.tree_dirty
            and self.authority_effect == other.authority_effect
            and self.target_scopes == other.target_scopes
            and self.status == other.status
            and self.strict_audit == other.strict_audit
            and self.examiner_tests == other.examiner_tests
            and self.mutations == other.mutations
            and self.red_green_transitions == other.red_green_transitions
            and self.tree_state_sha256 == other.tree_state_sha256
            and self.receipt_content_sha256 == other.receipt_content_sha256
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.receipt_id,
            self.schema_version,
            self.timestamp,
            self.commit_sha,
            self.tree_dirty,
            self.authority_effect,
            self.target_scopes,
            self.status,
            self.strict_audit,
            self.examiner_tests,
            self.mutations,
            self.red_green_transitions,
            self.tree_state_sha256,
            self.receipt_content_sha256,
        ))
