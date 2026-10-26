"""Filesystem binding of ``RunArtifactSinkPort`` to an explicit output root.

The root is required. For Woland runs it is the directory returned by
``omega_engine_operating_system.adapters.intelligence_custody.intelligence_root.resolve_intelligence_repo_root``,
so run folders land in the durable ``_ic/`` store rather than in a
worktree; tests pass a temporary directory.

AuthorityEffect: None.
"""

from __future__ import annotations

import stat
from collections.abc import Sequence
from pathlib import Path

from omega_engine_operating_system.adapters.intelligence_custody.ic_routing import (
    IcMigrationRefusal,
    read_activation,
    relative_parts,
    safe_path,
)
from omega_engine_pfp.domain.ports.run_artifact_port import RunArtifactSinkPort


class OutputRootRequired(ValueError):
    """A run artifact sink was requested without an explicit output root."""

    code = "OUTPUT_ROOT_REQUIRED"


class FilesystemRunArtifactSink(RunArtifactSinkPort):
    """Writes UTF-8, LF-terminated artifacts under one explicit root directory."""

    def __init__(self, root: Path | str) -> None:
        if root is None or (isinstance(root, str) and not root.strip()):
            raise OutputRootRequired(
                f"{OutputRootRequired.code}: a run artifact sink needs an explicit output root"
            )
        self.root = Path(root).resolve()

    def _path(self, relative_path: str, *, writing: bool = False) -> Path:
        parts = relative_parts(relative_path)
        reserved = parts[0].casefold()
        if reserved in {"_ic", "_intelligence"} and parts[0] != reserved:
            raise IcMigrationRefusal(
                "UNSAFE_PATH", "reserved intelligence prefixes require canonical spelling"
            )
        if writing and parts[0] == "_intelligence":
            raise IcMigrationRefusal(
                "LEGACY_INTELLIGENCE_WRITE_REFUSED", "active writes require the canonical _ic route"
            )
        if parts[0] == "_ic":
            if writing:
                read_activation(self.root)
            path = safe_path(self.root, relative_path)
            if writing:
                try:
                    metadata = path.stat()
                except FileNotFoundError:
                    pass
                else:
                    if stat.S_ISREG(metadata.st_mode) and metadata.st_nlink != 1:
                        raise IcMigrationRefusal(
                            "HARDLINK_WRITE_REFUSED",
                            "IC artifact targets must be single-linked files",
                        )
            return path
        return self.root.joinpath(*parts)

    def put_text(self, relative_path: str, text: str) -> str:
        path = self._path(relative_path, writing=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return str(path)

    def append_lines(self, relative_path: str, lines: Sequence[str]) -> str:
        path = self._path(relative_path, writing=True)
        for line in lines:
            if "\n" in line or "\r" in line:
                raise ValueError("an appended line must not contain a line break")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as stream:
            for line in lines:
                stream.write(line.encode("utf-8") + b"\n")
        return str(path)

    def read_lines(self, relative_path: str) -> tuple[str, ...]:
        path = self._path(relative_path)
        if not path.exists():
            return ()
        return tuple(path.read_bytes().decode("utf-8").splitlines())


__all__ = ["FilesystemRunArtifactSink", "OutputRootRequired"]
