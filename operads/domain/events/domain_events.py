"""Domain events emitted by OEWAS V3 aggregates."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Tuple

from ..value_objects.authority import AuthorityEffect
from ..value_objects.content_digest import ContentDigest
from ..value_objects.identifier import (
    CausationId,
    CorrelationId,
    DocumentId,
    EstateRef,
    OperationId,
    SkillId,
)


def _event_value(value: Any) -> Any:
    """Encode the existing event values without losing ordered collections."""
    if isinstance(value, Enum):
        return _event_value(value.value)
    if isinstance(value, (tuple, list)):
        return [_event_value(item) for item in value]
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("Event payload object keys must be strings")
        return {key: _event_value(item) for key, item in value.items()}
    if isinstance(value, (
        ContentDigest, CausationId, CorrelationId, DocumentId, EstateRef, OperationId, SkillId,
    )):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"Unsupported event payload value: {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class DomainEventV3(ABC):
    """Abstract immutable domain event base class for OEWAS and cross-system event streams."""

    event_id: str
    occurred_at: datetime
    correlation_id: CorrelationId
    causation_id: CausationId
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError(f"{type(self).__name__} event_id must be a non-empty string")
        if not isinstance(self.occurred_at, datetime):
            raise TypeError(f"{type(self).__name__} occurred_at must be a datetime, got {type(self.occurred_at).__name__}")
        if not isinstance(self.correlation_id, CorrelationId):
            raise TypeError(f"{type(self).__name__} correlation_id must be a CorrelationId, got {type(self.correlation_id).__name__}")
        if not isinstance(self.causation_id, CausationId):
            raise TypeError(f"{type(self).__name__} causation_id must be a CausationId, got {type(self.causation_id).__name__}")
        if not isinstance(self.authority_effect, AuthorityEffect):
            raise TypeError(f"{type(self).__name__} authority_effect must be an AuthorityEffect, got {type(self.authority_effect).__name__}")

    @property
    def event_name(self) -> str:
        return self.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        """Convert domain event to canonical serializable dictionary."""
        result: Dict[str, Any] = {
            "event_id": self.event_id,
            "event_type": self.event_name,
            "occurred_at": self.occurred_at.isoformat(),
            "correlation_id": str(self.correlation_id),
            "causation_id": str(self.causation_id),
            "authority_effect": str(self.authority_effect.value),
            "schema_version": self.schema_version,
        }
        for field_name in self.__dataclass_fields__:
            if field_name not in result:
                result[field_name] = _event_value(getattr(self, field_name))
        return result

    @classmethod
    def create(
        cls,
        event_id: str,
        correlation_id: str,
        causation_id: str,
        **kwargs,
    ):
        return cls(
            event_id=event_id,
            occurred_at=datetime.now(timezone.utc),
            correlation_id=CorrelationId(correlation_id),
            causation_id=CausationId(causation_id),
            authority_effect=AuthorityEffect.NONE,
            **kwargs,
        )


@dataclass(frozen=True, slots=True)
class EstateCapturedV3(DomainEventV3):
    estate_ref: EstateRef = EstateRef("canonical")
    document_count: int = 0
    raw_digest: ContentDigest = ContentDigest.empty_sha256()


@dataclass(frozen=True, slots=True)
class DocumentImportedV3(DomainEventV3):
    document_id: DocumentId = DocumentId("doc")
    skill_id: SkillId = SkillId("skill")
    raw_digest: ContentDigest = ContentDigest.empty_sha256()
    semantic_digest: ContentDigest = ContentDigest.empty_sha256()
    operation_count: int = 0


@dataclass(frozen=True, slots=True)
class OperationDeclaredV3(DomainEventV3):
    operation_id: OperationId = OperationId("op")
    skill_id: SkillId = SkillId("skill")
    colour_in: Tuple[str, ...] = ()
    colour_out: str = ""
    authority_ceiling: AuthorityEffect = AuthorityEffect.NONE


@dataclass(frozen=True, slots=True)
class CompositionBoundV3(DomainEventV3):
    composition_id: str = ""
    term_kind: str = "primitive"
    source_operation_ids: Tuple[OperationId, ...] = ()


@dataclass(frozen=True, slots=True)
class CatalogCompiledV3(DomainEventV3):
    catalog_id: str = ""
    epoch: int = 1
    total_skills: int = 0
    total_operations: int = 0
    catalog_digest: ContentDigest = ContentDigest.empty_sha256()


@dataclass(frozen=True, slots=True)
class SkillConsolidationRecordedV3(DomainEventV3):
    legacy_skill_id: SkillId = SkillId("legacy")
    successor_operation_id: OperationId = OperationId("successor")
    migration_hash: ContentDigest = ContentDigest.empty_sha256()
