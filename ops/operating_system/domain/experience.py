"""Redacted experience memory domain models for OEOS governed tasks.

ExperienceRecordV1, MemoryQueryV1, MemoryHitV1, and MemoryIndexReceiptV1
implement the data model for the Redacted Experience Memory Bridge
(experience_memory_bridge.contract.yaml).

Invariants:
- Only verified sealed governed receipts (HarnessRunReceiptV1) may produce
  redacted typed experience projections (EMB-INV-001).
- Disposable indexes are deterministically reproducible from canonical receipts
  and never become evidence authorities (EMB-INV-002).
- Retrieved material remains untrusted context and grants no tool, policy,
  license, or execution authority (EMB-INV-003).
- Raw prompts, responses, credentials, and file contents are excluded.
- Source and redaction profile digests bind every hit.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .receipt import HarnessRunReceiptV1
from .task import (
    TERMINAL_STATES,
    TaskInvariantError,
    _ExactTypeValue,
    _require_digest,
    _require_exact_int,
    _require_exact_str,
    _require_timestamp,
    _IDENTIFIER,
    _SCOPED_IDENTIFIER,
    digest_payload,
)

SCHEMA_EXPERIENCE_RECORD = "core.oeos.experience-record.v1"
SCHEMA_MEMORY_QUERY = "core.oeos.memory-query.v1"
SCHEMA_MEMORY_HIT = "core.oeos.memory-hit.v1"
SCHEMA_MEMORY_INDEX_RECEIPT = "core.oeos.memory-index-receipt.v1"

_FORBIDDEN_CREDENTIAL_SUBSTRINGS = (
    "BEGIN PRIVATE KEY",
    "BEGIN RSA PRIVATE KEY",
    "BEGIN OPENSSH PRIVATE KEY",
    "ghp_",
    "sk-",
    "Bearer ",
)


@dataclass(frozen=True, slots=True, eq=False)
class ExperienceRecordV1(_ExactTypeValue):
    """Redacted experience projection bound to a sealed run receipt."""

    experience_id: str
    receipt_digest: str
    task_id: str
    task_family: str
    redaction_profile_digest: str
    redacted_summary: str
    observed_capabilities: tuple[str, ...]
    projected_at_utc: str
    schema: str = SCHEMA_EXPERIENCE_RECORD
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_EXPERIENCE_RECORD:
            raise TaskInvariantError(
                "SCHEMA_MISMATCH", "experience record schema differs"
            )
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN",
                "experience records grant no authority",
            )
        _require_exact_str(self.experience_id, "experience_id", _IDENTIFIER)
        _require_digest(self.receipt_digest, "receipt_digest")
        _require_exact_str(self.task_id, "task_id", _IDENTIFIER)
        _require_exact_str(self.task_family, "task_family", _SCOPED_IDENTIFIER)
        _require_digest(
            self.redaction_profile_digest, "redaction_profile_digest"
        )
        _require_timestamp(self.projected_at_utc, "projected_at_utc")

        if type(self.redacted_summary) is not str:
            raise TaskInvariantError(
                "INVALID_SUMMARY", "redacted_summary must be a string"
            )
        if not 1 <= len(self.redacted_summary) <= 4096:
            raise TaskInvariantError(
                "INVALID_SUMMARY",
                "redacted_summary length must be between 1 and 4096 characters",
            )
        summary_upper = self.redacted_summary.upper()
        for pattern in _FORBIDDEN_CREDENTIAL_SUBSTRINGS:
            if pattern.upper() in summary_upper:
                raise TaskInvariantError(
                    "MEMORY_REDACTION_REFUSED",
                    f"summary contains forbidden credential marker: {pattern}",
                )

        if type(self.observed_capabilities) is not tuple or any(
            type(c) is not str for c in self.observed_capabilities
        ):
            raise TaskInvariantError(
                "INVALID_CAPABILITIES",
                "observed_capabilities must be a tuple of string capability names",
            )
        for cap in self.observed_capabilities:
            _require_exact_str(cap, "observed_capability", _SCOPED_IDENTIFIER)
        if (
            tuple(sorted(set(self.observed_capabilities)))
            != self.observed_capabilities
        ):
            raise TaskInvariantError(
                "INVALID_CAPABILITIES",
                "observed_capabilities must be sorted and unique",
            )

    def to_canonical(self) -> dict[str, object]:
        return {
            "authority_effect": self.authority_effect,
            "experience_id": self.experience_id,
            "observed_capabilities": list(self.observed_capabilities),
            "projected_at_utc": self.projected_at_utc,
            "receipt_digest": self.receipt_digest,
            "redaction_profile_digest": self.redaction_profile_digest,
            "redacted_summary": self.redacted_summary,
            "schema": self.schema,
            "task_family": self.task_family,
            "task_id": self.task_id,
        }

    @property
    def canonical_digest(self) -> str:
        return digest_payload(self.schema, self.to_canonical())

    @classmethod
    def create(
        cls,
        *,
        experience_id: str,
        receipt_digest: str,
        task_id: str,
        task_family: str,
        redaction_profile_digest: str,
        redacted_summary: str,
        observed_capabilities: tuple[str, ...],
        projected_at_utc: str,
    ) -> ExperienceRecordV1:
        return cls(
            experience_id=experience_id,
            receipt_digest=receipt_digest,
            task_id=task_id,
            task_family=task_family,
            redaction_profile_digest=redaction_profile_digest,
            redacted_summary=redacted_summary,
            observed_capabilities=observed_capabilities,
            projected_at_utc=projected_at_utc,
        )

    @classmethod
    def project_from_receipt(
        cls,
        *,
        receipt: HarnessRunReceiptV1,
        experience_id: str,
        task_family: str,
        redaction_profile_digest: str,
        redacted_summary: str,
        observed_capabilities: tuple[str, ...],
        projected_at_utc: str,
    ) -> ExperienceRecordV1:
        if not isinstance(receipt, HarnessRunReceiptV1):
            raise TaskInvariantError(
                "MEMORY_RECEIPT_REFUSED",
                "receipt must be an instance of HarnessRunReceiptV1",
            )
        if receipt.terminal_state not in TERMINAL_STATES:
            raise TaskInvariantError(
                "MEMORY_RECEIPT_REFUSED",
                f"cannot project experience from non-terminal receipt state: {receipt.terminal_state.value}",
            )
        return cls(
            experience_id=experience_id,
            receipt_digest=receipt.canonical_digest,
            task_id=receipt.task_id,
            task_family=task_family,
            redaction_profile_digest=redaction_profile_digest,
            redacted_summary=redacted_summary,
            observed_capabilities=observed_capabilities,
            projected_at_utc=projected_at_utc,
        )

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> ExperienceRecordV1:
        expected = {
            "authority_effect",
            "experience_id",
            "observed_capabilities",
            "projected_at_utc",
            "receipt_digest",
            "redaction_profile_digest",
            "redacted_summary",
            "schema",
            "task_family",
            "task_id",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_EXPERIENCE_RECORD",
                "experience record fields differ",
            )
        raw_caps = value["observed_capabilities"]
        if type(raw_caps) is not list:
            raise TaskInvariantError(
                "INVALID_CAPABILITIES",
                "observed_capabilities must be a list in canonical form",
            )
        return cls(
            experience_id=value["experience_id"],  # type: ignore[arg-type]
            receipt_digest=value["receipt_digest"],  # type: ignore[arg-type]
            task_id=value["task_id"],  # type: ignore[arg-type]
            task_family=value["task_family"],  # type: ignore[arg-type]
            redaction_profile_digest=value["redaction_profile_digest"],  # type: ignore[arg-type]
            redacted_summary=value["redacted_summary"],  # type: ignore[arg-type]
            observed_capabilities=tuple(raw_caps),
            projected_at_utc=value["projected_at_utc"],  # type: ignore[arg-type]
            schema=value["schema"],  # type: ignore[arg-type]
            authority_effect=value["authority_effect"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True, eq=False)
class MemoryQueryV1(_ExactTypeValue):
    """Scoped query for disposable memory index retrieval."""

    query_id: str
    task_family: str
    query_digest: str
    limit: int
    created_at_utc: str
    schema: str = SCHEMA_MEMORY_QUERY
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_MEMORY_QUERY:
            raise TaskInvariantError(
                "SCHEMA_MISMATCH", "memory query schema differs"
            )
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN",
                "memory queries grant no authority",
            )
        _require_exact_str(self.query_id, "query_id", _IDENTIFIER)
        _require_exact_str(self.task_family, "task_family", _SCOPED_IDENTIFIER)
        _require_digest(self.query_digest, "query_digest")
        _require_exact_int(self.limit, "limit", 1, 1000)
        _require_timestamp(self.created_at_utc, "created_at_utc")

    def to_canonical(self) -> dict[str, object]:
        return {
            "authority_effect": self.authority_effect,
            "created_at_utc": self.created_at_utc,
            "limit": self.limit,
            "query_digest": self.query_digest,
            "query_id": self.query_id,
            "schema": self.schema,
            "task_family": self.task_family,
        }

    @property
    def canonical_digest(self) -> str:
        return digest_payload(self.schema, self.to_canonical())

    @classmethod
    def create(
        cls,
        *,
        query_id: str,
        task_family: str,
        query_digest: str,
        limit: int,
        created_at_utc: str,
    ) -> MemoryQueryV1:
        return cls(
            query_id=query_id,
            task_family=task_family,
            query_digest=query_digest,
            limit=limit,
            created_at_utc=created_at_utc,
        )

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> MemoryQueryV1:
        expected = {
            "authority_effect",
            "created_at_utc",
            "limit",
            "query_digest",
            "query_id",
            "schema",
            "task_family",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_MEMORY_QUERY",
                "memory query fields differ",
            )
        return cls(
            query_id=value["query_id"],  # type: ignore[arg-type]
            task_family=value["task_family"],  # type: ignore[arg-type]
            query_digest=value["query_digest"],  # type: ignore[arg-type]
            limit=value["limit"],  # type: ignore[arg-type]
            created_at_utc=value["created_at_utc"],  # type: ignore[arg-type]
            schema=value["schema"],  # type: ignore[arg-type]
            authority_effect=value["authority_effect"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True, eq=False)
class MemoryHitV1(_ExactTypeValue):
    """Untrusted context retrieved from disposable index with exact rational score."""

    hit_id: str
    experience_id: str
    record_digest: str
    score_numerator: int
    score_denominator: int
    source_receipt_digest: str
    redaction_profile_digest: str
    retrieved_at_utc: str
    schema: str = SCHEMA_MEMORY_HIT
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_MEMORY_HIT:
            raise TaskInvariantError(
                "SCHEMA_MISMATCH", "memory hit schema differs"
            )
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN",
                "retrieved material remains untrusted context and grants no authority",
            )
        _require_exact_str(self.hit_id, "hit_id", _IDENTIFIER)
        _require_exact_str(self.experience_id, "experience_id", _IDENTIFIER)
        _require_digest(self.record_digest, "record_digest")
        _require_digest(self.source_receipt_digest, "source_receipt_digest")
        _require_digest(
            self.redaction_profile_digest, "redaction_profile_digest"
        )
        _require_timestamp(self.retrieved_at_utc, "retrieved_at_utc")

        _require_exact_int(
            self.score_numerator, "score_numerator", 0, 1_000_000_000
        )
        _require_exact_int(
            self.score_denominator, "score_denominator", 1, 1_000_000_000
        )
        if self.score_numerator > self.score_denominator:
            raise TaskInvariantError(
                "INVALID_SCORE",
                "score_numerator cannot exceed score_denominator (rational in [0, 1])",
            )

    def to_canonical(self) -> dict[str, object]:
        return {
            "authority_effect": self.authority_effect,
            "experience_id": self.experience_id,
            "hit_id": self.hit_id,
            "record_digest": self.record_digest,
            "redaction_profile_digest": self.redaction_profile_digest,
            "retrieved_at_utc": self.retrieved_at_utc,
            "schema": self.schema,
            "score_denominator": self.score_denominator,
            "score_numerator": self.score_numerator,
            "source_receipt_digest": self.source_receipt_digest,
        }

    @property
    def canonical_digest(self) -> str:
        return digest_payload(self.schema, self.to_canonical())

    @classmethod
    def create(
        cls,
        *,
        hit_id: str,
        experience_id: str,
        record_digest: str,
        score_numerator: int,
        score_denominator: int,
        source_receipt_digest: str,
        redaction_profile_digest: str,
        retrieved_at_utc: str,
    ) -> MemoryHitV1:
        return cls(
            hit_id=hit_id,
            experience_id=experience_id,
            record_digest=record_digest,
            score_numerator=score_numerator,
            score_denominator=score_denominator,
            source_receipt_digest=source_receipt_digest,
            redaction_profile_digest=redaction_profile_digest,
            retrieved_at_utc=retrieved_at_utc,
        )

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> MemoryHitV1:
        expected = {
            "authority_effect",
            "experience_id",
            "hit_id",
            "record_digest",
            "redaction_profile_digest",
            "retrieved_at_utc",
            "schema",
            "score_denominator",
            "score_numerator",
            "source_receipt_digest",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_MEMORY_HIT",
                "memory hit fields differ",
            )
        return cls(
            hit_id=value["hit_id"],  # type: ignore[arg-type]
            experience_id=value["experience_id"],  # type: ignore[arg-type]
            record_digest=value["record_digest"],  # type: ignore[arg-type]
            score_numerator=value["score_numerator"],  # type: ignore[arg-type]
            score_denominator=value["score_denominator"],  # type: ignore[arg-type]
            source_receipt_digest=value["source_receipt_digest"],  # type: ignore[arg-type]
            redaction_profile_digest=value["redaction_profile_digest"],  # type: ignore[arg-type]
            retrieved_at_utc=value["retrieved_at_utc"],  # type: ignore[arg-type]
            schema=value["schema"],  # type: ignore[arg-type]
            authority_effect=value["authority_effect"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True, eq=False)
class MemoryIndexReceiptV1(_ExactTypeValue):
    """Disposable index build receipt binding source receipts."""

    index_receipt_id: str
    index_digest: str
    source_receipt_digests: tuple[str, ...]
    record_count: int
    indexed_at_utc: str
    schema: str = SCHEMA_MEMORY_INDEX_RECEIPT
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_MEMORY_INDEX_RECEIPT:
            raise TaskInvariantError(
                "SCHEMA_MISMATCH", "memory index receipt schema differs"
            )
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN",
                "memory index receipts grant no authority",
            )
        _require_exact_str(self.index_receipt_id, "index_receipt_id", _IDENTIFIER)
        _require_digest(self.index_digest, "index_digest")
        _require_timestamp(self.indexed_at_utc, "indexed_at_utc")

        if type(self.source_receipt_digests) is not tuple or any(
            type(d) is not str for d in self.source_receipt_digests
        ):
            raise TaskInvariantError(
                "INVALID_SOURCE_RECEIPTS",
                "source_receipt_digests must be a tuple of digest strings",
            )
        for d in self.source_receipt_digests:
            _require_digest(d, "source_receipt_digest")
        if (
            tuple(sorted(set(self.source_receipt_digests)))
            != self.source_receipt_digests
        ):
            raise TaskInvariantError(
                "INVALID_SOURCE_RECEIPTS",
                "source_receipt_digests must be sorted and unique",
            )

        _require_exact_int(self.record_count, "record_count", 0, 1_000_000)
        if self.record_count != len(self.source_receipt_digests):
            raise TaskInvariantError(
                "RECORD_COUNT_MISMATCH",
                f"record_count {self.record_count} does not match source receipt count {len(self.source_receipt_digests)}",
            )

    def to_canonical(self) -> dict[str, object]:
        return {
            "authority_effect": self.authority_effect,
            "index_digest": self.index_digest,
            "index_receipt_id": self.index_receipt_id,
            "indexed_at_utc": self.indexed_at_utc,
            "record_count": self.record_count,
            "schema": self.schema,
            "source_receipt_digests": list(self.source_receipt_digests),
        }

    @property
    def canonical_digest(self) -> str:
        return digest_payload(self.schema, self.to_canonical())

    @classmethod
    def create(
        cls,
        *,
        index_receipt_id: str,
        index_digest: str,
        source_receipt_digests: tuple[str, ...],
        record_count: int,
        indexed_at_utc: str,
    ) -> MemoryIndexReceiptV1:
        return cls(
            index_receipt_id=index_receipt_id,
            index_digest=index_digest,
            source_receipt_digests=source_receipt_digests,
            record_count=record_count,
            indexed_at_utc=indexed_at_utc,
        )

    @classmethod
    def from_canonical(
        cls, value: Mapping[str, object]
    ) -> MemoryIndexReceiptV1:
        expected = {
            "authority_effect",
            "index_digest",
            "index_receipt_id",
            "indexed_at_utc",
            "record_count",
            "schema",
            "source_receipt_digests",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_MEMORY_INDEX_RECEIPT",
                "memory index receipt fields differ",
            )
        raw_digests = value["source_receipt_digests"]
        if type(raw_digests) is not list:
            raise TaskInvariantError(
                "INVALID_SOURCE_RECEIPTS",
                "source_receipt_digests must be a list in canonical form",
            )
        return cls(
            index_receipt_id=value["index_receipt_id"],  # type: ignore[arg-type]
            index_digest=value["index_digest"],  # type: ignore[arg-type]
            source_receipt_digests=tuple(raw_digests),
            record_count=value["record_count"],  # type: ignore[arg-type]
            indexed_at_utc=value["indexed_at_utc"],  # type: ignore[arg-type]
            schema=value["schema"],  # type: ignore[arg-type]
            authority_effect=value["authority_effect"],  # type: ignore[arg-type]
        )


__all__ = [
    "ExperienceRecordV1",
    "MemoryHitV1",
    "MemoryIndexReceiptV1",
    "MemoryQueryV1",
    "SCHEMA_EXPERIENCE_RECORD",
    "SCHEMA_MEMORY_HIT",
    "SCHEMA_MEMORY_INDEX_RECEIPT",
    "SCHEMA_MEMORY_QUERY",
]
