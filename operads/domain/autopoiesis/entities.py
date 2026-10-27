"""Domain entities and value objects for the Core Autopoiesis Engine.

Defines immutable records for harvested artifacts, snapshots, mined skills,
and mined antibodies.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class HarvestRecord:
    """An individual file ingested into the autopoietic archive."""

    relative_path: str
    sha256: str
    byte_size: int
    file_type: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "sha256": self.sha256,
            "byte_size": self.byte_size,
            "file_type": self.file_type,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class HarvestSnapshot:
    """A sealed, immutable snapshot of an ingested directory."""

    snapshot_id: str
    source_name: str
    created_at: str
    records: Sequence[HarvestRecord]
    merkle_root: str

    @classmethod
    def create(
        cls,
        snapshot_id: str,
        source_name: str,
        records: Sequence[HarvestRecord],
        created_at: str | None = None,
    ) -> HarvestSnapshot:
        ts = created_at or datetime.now(timezone.utc).isoformat()
        # Compute deterministic Merkle / sequence root over sorted records
        sorted_records = sorted(records, key=lambda r: r.relative_path)
        hasher = hashlib.sha256()
        for rec in sorted_records:
            hasher.update(rec.relative_path.encode("utf-8"))
            hasher.update(rec.sha256.encode("utf-8"))
            hasher.update(str(rec.byte_size).encode("utf-8"))
        merkle = hasher.hexdigest()
        return cls(
            snapshot_id=snapshot_id,
            source_name=source_name,
            created_at=ts,
            records=tuple(sorted_records),
            merkle_root=merkle,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "source_name": self.source_name,
            "created_at": self.created_at,
            "record_count": len(self.records),
            "merkle_root": self.merkle_root,
            "records": [r.to_dict() for r in self.records],
        }


@dataclass(frozen=True, slots=True)
class MinedSkillProposal:
    """A candidate skill mined from agent execution traces or work products."""

    skill_id: str
    title: str
    lead_council: str
    scope: str
    origin_agent_role: str
    confidence: str
    source_artifacts: Sequence[str]
    suggested_checks: Sequence[str]
    authority_effect: str = "None"

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "title": self.title,
            "lead_council": self.lead_council,
            "scope": self.scope,
            "origin_agent_role": self.origin_agent_role,
            "confidence": self.confidence,
            "source_artifacts": list(self.source_artifacts),
            "suggested_checks": list(self.suggested_checks),
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True, slots=True)
class MinedAntibody:
    """A candidate antibody / immune rule mined from agent failure modes."""

    antibody_id: str
    failure_class: str
    target_pattern: str
    constraint_type: str
    operatorizability: str
    action: str
    severity: str
    description: str
    negative_fixture: str
    positive_fixture: str
    source_file: str
    evidence_sha256: str
    authority_effect: str = "None"

    def to_dict(self) -> dict[str, Any]:
        return {
            "antibody_id": self.antibody_id,
            "failure_class": self.failure_class,
            "target_pattern": self.target_pattern,
            "constraint_type": self.constraint_type,
            "operatorizability": self.operatorizability,
            "action": self.action,
            "severity": self.severity,
            "description": self.description,
            "negative_fixture": self.negative_fixture,
            "positive_fixture": self.positive_fixture,
            "source_file": self.source_file,
            "evidence_sha256": self.evidence_sha256,
            "pharmacy_status": "candidate",
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True, slots=True)
class HarvestReceipt:
    """Verified evidence receipt certifying an autopoietic harvest run."""

    receipt_id: str
    timestamp: str
    teamwork_files_preserved: int
    antibodies_cataloged: int
    skills_mined: int
    antibodies_mined: int
    cas_objects_written: int
    merkle_roots: Mapping[str, str]
    authority_effect: str = "None"

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp,
            "teamwork_files_preserved": self.teamwork_files_preserved,
            "antibodies_cataloged": self.antibodies_cataloged,
            "skills_mined": self.skills_mined,
            "antibodies_mined": self.antibodies_mined,
            "cas_objects_written": self.cas_objects_written,
            "merkle_roots": dict(self.merkle_roots),
            "authority_effect": self.authority_effect,
        }
