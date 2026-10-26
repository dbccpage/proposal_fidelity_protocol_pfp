"""Port for emitting projection manifests."""

from __future__ import annotations

from abc import ABC, abstractmethod

from omega_engine_operations.domain.rop.result import Result
from ...domain.entities.catalog_v3 import EstateCatalogV3
from ...domain.errors.domain_errors import OeopDomainError


class ProjectionManifestPort(ABC):
    @abstractmethod
    def emit_projection(
        self,
        catalog: EstateCatalogV3,
        target_format: str,
    ) -> Result[str, OeopDomainError]:
        """Emit projection manifest bytes/string for target compatibility format."""
        pass
