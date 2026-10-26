"""Shared Kernel: BytePayload Value Object encapsulating raw payload bytes with strict size invariants.

Guards against memory exhaustion by strictly rejecting payloads larger than MAX_PAYLOAD_BYTES (16MB).
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..exceptions import (
    InvariantViolationError,
    PayloadSizeLimitExceededError,
)
from .content_digest import ContentDigest

# Hard size limits guarding against memory exhaustion / zip bomb attacks
MAX_PAYLOAD_BYTES: int = 16 * 1024 * 1024  # 16 MB maximum single payload
MAX_STRING_LENGTH: int = 1 * 1024 * 1024  # 1 MB maximum single string field
MAX_CANDIDATE_BUDGET: int = 64  # Maximum candidates permitted in single turn run
MAX_OPERATION_BUDGET: int = 256  # Maximum operations permitted in single turn run


@dataclass(frozen=True, slots=True)
class BytePayload:
    """Enriched Value Object encapsulating raw payload bytes."""

    data: bytes
    digest: ContentDigest = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.data, (bytes, bytearray)):
            raise InvariantViolationError(f"BytePayload data must be bytes, got {type(self.data).__name__}")
        if len(self.data) > MAX_PAYLOAD_BYTES:
            raise PayloadSizeLimitExceededError(
                f"Payload size {len(self.data)} bytes exceeds maximum allowed size of {MAX_PAYLOAD_BYTES} bytes (16MB)"
            )
        object.__setattr__(self, "digest", ContentDigest.from_bytes(bytes(self.data)))
        object.__setattr__(self, "data", bytes(self.data))

    @classmethod
    def from_str(cls, text: str) -> BytePayload:
        if len(text) > MAX_STRING_LENGTH:
            raise PayloadSizeLimitExceededError(
                f"String length {len(text)} exceeds maximum allowed length of {MAX_STRING_LENGTH}"
            )
        return cls(text.encode("utf-8"))

    def as_bytes(self) -> bytes:
        return self.data

    def as_str(self, encoding: str = "utf-8") -> str:
        return self.data.decode(encoding)

    def __len__(self) -> int:
        return len(self.data)
