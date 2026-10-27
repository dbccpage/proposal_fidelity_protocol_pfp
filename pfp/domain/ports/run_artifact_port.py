"""Port for the files a Symbol Game run leaves behind.

The domain names artifacts by repository-relative POSIX paths such as
``_intelligence/unified_oe_trace.jsonl``; it never holds a filesystem root and
never opens a file. The composition root binds this port to an explicit output
root (for a Adversary run, the root that ``resolve_intelligence_repo_root``
returns). There is no default root: an unbound sink is a refusal, not a write
into whichever checkout the code happens to live in.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class RunArtifactSinkPort(Protocol):
    """Write and read run artifacts by relative path under a bound root."""

    def put_text(self, relative_path: str, text: str) -> str:
        """Create or replace one text artifact; return its locator."""
        ...

    def append_lines(self, relative_path: str, lines: Sequence[str]) -> str:
        """Append newline-free lines to an append-only artifact; return its locator."""
        ...

    def read_lines(self, relative_path: str) -> tuple[str, ...]:
        """Return the artifact's lines, or an empty tuple when it does not exist."""
        ...


__all__ = ["RunArtifactSinkPort", "create_filesystem_artifact_sink"]


def create_filesystem_artifact_sink(root: object) -> RunArtifactSinkPort:
    """Dynamically resolve and instantiate the filesystem sink without static domain-to-infra coupling."""
    import importlib

    mod = importlib.import_module(
        "pfp.infrastructure.persistence.run_artifact_sink"
    )
    sink = mod.FilesystemRunArtifactSink(str(root))
    return sink

