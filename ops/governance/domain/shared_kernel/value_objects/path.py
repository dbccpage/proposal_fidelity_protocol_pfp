"""Strongly-Typed Repository Path Value Object.

AuthorityEffect: None.
Guarantees canonical relative forward-slash paths, case-folding alias detection,
and hierarchical collision checking.
"""

from __future__ import annotations

import posixpath
from dataclasses import dataclass
from typing import Self

from .domain_invariant_error import DomainInvariantError


@dataclass(frozen=True, slots=True, eq=False)
class RepoPath:
    """Canonical repository-relative path Value Object."""

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str:
            raise DomainInvariantError("INVALID_PATH_TYPE", f"RepoPath must be str, got {type(self.value).__name__}")
        raw = self.value.strip()
        if not raw:
            raise DomainInvariantError("EMPTY_PATH", "RepoPath must not be empty")

        norm = raw.replace("\\", "/")
        norm = posixpath.normpath(norm).strip("/")

        if not norm or norm == ".":
            raise DomainInvariantError("EMPTY_PATH", "RepoPath must not resolve to empty root")
        if norm.startswith("/") or raw.startswith("/"):
            raise DomainInvariantError("ABSOLUTE_PATH_REFUSED", f"RepoPath must be relative: {raw}")
        if norm.startswith("..") or "/../" in norm or norm.endswith("/..") or ".." in norm.split("/"):
            raise DomainInvariantError("PARENT_DIRECTORY_ESCAPE_REFUSED", f"RepoPath must not escape parent: {raw}")

        if norm != self.value:
            object.__setattr__(self, "value", norm)

    @classmethod
    def from_str(cls: type[Self], val: str | Self) -> Self:
        if isinstance(val, cls):
            return val
        if type(val) is not str:
            raise DomainInvariantError("INVALID_PATH_COERCION", f"RepoPath.from_str requires str, got {type(val).__name__}")
        return cls(val)

    @property
    def segments(self) -> tuple[str, ...]:
        return tuple(self.value.split("/"))

    @property
    def casefold_value(self) -> str:
        return self.value.casefold()

    def conflicts_with(self, other: RepoPath | str) -> bool:
        """True if paths are identical, case-folding aliases, or hierarchically nested."""
        other_path = RepoPath.from_str(other)
        s1 = self.casefold_value
        s2 = other_path.casefold_value
        if s1 == s2:
            return True
        if s1.startswith(s2 + "/"):
            return True
        if s2.startswith(s1 + "/"):
            return True
        return False

    def is_under(self, root: RepoPath | str) -> bool:
        """True if this path is within or equal to the given root directory."""
        root_path = RepoPath.from_str(root)
        s_self = self.casefold_value
        s_root = root_path.casefold_value
        if s_self == s_root:
            return True
        return s_self.startswith(s_root + "/")

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"RepoPath({self.value!r})"


# Canonical alias for domain shared kernel
RepositoryPath = RepoPath
