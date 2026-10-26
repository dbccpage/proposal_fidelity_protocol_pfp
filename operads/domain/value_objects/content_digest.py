"""Exact-type ContentDigest value object."""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEX_64 = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True, slots=True)
class ContentDigest:
    algorithm: str
    hex_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.algorithm, str) or isinstance(self.algorithm, bool):
            raise TypeError(f"algorithm must be a string, got {type(self.algorithm).__name__}")
        if not isinstance(self.hex_digest, str) or isinstance(self.hex_digest, bool):
            raise TypeError(f"hex_digest must be a string, got {type(self.hex_digest).__name__}")
        algo_stripped = self.algorithm.strip()
        digest_stripped = self.hex_digest.strip()
        if not algo_stripped:
            raise ValueError("algorithm must be a non-empty string")
        if not digest_stripped:
            raise ValueError("hex_digest must be a non-empty string")
        algo_lower = algo_stripped.lower()
        object.__setattr__(self, "algorithm", algo_lower)
        if algo_lower in ("sha256", "sha-256", "canonical_json_sha256"):
            if not _HEX_64.match(digest_stripped):
                raise ValueError(f"invalid sha256 hex digest: {digest_stripped}")
        object.__setattr__(self, "hex_digest", digest_stripped.lower())

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.algorithm == other.algorithm and self.hex_digest == other.hex_digest

    def __hash__(self) -> int:
        return hash((type(self), self.algorithm, self.hex_digest))

    @classmethod
    def sha256(cls, hex_digest: str) -> ContentDigest:
        return cls("sha256", hex_digest)

    @classmethod
    def empty_sha256(cls) -> ContentDigest:
        return cls("sha256", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

    def __str__(self) -> str:
        return f"{self.algorithm}:{self.hex_digest}"
