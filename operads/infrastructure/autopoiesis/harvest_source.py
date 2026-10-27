"""Filesystem acquisition and verified clearing for autopoietic harvest."""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from typing import Iterator, Mapping

from operads.domain.autopoiesis.ports import (
    ArtifactLocation,
    HarvestSourceFile,
)


class FilesystemHarvestSource:
    def resolve(self, source: ArtifactLocation | str) -> str:
        return str(Path(source).resolve())

    @staticmethod
    def _inventory(root: Path) -> list[Path]:
        def fail(error: OSError) -> None:
            raise error

        files = []
        for parent, directories, names in os.walk(root, followlinks=False, onerror=fail):
            for name in [*directories, *names]:
                path = Path(parent) / name
                info = path.lstat()
                if getattr(info, "st_file_attributes", 0) & 0x400 or stat.S_ISLNK(info.st_mode):
                    raise RuntimeError(f"PRE_CLEAN_REFUSAL: linked source entry: {path}")
                if name in names:
                    if not stat.S_ISREG(info.st_mode):
                        raise RuntimeError(f"PRE_CLEAN_REFUSAL: non-regular source: {path}")
                    files.append(path)
        return sorted(files, key=lambda p: p.relative_to(root).as_posix().encode("utf-8"))

    def read_directory(self, root: str) -> Iterator[HarvestSourceFile]:
        directory = Path(root)
        if not directory.exists():
            raise FileNotFoundError(f"Source directory does not exist: {directory}")
        if not directory.is_dir():
            raise NotADirectoryError(directory)
        for path in self._inventory(directory):
            yield HarvestSourceFile(
                relative_path=path.relative_to(directory).as_posix(),
                file_type=path.suffix.lstrip(".").lower() or "txt",
                content=path.read_bytes(),
            )

    def clear_verified(self, root: str, expected: Mapping[str, str]) -> int:
        directory = Path(root)
        paths = self._inventory(directory)
        observed = {
            path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths
        }
        if observed != expected:
            raise RuntimeError("PRE_CLEAN_REFUSAL: source changed after verification")
        cleared_count = len([path for path in directory.iterdir() if path.name != ".gitkeep"])
        # Only verified regular files are removed; recursive deletion could erase
        # new files or files omitted by an earlier traversal.
        for path in paths:
            if path == directory / ".gitkeep":
                continue
            if (
                path.is_symlink()
                or hashlib.sha256(path.read_bytes()).hexdigest()
                != expected[path.relative_to(directory).as_posix()]
            ):
                raise RuntimeError("PRE_CLEAN_REFUSAL: source changed before removal")
            path.unlink()
        for parent, _, _ in os.walk(directory, topdown=False, followlinks=False):
            if Path(parent) != directory:
                Path(parent).rmdir()
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# Autopoietic Harvest Managed\n", encoding="utf-8")
        return cleared_count
