"""Filesystem implementation of the Python Development Office source port."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from omega_engine_operads.domain.operad.errors import Err, Ok, Result
from omega_engine_operads.domain.python_development_office.errors import (
    SourceReadError,
)


class FileSystemSourceRepository:
    def current_directory(self) -> str:
        return str(Path.cwd())

    def resolve_path(self, path: str, project_root: str) -> str:
        source_path = Path(path)
        if not source_path.is_absolute():
            source_path = Path(project_root) / source_path
        return str(source_path.resolve())

    def discover(self, targets: Sequence[str], project_root: str) -> tuple[str, ...]:
        discovered: set[str] = set()
        for target in targets:
            path = Path(self.resolve_path(target, project_root))
            if path.is_file() and path.suffix == ".py":
                discovered.add(str(path))
            elif path.is_dir():
                discovered.update(
                    str(file.resolve()) for file in path.rglob("*.py") if file.is_file()
                )
        return tuple(sorted(discovered))

    def read_source(self, path: str) -> Result[str, SourceReadError]:
        try:
            return Ok(Path(path).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            return Err(SourceReadError(path, str(exc)))
