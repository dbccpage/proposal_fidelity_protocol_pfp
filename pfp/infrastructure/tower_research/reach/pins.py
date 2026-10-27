"""Reading pinned bytes: ``git show <commit>:<path>`` and nothing else.

AuthorityEffect: None. K2 recomputes every digest from bytes read here; no
digest is taken from a record.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Protocol

from pfp.infrastructure.tower_evidence.level_engine import (
    EvidenceRefusal, LevelEngineEvidenceResolver,
)


class Resolver(Protocol):
    def read(self, repo: str, commit: str, path: str) -> bytes | None: ...


@dataclass(frozen=True)
class GitResolver:
    """Resolves (repo, commit, path) against local clones named by repo.

    ``harness_hosts`` names, per carrier, the repository that holds its
    Mode E harness commits (declared in ``carriers.json`` as
    ``harness_host``). It is tried only after the carrier's own clone, and
    only a commit that exists in the host's history resolves there: a
    carrier's own commit never does, since the histories are distinct.
    """

    clones: Mapping[str, Path]
    harness_hosts: Mapping[str, Path] = field(default_factory=dict)

    def read(self, repo: str, commit: str, path: str) -> bytes | None:
        for clone in (self.clones.get(repo), self.harness_hosts.get(repo)):
            if clone is None:
                continue
            try:
                return LevelEngineEvidenceResolver(clone).read_bytes("v1", path, revision=commit)
            except EvidenceRefusal:
                # Missing or invalid historical pins are unresolved. Never try v2 or disk bytes.
                continue
        return None


@dataclass(frozen=True)
class MapResolver:
    """An in-memory resolver, for tests and for replaying a frozen bundle."""

    files: Mapping[tuple[str, str, str], bytes] = field(default_factory=dict)

    def read(self, repo: str, commit: str, path: str) -> bytes | None:
        return self.files.get((repo, commit, path))
