"""Use cases for Symbol Game operational modes discovery and auditing.
AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Dict, Optional

from pfp.domain.modes import ModeContract, ModesManifest


class ListModesUseCase:
    """Discovers and lists all registered operational modes."""

    def __init__(
        self,
        load_manifest: Callable[[], ModesManifest],
        load_contracts: Callable[[], Dict[int, ModeContract]],
    ) -> None:
        self.load_manifest = load_manifest
        self.load_contracts = load_contracts

    def execute(self, cluster_filter: Optional[str] = None) -> Dict[str, Any]:
        manifest = self.load_manifest()
        contracts = self.load_contracts()

        rows = []
        for mid, contract in sorted(contracts.items(), key=lambda x: x[0]):
            if cluster_filter and cluster_filter.lower() not in contract.cluster.lower():
                continue
            rows.append(contract.to_dict())

        return {
            "title": manifest.title,
            "manifest_version": manifest.manifest_version,
            "modes_dir": str(Path(manifest.manifest_path).parent),
            "total_count": len(contracts),
            "returned_count": len(rows),
            "modes": rows,
        }


class GetModeUseCase:
    """Retrieves a single operational mode contract by its ID."""

    def __init__(self, load_contracts: Callable[[], Dict[int, ModeContract]]) -> None:
        self.load_contracts = load_contracts

    def execute(self, mode_id: int) -> ModeContract:
        contracts = self.load_contracts()
        if mode_id not in contracts:
            raise KeyError(f"Mode ID {mode_id} not found in registered mode contracts.")
        return contracts[mode_id]


class ValidateModesUseCase:
    """Validates structural closure and contract invariants across the modes estate."""

    def __init__(self, validate_catalog: Callable[[], Dict[str, Any]]) -> None:
        self.validate_catalog = validate_catalog

    def execute(self) -> Dict[str, Any]:
        return self.validate_catalog()
