#!/usr/bin/env python3
"""Domain Value Objects for the packaging Bounded Context.

Enforces exact-type equality (RULE_VO_EXACT_TYPE_EQUALITY_001) and immutability.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from omega_engine_operations.domain.packaging.enums import (
    AssetDisposition,
    ContentHashMode,
)


@dataclass(frozen=True)
class AssetEntry:
    """Immutable record of an agent system asset entry."""

    path: str
    disposition: AssetDisposition
    hash_mode: ContentHashMode
    sha256: str
    byte_count: int
    containment_target: str | None = None

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, AssetEntry)
        return (
            self.path == other.path
            and self.disposition == other.disposition
            and self.hash_mode == other.hash_mode
            and self.sha256 == other.sha256
            and self.byte_count == other.byte_count
            and self.containment_target == other.containment_target
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.path,
                self.disposition,
                self.hash_mode,
                self.sha256,
                self.byte_count,
                self.containment_target,
            )
        )


@dataclass(frozen=True)
class ValidationFinding:
    """Immutable validation finding with severity and rationale."""

    category: str
    path: str
    message: str
    severity: str = "ERROR"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ValidationFinding)
        return (
            self.category == other.category
            and self.path == other.path
            and self.message == other.message
            and self.severity == other.severity
        )

    def __hash__(self) -> int:
        return hash((type(self), self.category, self.path, self.message, self.severity))


@dataclass(frozen=True)
class SourceAssetLockEntry:
    """Lockfile record for a bound source asset."""

    path: str
    sha256: str
    byte_count: int
    hash_mode: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, SourceAssetLockEntry)
        return (
            self.path == other.path
            and self.sha256 == other.sha256
            and self.byte_count == other.byte_count
            and self.hash_mode == other.hash_mode
        )

    def __hash__(self) -> int:
        return hash((type(self), self.path, self.sha256, self.byte_count, self.hash_mode))
