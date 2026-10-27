# -*- coding: utf-8 -*-
"""protocols.py: Domain ports and interfaces for packaging and agent inventory operations.

Clean Architecture Layer: Domain Ports / Interfaces
AuthorityEffect: None
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Protocol

from operations.domain.packaging.value_objects import (
    AssetEntry,
    ValidationFinding,
)
from operations.domain.ports.advisory_lock_port import (
    AdvisoryLockFactoryPort,
    AdvisoryLockPort,
)
from operations.domain.rop import Refusal, Result


class InventoryScannerProtocol(Protocol):
    """Abstract interface for scanning repository paths for agent system assets."""

    def scan_assets(self, repo_root: Path) -> List[AssetEntry]:
        ...


class InventoryValidatorProtocol(Protocol):
    """Abstract interface for validating agent-system inventory against policy."""

    def validate_inventory(
        self, repo_root: Path, inventory_data: Dict[str, Any]
    ) -> List[ValidationFinding]:
        ...


class InventoryRendererProtocol(Protocol):
    """Abstract interface for rendering inventory views and reports."""

    def render_inventory(self, inventory_data: Dict[str, Any]) -> str:
        ...


class MirrorRecoveryEnvironmentPort(Protocol):
    """Custody primitives required by the mirror recovery application service."""

    def activate(self, repo_root: Path) -> Result[None, Refusal]: ...

    def json_bytes(self, value: object) -> Result[bytes, Refusal]: ...

    def parse_json(self, raw: bytes) -> Result[dict, Refusal]: ...

    def relative_parts(self, relative: str) -> Result[tuple[str, ...], Refusal]: ...

    def safe_path(self, repo_root: Path, relative: str) -> Result[Path, Refusal]: ...


class MirrorRecoveryFactoryPort(Protocol):
    """Build a recovery service with concrete outer-layer dependencies bound."""

    def create(self, mirror: object, names: list[str]) -> "MirrorRecoveryPort": ...


class MirrorRecoveryPort(Protocol):
    """Application-facing recovery transaction used by skill mirroring."""

    pending: Path
    lock: AdvisoryLockPort

    def recover(self) -> bool: ...

    def begin(self) -> None: ...

    def finish(self) -> None: ...


__all__ = [
    "AdvisoryLockFactoryPort",
    "InventoryRendererProtocol",
    "InventoryScannerProtocol",
    "InventoryValidatorProtocol",
    "MirrorRecoveryEnvironmentPort",
    "MirrorRecoveryFactoryPort",
    "MirrorRecoveryPort",
]
