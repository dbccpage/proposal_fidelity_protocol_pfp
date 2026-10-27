"""Lease Denied Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LeaseDenied:
    residual: str
    holder: str
    conflict_paths: tuple[str, ...] = ()
    conflict_resources: tuple[str, ...] = ()
