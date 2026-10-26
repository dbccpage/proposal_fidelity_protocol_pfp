"""EstateCatalogV3 Aggregate Root."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Tuple

from ..value_objects.content_digest import ContentDigest
from ..value_objects.identifier import EstateRef, OperationId, SkillId
from .operation_v3 import OperationV3
from .skill_document_v3 import SkillDocumentV3


@dataclass(frozen=True, slots=True)
class CapabilitySliceV3:
    slice_id: str
    name: str
    operation_ids: Tuple[OperationId, ...]
    description: str = ""


@dataclass(slots=True)
class EstateCatalogV3:
    catalog_id: str
    estate_ref: EstateRef
    epoch: int
    compiled_at: datetime
    skills: Dict[SkillId, SkillDocumentV3]
    operations: Dict[OperationId, OperationV3]
    capability_slices: Dict[str, CapabilitySliceV3]
    aliases: Dict[str, OperationId]
    catalog_digest: ContentDigest

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.catalog_id == other.catalog_id and self.catalog_digest == other.catalog_digest

    def __hash__(self) -> int:
        return hash((type(self), self.catalog_id, self.catalog_digest))

    @property
    def total_skills(self) -> int:
        return len(self.skills)

    @property
    def total_operations(self) -> int:
        return len(self.operations)
