"""Port for reading legacy V1/V2 skill catalogs and markdown files."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

from omega_engine_operations.domain.rop.result import Result
from ...domain.entities.skill_document_v3 import SkillDocumentV3
from ...domain.errors.domain_errors import OeopDomainError
from ...domain.value_objects.identifier import EstateRef


class LegacyCatalogReaderPort(ABC):
    @abstractmethod
    def read_legacy_estate(
        self,
        estate_ref: EstateRef,
    ) -> Result[Tuple[SkillDocumentV3, ...], OeopDomainError]:
        """Read and adapt legacy V1/V2 skills into V3 SkillDocumentV3 aggregates."""
        pass
