"""Port for atomic Unit of Work managing catalog persistence and journal events."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from operations.domain.rop.result import Result
from ...domain.entities.catalog_v3 import EstateCatalogV3
from ...domain.errors.domain_errors import OeopDomainError
from ...domain.events.domain_events import DomainEventV3
from ...domain.value_objects.identifier import IdempotencyKey


class OeopUnitOfWorkPort(ABC):
    @abstractmethod
    def get_catalog(self, catalog_id: str) -> Result[Optional[EstateCatalogV3], OeopDomainError]:
        """Retrieve catalog by ID."""
        pass

    @abstractmethod
    def get_latest_catalog(
        self,
        estate_ref: Optional[str] = None,
    ) -> Result[Optional[EstateCatalogV3], OeopDomainError]:
        """Retrieve the most recently compiled catalog."""
        pass

    @abstractmethod
    def save_catalog(
        self,
        catalog: EstateCatalogV3,
        events: Tuple[DomainEventV3, ...],
        idempotency_key: Optional[IdempotencyKey] = None,
        request_digest: str = "",
        response_data: Optional[dict] = None,
        expected_version: Optional[int] = None,
    ) -> Result[None, OeopDomainError]:
        """Atomically commit catalog, events, outbox records, and idempotency receipt."""
        pass
