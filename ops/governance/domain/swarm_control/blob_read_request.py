"""Blob Read Request Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BlobReadRequest:
    revision: str
    path: str

    def as_argv(self) -> list[str]:
        return ["git", "cat-file", "-p", f"{self.revision}:{self.path}"]
