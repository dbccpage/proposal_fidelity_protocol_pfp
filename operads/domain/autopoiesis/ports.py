"""Domain ports for the Omega Autopoiesis Engine.

Defines interfaces for:
1. HarvestVaultPort: Content-addressed storage (CAS) and snapshot registry.
2. PharmacyCatalogPort: Antibody persistence and catalog updates.
3. SkillsRegisterPort: Proposed skills register persistence.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, Mapping, Protocol, Sequence

from .entities import (
    HarvestSnapshot,
    MinedAntibody,
    MinedSkillProposal,
)


class HarvestVaultPort(Protocol):
    """Port for storing files into content-addressed storage and recording snapshots."""

    def put_file(self, content_bytes: bytes, expected_sha256: str) -> bool:
        """Stores content in CAS if not already present. Returns True if written, False if existed."""
        ...

    def get_file(self, sha256: str) -> bytes | None:
        """Retrieves raw content from CAS by SHA-256 digest."""
        ...

    def save_snapshot(self, snapshot: HarvestSnapshot) -> ArtifactLocation:
        """Persists the snapshot manifest and returns its saved path."""
        ...

    def list_snapshots(self) -> Sequence[str]:
        """Lists all registered snapshot IDs."""
        ...

    def get_snapshot(self, snapshot_id: str) -> HarvestSnapshot | None:
        """Loads a snapshot by ID."""
        ...


class PharmacyCatalogPort(Protocol):
    """Port for managing antibody records and the central pharmacy catalog."""

    def load_catalog(self) -> Mapping[str, Any]:
        """Loads the current pharmacy catalog."""
        ...

    def save_antibody(self, antibody: MinedAntibody) -> ArtifactLocation:
        """Persists an antibody JSON record."""
        ...

    def merge_antibodies(self, antibodies: Sequence[MinedAntibody]) -> int:
        """Merges candidate antibodies into the catalog, incrementing sightings or creating entries. Returns updated count."""
        ...


class SkillsRegisterPort(Protocol):
    """Port for managing candidate skill proposals in the ooutwire register."""

    def load_proposed_skills(self) -> Sequence[str]:
        """Returns the list of already proposed skill IDs."""
        ...

    def append_skill_proposals(self, proposals: Sequence[MinedSkillProposal]) -> int:
        """Appends new unique skill proposals to the register. Returns count of newly added proposals."""
        ...


class ArtifactLocation(Protocol):
    """An artifact location with no filesystem implementation dependency."""

    def __fspath__(self) -> str: ...


@dataclass(frozen=True)
class HarvestSourceFile:
    relative_path: str
    file_type: str
    content: bytes


class HarvestSourcePort(Protocol):
    """Acquire source bytes and clear only a previously verified inventory."""

    def resolve(self, source: ArtifactLocation | str) -> str: ...

    def read_directory(self, root: str) -> Iterator[HarvestSourceFile]: ...

    def clear_verified(self, root: str, expected: Mapping[str, str]) -> int: ...
