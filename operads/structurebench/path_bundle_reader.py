"""Filesystem adapter for the StructureBench bundle-reader port."""

import os
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath


def _safe_leaf_name(name: str) -> bool:
    """Admit a single relative filename and reject traversal or drive syntax."""
    if not name or name in {".", ".."}:
        return False
    posix = PurePosixPath(name)
    windows = PureWindowsPath(name)
    return (
        not posix.is_absolute()
        and not windows.is_absolute()
        and len(posix.parts) == 1
        and len(windows.parts) == 1
        and not windows.drive
    )


@dataclass(frozen=True, slots=True)
class PathBundleReader:
    """Read regular, non-symlink artifact files confined to one directory."""

    root: Path

    def __init__(self, root: Path | str) -> None:
        object.__setattr__(self, "root", Path(root))

    def is_bundle(self) -> bool:
        return self.root.is_dir()

    def read(self, name: str) -> bytes | None:
        if not _safe_leaf_name(name):
            return None
        path = self.root / name
        try:
            before_open = path.lstat()
        except OSError:
            return None
        if not stat.S_ISREG(before_open.st_mode):
            return None
        try:
            with path.open("rb") as stream:
                # Bind the opened handle to the regular file inspected above.
                # A path swap between lstat() and open() is refused before any
                # bytes are read, including on platforms without O_NOFOLLOW.
                if not os.path.samestat(before_open, os.fstat(stream.fileno())):
                    return None
                return stream.read()
        except OSError:
            return None


__all__ = ["PathBundleReader"]
