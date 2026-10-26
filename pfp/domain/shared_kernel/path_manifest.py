"""Shared Kernel: PathManifest Value Object with security traversal invariants."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from ..exceptions import InvariantViolationError
from .path import OwnedPath, ProtectedPath, RelativePath, validate_path_security


@dataclass(frozen=True, slots=True)
class PathManifest:
    """Enriched Value Object holding verified disjoint sets of owned and protected paths."""

    owned_paths: tuple[str, ...] = field(default_factory=tuple)
    protected_paths: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.owned_paths:
            raise InvariantViolationError("owned_paths must not be empty")

        for p in self.owned_paths:
            validate_path_security(p)
        for p in self.protected_paths:
            validate_path_security(p)

        owned_set = set(self.owned_paths)
        if len(owned_set) != len(self.owned_paths):
            raise InvariantViolationError("owned_paths contains duplicates")

        protected_set = set(self.protected_paths)
        if len(protected_set) != len(self.protected_paths):
            raise InvariantViolationError("protected_paths contains duplicates")

        intersection = owned_set & protected_set
        if intersection:
            raise InvariantViolationError(f"owned_paths and protected_paths must be disjoint; overlaps: {intersection}")

        object.__setattr__(self, "owned_paths", tuple(sorted(owned_set)))
        object.__setattr__(self, "protected_paths", tuple(sorted(protected_set)))

    @classmethod
    def create(
        cls,
        owned: Sequence[str | OwnedPath | RelativePath],
        protected: Sequence[str | ProtectedPath | RelativePath] = (),
    ) -> PathManifest:
        owned_strs = tuple(str(p) for p in owned)
        protected_strs = tuple(str(p) for p in protected)
        return cls(owned_paths=owned_strs, protected_paths=protected_strs)
