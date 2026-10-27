"""Filesystem adapter for PackageBytesReader. Domain rules do not import this module.

AuthorityEffect: None.
"""

from __future__ import annotations

import os
from pathlib import Path


class FilesystemPackageReader:
    """Walks a package directory and reads file bytes from the host filesystem."""

    def list_relative_paths(self, package_dir: Path) -> list[str]:
        if not package_dir.is_dir():
            return []
        paths: list[str] = []
        for root, _, files in os.walk(package_dir):
            for name in files:
                full = Path(root) / name
                paths.append(full.relative_to(package_dir).as_posix())
        return paths

    def is_file(self, package_dir: Path, relative_path: str) -> bool:
        return (package_dir / relative_path).is_file()

    def read_bytes(self, package_dir: Path, relative_path: str) -> bytes:
        path = package_dir / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        return path.read_bytes()


__all__ = ["FilesystemPackageReader"]
