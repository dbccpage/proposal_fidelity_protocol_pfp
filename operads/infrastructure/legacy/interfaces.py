"""Protocols for reading estate files and managing catalog repositories."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from .models import AgentDefV1, EstateCatalogSnapshotV1, SkillDefV1, WorkflowDefV1


class EstateReaderProtocol(Protocol):
    """Protocol for reading estate source metadata without write capability."""

    def read_skill_frontmatters(self, skills_dir: Path) -> Mapping[str, SkillDefV1]:
        """Read all SKILL.md frontmatters beneath skills_dir."""
        ...

    def read_agent_specs(self, agents_dir: Path) -> Mapping[str, AgentDefV1]:
        """Read all agent spec markdown files beneath agents_dir."""
        ...

    def read_workflow_specs(self, workflows_dir: Path) -> Mapping[str, WorkflowDefV1]:
        """Read all workflow JSON files beneath workflows_dir."""
        ...


class EstateCatalogRepositoryProtocol(Protocol):
    """Protocol for accessing immutable catalog snapshots."""

    def get_snapshot(self) -> EstateCatalogSnapshotV1:
        """Get the current loaded estate catalog snapshot."""
        ...
