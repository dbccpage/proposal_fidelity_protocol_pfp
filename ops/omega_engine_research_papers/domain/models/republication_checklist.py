"""Canonical 52-Point Severe Zenodo Republication Checklist & Evidence Catalog.

AuthorityEffect: None.

Defines the 52 canonical checklist items across the 9 Evidence Channels (A through I)
derived from the canonical Zenodo republication gate specification, checklist.py, and
the companion declarative YAML catalog (republication_checklist.yaml).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

CATALOG_VERSION = "omega.paper-republication-checklist.v1"
CATALOG_ORIGIN = "canonical A-I obligations from omega-paper-review-swarm"
DEFAULT_SOURCE = "omega_engine_operads/skills/omega-paper-review-swarm/references/canonical_zenodo_republication_gate_prompt.md"


class CheckMethod(str, Enum):
    """Evaluation method required for a checklist item."""

    STATIC = "static"
    REVIEW = "review"
    EXECUTION = "execution"
    AUTHORIZATION = "authorization"


@dataclass(frozen=True)
class ChecklistChannel:
    """Evidence channel metadata (A through I)."""

    code: str
    name: str
    description: str


@dataclass(frozen=True)
class ChecklistConfiguration:
    """Operational limits and deposit constraints."""

    max_file_bytes: int = 64 * 1024 * 1024  # 64 MiB
    max_payload_bytes: int = 256 * 1024 * 1024  # 256 MiB
    max_path_length: int = 250
    cache_directories: frozenset[str] = frozenset(
        {
            ".git",
            ".lake",
            ".venv",
            "venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".ipynb_checkpoints",
            "htmlcov",
            "target",
        }
    )
    required_files: Tuple[str, ...] = (
        "README.md",
        "LICENSE",
        "MANIFEST.sha256",
        "SHA256SUMS",
        "zenodo_metadata.json",
    )
    required_change_log_suffix: str = "_change_log.md"
    required_claim_ledger_suffix: str = "_claim_ledger.md"


@dataclass
class RepublicationCheckItem:
    """Individual gate check item."""

    id: str
    channel: str
    method: str
    requirement: str
    source: str
    status: str = "NOT_VERIFIED"  # "PASS", "FAIL", "NOT_VERIFIED", "NOT_APPLICABLE", "BLOCKED"
    detail: str = ""
    description: str = ""
    recorded_evidence: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_static(self) -> bool:
        return self.method == CheckMethod.STATIC.value

    @property
    def is_review(self) -> bool:
        return self.method == CheckMethod.REVIEW.value

    @property
    def is_execution(self) -> bool:
        return self.method == CheckMethod.EXECUTION.value

    @property
    def is_authorization(self) -> bool:
        return self.method == CheckMethod.AUTHORIZATION.value

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "id": self.id,
            "channel": self.channel,
            "method": self.method,
            "requirement": self.requirement,
            "source": self.source,
            "status": self.status,
            "detail": self.detail,
        }
        if self.recorded_evidence:
            res["recorded_evidence"] = self.recorded_evidence
        return res


@dataclass
class RepublicationChecklistCatalog:
    """Strongly-typed container for the complete republication checklist."""

    schema_version: str
    catalog_origin: str
    source: str
    authority_effect: str = "None"
    channels: Dict[str, ChecklistChannel] = field(default_factory=dict)
    configuration: ChecklistConfiguration = field(default_factory=ChecklistConfiguration)
    items: List[RepublicationCheckItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")
        self._by_id: Dict[str, RepublicationCheckItem] = {item.id: item for item in self.items}

    def validate(self) -> None:
        """Fail-closed consistency validation."""
        if len(self.items) != 52:
            raise ValueError(f"Catalog must contain exactly 52 items, found {len(self.items)}")
        if len(self.channels) != 9:
            raise ValueError(f"Catalog must define exactly 9 channels, found {len(self.channels)}")
        expected_channels = set("ABCDEFGHI")
        actual_channels = {item.channel for item in self.items}
        if actual_channels != expected_channels:
            raise ValueError(f"Items must span channels {expected_channels}, found {actual_channels}")
        valid_methods = {m.value for m in CheckMethod}
        for item in self.items:
            if item.method not in valid_methods:
                raise ValueError(f"Item {item.id} has invalid method {item.method!r}")
            if not item.id.startswith(item.channel):
                raise ValueError(f"Item ID {item.id} does not match channel {item.channel}")

    def to_catalog_tuple(self) -> Tuple[Tuple[str, str, str], ...]:
        """Convert to legacy (id, method, requirement) tuple format."""
        return tuple((item.id, item.method, item.requirement) for item in self.items)

    def get_item(self, check_id: str) -> Optional[RepublicationCheckItem]:
        return self._by_id.get(check_id)

    def get_channel_items(self, channel: str) -> List[RepublicationCheckItem]:
        return [item for item in self.items if item.channel == channel]

    @classmethod
    def from_yaml_data(cls, data: Dict[str, Any]) -> RepublicationChecklistCatalog:
        schema_version = str(data.get("schema_version", CATALOG_VERSION))
        catalog_origin = str(data.get("catalog_origin", CATALOG_ORIGIN))
        authority_effect = str(data.get("authority_effect", "None"))
        source = str(data.get("source", DEFAULT_SOURCE))

        # Channels
        channels: Dict[str, ChecklistChannel] = {}
        for code, info in data.get("channels", {}).items():
            channels[code] = ChecklistChannel(
                code=code,
                name=str(info.get("name", "")),
                description=str(info.get("description", "")),
            )

        # Configuration
        cfg_data = data.get("configuration", {})
        config = ChecklistConfiguration(
            max_file_bytes=int(cfg_data.get("max_file_bytes", 64 * 1024 * 1024)),
            max_payload_bytes=int(cfg_data.get("max_payload_bytes", 256 * 1024 * 1024)),
            max_path_length=int(cfg_data.get("max_path_length", 250)),
            cache_directories=frozenset(cfg_data.get("cache_directories", [])),
            required_files=tuple(cfg_data.get("required_files", ())),
            required_change_log_suffix=str(cfg_data.get("required_change_log_suffix", "_change_log.md")),
            required_claim_ledger_suffix=str(cfg_data.get("required_claim_ledger_suffix", "_claim_ledger.md")),
        )

        # Items
        items: List[RepublicationCheckItem] = []
        for raw in data.get("checks", []):
            item_id = str(raw["id"])
            method = str(raw["method"])
            items.append(
                RepublicationCheckItem(
                    id=item_id,
                    channel=str(raw.get("channel", item_id[0])),
                    method=method,
                    requirement=str(raw["requirement"]),
                    source=f"{source}#required-evidence-channels",
                    status="NOT_VERIFIED",
                    detail=str(raw.get("detail", f"Requires independent {method} evidence; file presence or a claimed PASS is insufficient.")),
                    description=str(raw.get("description", "")),
                )
            )

        catalog = cls(
            schema_version=schema_version,
            catalog_origin=catalog_origin,
            authority_effect=authority_effect,
            source=source,
            channels=channels,
            configuration=config,
            items=items,
        )
        catalog.validate()
        return catalog

    @classmethod
    def load_from_yaml(cls, yaml_path: Optional[Path | str] = None) -> RepublicationChecklistCatalog:
        if yaml_path is not None:
            p = Path(yaml_path)
            if p.is_file():
                content = p.read_text(encoding="utf-8")
                return cls.from_yaml_data(yaml.safe_load(content))

        # Search candidates
        this_dir = Path(__file__).resolve().parent
        repo_root = this_dir.parents[2]
        candidates = [
            this_dir / "republication_checklist.yaml",
            repo_root / "omega_engine_research_papers" / "use_cases" / "paper_review" / "republication_checklist.yaml",
        ]
        for candidate in candidates:
            if candidate.is_file():
                content = candidate.read_text(encoding="utf-8")
                return cls.from_yaml_data(yaml.safe_load(content))

        raise FileNotFoundError(f"Cannot find republication_checklist.yaml in {[str(c) for c in candidates]}")


_CACHED_CATALOG: Optional[RepublicationChecklistCatalog] = None


def get_checklist_catalog() -> RepublicationChecklistCatalog:
    """Return the cached, singleton instance of the RepublicationChecklistCatalog."""
    global _CACHED_CATALOG
    if _CACHED_CATALOG is None:
        _CACHED_CATALOG = RepublicationChecklistCatalog.load_from_yaml()
    return _CACHED_CATALOG


# Backward-compatible global exports
REPUBLICATION_CATALOG: Tuple[Tuple[str, str, str], ...] = get_checklist_catalog().to_catalog_tuple()
EVIDENCE_CHANNELS: Dict[str, str] = {c.code: c.name for c in get_checklist_catalog().channels.values()}


@dataclass
class RepublicationGateReceipt:
    """Receipt for Stage Ω Canonical Severe Zenodo Republication Gate."""

    catalog_version: str = CATALOG_VERSION
    catalog_origin: str = CATALOG_ORIGIN
    snapshot_sha256: str = ""
    paper_path: str = ""
    monograph_path: str = ""
    files: List[Dict[str, Any]] = field(default_factory=list)
    checks: List[RepublicationCheckItem] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)
    recorded_evidence: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    status: str = "BLOCKED"  # "PASS" or "BLOCKED"
    verdict: str = "NOT READY FOR ZENODO REPUBLICATION"
    authority_effect: str = "None"
    limitations: Tuple[str, ...] = (
        "Static PASS establishes only its named predicate.",
        "Imported reports and PASS fields are provenance, never independently verified execution or proof.",
        "Semantic, execution and authorization obligations need separate independent assessment.",
    )

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "catalog_version": self.catalog_version,
            "catalog_origin": self.catalog_origin,
            "snapshot_sha256": self.snapshot_sha256,
            "paper_path": self.paper_path,
            "monograph_path": self.monograph_path,
            "files": self.files,
            "checks": [c.to_dict() for c in self.checks],
            "counts": self.counts,
            "recorded_evidence": self.recorded_evidence,
            "errors": self.errors,
            "status": self.status,
            "verdict": self.verdict,
            "authority_effect": self.authority_effect,
            "limitations": list(self.limitations),
        }
