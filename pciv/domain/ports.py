"""Domain ports and interface protocols for Prompt Civilization.

Clean Architecture boundaries: pure typed abstract protocols.
AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Protocol, Sequence
from .models import (
    CemeteryHeadstoneV1,
    CivilizationPrompt,
    GenealogyEntryV1,
    PopulationTier,
    PromptGenomeV1,
)


class CemeterySink(Protocol):
    """Protocol for recording terminal cemetery headstones."""

    def record_headstone(self, headstone: CemeteryHeadstoneV1) -> Any: ...


class GenealogyStorePort(Protocol):
    """Protocol for persisting and retrieving parent->child lineage mutations."""

    def record_lineage(self, entry: GenealogyEntryV1) -> Any: ...
    def get_lineage(self, child_run_key: str) -> Any: ...


class GenealogySink(Protocol):
    """Protocol for emitting re-entry mutation links."""

    def record_lineage(self, entry: GenealogyEntryV1) -> Any: ...


class ContentAddressedStoragePort(Protocol):
    """Protocol for storing and retrieving immutable byte artifacts."""

    def put_bytes(self, payload: bytes) -> str: ...
    def get_bytes(self, digest: str) -> bytes | None: ...
    def has(self, digest: str) -> bool: ...


class EventLogPort(Protocol):
    """Protocol for append-only event logging."""

    def append(self, event_type: str, payload: dict[str, Any]) -> str: ...
    def read_events(self) -> list[dict[str, Any]]: ...


class CustodyLedgerPort(Protocol):
    """Protocol for demographic tier and cryptographic signature ledger."""

    def get_prompt(self, prompt_id: str) -> CivilizationPrompt | None: ...
    def list_by_tier(self, tier: PopulationTier) -> Sequence[CivilizationPrompt]: ...


__all__ = [
    "CemeterySink",
    "ContentAddressedStoragePort",
    "CustodyLedgerPort",
    "EventLogPort",
    "GenealogySink",
    "GenealogyStorePort",
]
