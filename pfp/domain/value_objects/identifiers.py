"""Strongly typed Domain Identifier Value Objects.

AuthorityEffect: None.
Eliminates primitive obsession for entity keys, digests, and checkers.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from .base import ValueObject

_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]+$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_NF_ID_PATTERN = re.compile(r"^nf\.[a-z0-9_]+\.[a-z0-9_]+$")

CANONICAL_CHECKERS = frozenset({
    "PFP-01-EXACT-LINALG",
    "PFP-02-EXACT-PRIMES",
    "PFP-03-EXACT-FOL-DEDUCTION",
    "PFP-04-EXACT-EPISTEMIC-REFUSAL",
    "PFP-05-EXACT-2X2-DETERMINANT",
})


def _validate_string_id(name: str, value: Any, min_len: int = 1, max_len: int = 128) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be a str, got {type(value).__name__}")
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{name} cannot be empty or whitespace-only")
    if len(value) != len(stripped):
        raise ValueError(f"{name} cannot have leading or trailing whitespace: {value!r}")
    if len(value) < min_len or len(value) > max_len:
        raise ValueError(f"{name} length must be between {min_len} and {max_len}, got {len(value)}")
    if not _ID_PATTERN.match(value):
        raise ValueError(f"{name} contains invalid characters: {value!r}")
    return value


@dataclass(frozen=True)
class PilotId(ValueObject):
    """Strongly typed Pilot Identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_string_id("PilotId", self.value))

    def __str__(self) -> str:
        return self.value

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        try:
            from pydantic_core import core_schema
            return core_schema.no_info_after_validator_function(
                cls,
                core_schema.str_schema(),
            )
        except ImportError:
            return None


@dataclass(frozen=True)
class PromptId(ValueObject):
    """Strongly typed Prompt Identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_string_id("PromptId", self.value))

    def __str__(self) -> str:
        return self.value

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        try:
            from pydantic_core import core_schema
            return core_schema.no_info_after_validator_function(
                cls,
                core_schema.str_schema(),
            )
        except ImportError:
            return None


@dataclass(frozen=True)
class RequestId(ValueObject):
    """Strongly typed Request Identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_string_id("RequestId", self.value))

    def __str__(self) -> str:
        return self.value

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        try:
            from pydantic_core import core_schema
            return core_schema.no_info_after_validator_function(
                cls,
                core_schema.str_schema(),
            )
        except ImportError:
            return None


@dataclass(frozen=True)
class CheckerIdVO(ValueObject):
    """Strongly typed Checker Identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_string_id("CheckerIdVO", self.value))

    @property
    def is_canonical(self) -> bool:
        return self.value in CANONICAL_CHECKERS

    def __str__(self) -> str:
        return self.value

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        try:
            from pydantic_core import core_schema
            return core_schema.no_info_after_validator_function(
                cls,
                core_schema.str_schema(),
            )
        except ImportError:
            return None


@dataclass(frozen=True)
class Sha256Digest(ValueObject):
    """Strongly typed lowercase SHA-256 Digest."""

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str:
            raise TypeError(f"Sha256Digest must be a str, got {type(self.value).__name__}")
        if not _SHA256_PATTERN.match(self.value):
            raise ValueError(
                f"Sha256Digest must be exactly 64 lowercase hexadecimal characters, got {self.value!r}"
            )

    def __str__(self) -> str:
        return self.value

    @classmethod
    def compute(cls, data: bytes) -> Sha256Digest:
        import hashlib
        return cls(hashlib.sha256(data).hexdigest())

    @classmethod
    def from_bytes(cls, data: bytes) -> Sha256Digest:
        return cls.compute(data)

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        try:
            from pydantic_core import core_schema
            return core_schema.no_info_after_validator_function(
                cls,
                core_schema.str_schema(),
            )
        except ImportError:
            return None


@dataclass(frozen=True)
class NormalFormId(ValueObject):
    """Strongly typed Normal Form Identifier matching nf.<family>.<slug>."""

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str:
            raise TypeError(f"NormalFormId must be a str, got {type(self.value).__name__}")
        if not _NF_ID_PATTERN.match(self.value):
            raise ValueError(
                f"NormalFormId must follow pattern 'nf.<family>.<slug>', got {self.value!r}"
            )

    def __str__(self) -> str:
        return self.value

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        try:
            from pydantic_core import core_schema
            return core_schema.no_info_after_validator_function(
                cls,
                core_schema.str_schema(),
            )
        except ImportError:
            return None


@dataclass(frozen=True)
class ProblemId(ValueObject):
    """Strongly typed Cycle Balance Problem Identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_string_id("ProblemId", self.value))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class CandidateId(ValueObject):
    """Strongly typed Cycle Balance Candidate Proposal Identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_string_id("CandidateId", self.value))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class VerifierId(ValueObject):
    """Strongly typed Cycle Balance Verifier Contract Identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_string_id("VerifierId", self.value))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ReceiptId(ValueObject):
    """Strongly typed Cycle Balance Receipt Identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_string_id("ReceiptId", self.value))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class CaseId(ValueObject):
    """Strongly typed Problem Case Identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _validate_string_id("CaseId", self.value))

    def __str__(self) -> str:
        return self.value

