"""Shared Kernel: RelativePath Value Object with strict POSIX path security invariants."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ..exceptions import InvariantViolationError, SecurityPathViolationError

_WINDOWS_RESERVED_NAMES: frozenset[str] = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
)


def is_normalized_relative_posix(value: str) -> bool:
    """Return whether ``value`` is already a normalized relative POSIX path."""
    if not value or "\\" in value or "\x00" in value:
        return False
    if value.startswith("/") or value.endswith("/") or "//" in value:
        return False
    parts = value.split("/")
    if not parts or any(part in {"", ".", ".."} for part in parts):
        return False
    if any(":" in part or part.endswith((".", " ")) for part in parts):
        return False
    if any(part.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES for part in parts):
        return False
    return True


def validate_path_security(path_str: str) -> None:
    """Invariant: Paths must be clean, relative POSIX paths without directory traversal or forbidden names."""
    if not isinstance(path_str, str) or not path_str:
        raise SecurityPathViolationError("Path must be a non-empty string")
    if "\\" in path_str or ":" in path_str:
        raise SecurityPathViolationError(
            f"Path contains backslashes, drive letters, or alternate streams: {path_str!r}"
        )
    if any(ord(char) < 32 or ord(char) == 127 for char in path_str):
        raise SecurityPathViolationError(
            f"Path contains control characters: {path_str!r}"
        )
    if path_str.startswith("/") or path_str.endswith("/") or "//" in path_str:
        raise SecurityPathViolationError(
            f"Path has leading/trailing/double slashes: {path_str!r}"
        )

    segments = path_str.split("/")
    for segment in segments:
        if segment in (".", "..") or not segment:
            raise SecurityPathViolationError(
                f"Path contains invalid segment {segment!r} in {path_str!r}"
            )
        if segment.endswith((".", " ")):
            raise SecurityPathViolationError(
                f"Path segment ends with dot or space: {segment!r} in {path_str!r}"
            )
        base_name = segment.split(".")[0].upper()
        if base_name in _WINDOWS_RESERVED_NAMES:
            raise SecurityPathViolationError(
                f"Path contains Windows reserved device name {segment!r} in {path_str!r}"
            )


@dataclass(frozen=True, slots=True, eq=False)
class RelativePath:
    """Strongly-typed relative POSIX path Value Object."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolationError(
                f"RelativePath must be a string, got {type(self.value).__name__}"
            )
        validate_path_security(self.value)

    @classmethod
    def from_str(cls: type[Self], val: str | Self) -> Self:
        if isinstance(val, cls):
            return val
        if type(val) is not str:
            raise InvariantViolationError(
                f"{cls.__name__}.from_str requires an exact str, got {type(val).__name__}"
            )
        return cls(val)

    def is_within(self, root: str | RelativePath) -> bool:
        """Boundary-aware containment check."""
        root_str = root.value if isinstance(root, RelativePath) else str(root)
        root_str = root_str.strip("/")
        if not root_str:
            return True
        return self.value == root_str or self.value.startswith(root_str + "/")

    def startswith(self, prefix: str | RelativePath) -> bool:
        pref = prefix.value if isinstance(prefix, RelativePath) else str(prefix)
        return self.value.startswith(pref)

    def endswith(self, suffix: str | RelativePath) -> bool:
        suf = suffix.value if isinstance(suffix, RelativePath) else str(suffix)
        return self.value.endswith(suf)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RelativePath) or type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))


@dataclass(frozen=True, slots=True, eq=False)
class OwnedPath(RelativePath):
    """Path owned and mutable by a task proposal."""


@dataclass(frozen=True, slots=True, eq=False)
class ProtectedPath(RelativePath):
    """Read-only / immutable path protected against modification."""
