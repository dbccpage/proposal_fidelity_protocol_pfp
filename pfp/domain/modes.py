"""Domain entities for Symbol Game operational modes.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ModeCluster:
    cluster_id: str
    name: str
    mode_ids: List[int] = field(default_factory=list)


@dataclass(frozen=True)
class ModeContract:
    mode_id: int
    name: str
    cluster: str
    authority_effect: str
    core_mechanism: str
    substrate: str
    paper_reference: str
    rules: List[str] = field(default_factory=list)
    entry_preconditions: List[str] = field(default_factory=list)
    winning_condition: str = ""
    failure_modes: List[str] = field(default_factory=list)
    verifier_contract: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode_id": self.mode_id,
            "name": self.name,
            "cluster": self.cluster,
            "authority_effect": self.authority_effect,
            "core_mechanism": self.core_mechanism,
            "substrate": self.substrate,
            "paper_reference": self.paper_reference,
            "rules": list(self.rules),
            "entry_preconditions": list(self.entry_preconditions),
            "winning_condition": self.winning_condition,
            "failure_modes": list(self.failure_modes),
            "verifier_contract": dict(self.verifier_contract),
            "file_path": str(self.file_path) if self.file_path else None,
        }


@dataclass(frozen=True)
class ModesManifest:
    manifest_version: str
    title: str
    description: str
    clusters: Dict[str, ModeCluster]
    modes: List[Dict[str, Any]]
    manifest_path: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "title": self.title,
            "description": self.description,
            "clusters": {
                k: {"name": v.name, "mode_ids": list(v.mode_ids)}
                for k, v in self.clusters.items()
            },
            "modes_count": len(self.modes),
            "manifest_path": str(self.manifest_path),
        }
