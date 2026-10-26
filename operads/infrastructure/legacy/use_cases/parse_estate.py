"""Use case for parsing the entire estate into an immutable typed snapshot."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..interfaces import EstateReaderProtocol
from ..models import (
    CatalogAntiSkillRefV1,
    EstateCatalogSnapshotV1,
)
from ...fs_reader import ReadOnlyEstateFSReader


class ParseEstateUseCase:
    """Orchestrates reading and constructing an EstateCatalogSnapshotV1."""

    def __init__(self, reader: EstateReaderProtocol | None = None) -> None:
        self.reader = reader or ReadOnlyEstateFSReader()

    def execute(
        self,
        estate_root: Path,
        anti_skills: Mapping[str, CatalogAntiSkillRefV1] | None = None,
        snapshot_id: str = "snapshot_epoch1_shadow",
    ) -> EstateCatalogSnapshotV1:
        skills_dir = estate_root / "skills"
        agents_dir = estate_root / "agents"
        workflows_dir = estate_root / "workflows"

        skills = self.reader.read_skill_frontmatters(skills_dir)
        agents = self.reader.read_agent_specs(agents_dir)
        workflows = self.reader.read_workflow_specs(workflows_dir)

        anti_skill_map = dict(anti_skills or {})

        return EstateCatalogSnapshotV1(
            snapshot_id=snapshot_id,
            skills=skills,
            agents=agents,
            workflows=workflows,
            anti_skills=anti_skill_map,
            authority_effect="None",
        )
