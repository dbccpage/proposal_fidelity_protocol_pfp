"""Catalog text port. The domain does not open paths."""

from __future__ import annotations

from typing import Protocol


class CatalogTextSource(Protocol):
    def read_text(self, path: str) -> str: ...

    def is_file(self, path: str) -> bool: ...

    def exists(self, path: str) -> bool: ...


__all__ = ["CatalogTextSource"]
