"""Port for bounded advisory-lock acquisition.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from operations.domain.rop import Refusal, Result


class AdvisoryLockPort(Protocol):
    """Context-managed exclusive lock used by mutation and packaging workflows."""

    def __enter__(self) -> "AdvisoryLockPort": ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...


class AdvisoryLockFactoryPort(Protocol):
    """Construct a host lock without exposing its infrastructure implementation."""

    def create(self, path: Path, *, timeout: float) -> Result[AdvisoryLockPort, Refusal]: ...


__all__ = ["AdvisoryLockFactoryPort", "AdvisoryLockPort"]
