"""Inward ports for the native intelligence lifecycle kernel.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class IntelligenceCollectionReceipt:
    """Durable acknowledgement that a producer's terminal evidence is queued.

    ``COLLECTED`` intentionally says nothing about extraction, transfer, or
    closure.  It only proves that the source location and the work obligation
    were committed together by the collection store.
    """

    event_id: str
    work_key: str
    source_locator: str
    source_status: str
    created: bool
    state: str = "COLLECTED"
    authority_effect: str = "None"


class IntelligenceLifecyclePort(Protocol):
    """Evaluate custody claims without giving Python a second terminal predicate."""

    def seal_manifest(self, request: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def evaluate_lifecycle(self, request: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def evaluate_retention(self, request: Mapping[str, Any]) -> Mapping[str, Any]: ...


class IntelligenceCollectionPort(Protocol):
    """Durably register a producer's completed or refused work unit."""

    def collect(
        self,
        run_directory: str | Path,
        *,
        outcome: str,
        origin: str,
        producer_id: str,
    ) -> IntelligenceCollectionReceipt: ...

    def pending_work(self) -> list[dict[str, str]]: ...

    def record_lifecycle(
        self,
        work_key: str,
        *,
        lifecycle_state: str,
        detail: Mapping[str, Any],
    ) -> None: ...

    def complete_work(
        self,
        work_key: str,
        *,
        lifecycle_state: str,
        detail: Mapping[str, Any],
    ) -> None: ...


class IntelligenceDigestionFileSystemPort(Protocol):
    """Injected mutating filesystem boundary for archival application services."""

    def ensure_directory(self, path: Path) -> None: ...

    def create_directory(self, path: Path) -> None: ...

    def atomic_write_json(self, path: Path, payload: Mapping[str, Any]) -> None: ...

    def append_bytes(self, path: Path, payload: bytes) -> None: ...
