"""protocols.py: Abstract port and interface definitions for product planning epic manifests.

Clean Architecture Layer: Ports / Interfaces
AuthorityEffect: None
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Protocol

from product_planning_office.domain.manifest_models import (
    EpicManifestAuditReport,
)


class EpicManifestAuditProtocol(Protocol):
    """Abstract interface for verifying epic manifest schema, inventory, and byte hashes."""

    def audit_manifest(
        self, repo_root: Path, manifest_path: Optional[Path] = None
    ) -> EpicManifestAuditReport:
        ...


class EpicManifestStorageProtocol(Protocol):
    """Abstract interface for loading and storing manifest JSON records."""

    def load_manifest(self, path: Path) -> Dict[str, Any]:
        ...

    def save_manifest(self, path: Path, manifest_data: Dict[str, Any]) -> None:
        ...
