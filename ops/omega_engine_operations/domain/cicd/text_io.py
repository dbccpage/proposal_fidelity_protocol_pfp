"""Narrow text ports. The domain does not open paths."""

from __future__ import annotations

from typing import Protocol


class TextReader(Protocol):
    """Read text the caller already located. No filesystem import."""

    def exists(self, path: str) -> bool: ...

    def read_text(self, path: str, *, errors: str = "strict") -> str: ...


class TextWriter(Protocol):
    """Write text the caller already located. No filesystem import."""

    def write_text(self, path: str, text: str) -> None: ...


class ByteReader(Protocol):
    """Read bytes the caller already located. No filesystem import."""

    def read_bytes(self, path: str) -> bytes: ...


class TreeRemover(Protocol):
    """Remove one directory tree the caller already located."""

    def remove_tree(self, path: str) -> None: ...


__all__ = ["ByteReader", "TextReader", "TextWriter", "TreeRemover"]
