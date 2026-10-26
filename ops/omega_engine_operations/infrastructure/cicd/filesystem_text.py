"""Filesystem adapters for the domain text ports.

AuthorityEffect: None.
"""

from __future__ import annotations

import shutil
from pathlib import Path


class FilesystemTextReader:
    """Read UTF-8 text from a path the caller already chose."""

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def read_text(self, path: str, *, errors: str = "strict") -> str:
        return Path(path).read_text(encoding="utf-8", errors=errors)


class FilesystemTextWriter:
    """Write UTF-8 text to a path the caller already chose."""

    def write_text(self, path: str, text: str) -> None:
        Path(path).write_text(text, encoding="utf-8")


class FilesystemByteReader:
    """Read bytes from a path the caller already chose."""

    def read_bytes(self, path: str) -> bytes:
        return Path(path).read_bytes()


class FilesystemTreeRemover:
    """Remove one directory tree. Failures propagate."""

    def remove_tree(self, path: str) -> None:
        shutil.rmtree(path, ignore_errors=False)
