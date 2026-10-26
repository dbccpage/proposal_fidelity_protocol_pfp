"""Strongly Typed Cryptographic Digest Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar, Pattern, Self

from .digest_kind import DigestKind
from .domain_invariant_error import DomainInvariantError

_HEX_40_64_REGEX = re.compile(r"^[0-9a-f]{40}$|^[0-9a-f]{64}$")
_HEX_64_REGEX = re.compile(r"^[0-9a-f]{64}$")
_HEX_64_128_REGEX = re.compile(r"^[0-9a-f]{64,128}$")


@dataclass(frozen=True, slots=True, eq=False)
class Digest:
    """Strongly-typed domain cryptographic hash Value Object parameterized by DigestKind."""

    value: str
    kind: DigestKind = DigestKind.SHA256

    PATTERN: ClassVar[Pattern[str]] = _HEX_64_REGEX

    def __post_init__(self) -> None:
        if type(self.value) is not str:
            raise DomainInvariantError(
                "INVALID_DIGEST_TYPE",
                f"Digest value must be str, got {type(self.value).__name__}",
            )
        val = self.value.strip().lower()
        if not val:
            raise DomainInvariantError(
                "EMPTY_DIGEST", "Digest must not be empty or whitespace only"
            )

        if self.kind in (
            DigestKind.GIT_OID,
            DigestKind.GIT_COMMIT,
            DigestKind.GIT_TREE,
            DigestKind.GIT_BLOB,
        ):
            pat = _HEX_40_64_REGEX
        elif self.kind == DigestKind.SIGNATURE:
            pat = _HEX_64_128_REGEX
        else:
            pat = _HEX_64_REGEX

        if not pat.match(val):
            raise DomainInvariantError(
                "INVALID_DIGEST_PATTERN",
                f"Invalid {self.kind.value} digest {val!r}: must match pattern {pat.pattern}",
            )

        if val != self.value:
            object.__setattr__(self, "value", val)

    @classmethod
    def from_str(
        cls: type[Self], val: str | Self, kind: DigestKind | None = None
    ) -> Self:
        if isinstance(val, cls):
            if kind is not None and val.kind != kind:
                raise DomainInvariantError(
                    "DIGEST_KIND_MISMATCH", f"Expected kind {kind}, got {val.kind}"
                )
            return val
        if type(val) is not str:
            raise DomainInvariantError(
                "INVALID_DIGEST_COERCION",
                f"Digest.from_str requires an exact str, got {type(val).__name__}",
            )
        clean = val.strip().lower()
        if kind is None:
            if len(clean) == 40:
                target_kind = DigestKind.GIT_OID
            else:
                target_kind = DigestKind.SHA256
        else:
            target_kind = kind
        return cls(value=val, kind=target_kind)

    # Factory constructors
    @classmethod
    def sha256(cls, val: str | Self) -> Self:
        return cls.from_str(val, DigestKind.SHA256)

    @classmethod
    def policy(cls, val: str | Self) -> Self:
        return cls.from_str(val, DigestKind.POLICY)

    @classmethod
    def signature(cls, val: str | Self) -> Self:
        return cls.from_str(val, DigestKind.SIGNATURE)

    @classmethod
    def manifest(cls, val: str | Self) -> Self:
        return cls.from_str(val, DigestKind.MANIFEST)

    @classmethod
    def git_oid(cls, val: str | Self) -> Self:
        return cls.from_str(val, DigestKind.GIT_OID)

    @classmethod
    def git_commit(cls, val: str | Self) -> Self:
        return cls.from_str(val, DigestKind.GIT_COMMIT)

    @classmethod
    def git_tree(cls, val: str | Self) -> Self:
        return cls.from_str(val, DigestKind.GIT_TREE)

    @classmethod
    def git_blob(cls, val: str | Self) -> Self:
        return cls.from_str(val, DigestKind.GIT_BLOB)

    def as_bytes(self) -> bytes:
        return bytes.fromhex(self.value)

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.kind == other.kind and self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.kind, self.value))

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Digest({self.value!r}, kind={self.kind.value})"
