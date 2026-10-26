"""Exact-type immutable identifiers for OEWAS V3."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class _BaseId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or isinstance(self.value, bool):
            raise TypeError(f"{type(self).__name__} must be a string, got {type(self.value).__name__}")
        stripped = self.value.strip()
        if not stripped:
            raise ValueError(f"{type(self).__name__} must be a non-empty string")
        if len(stripped) > 512:
            raise ValueError(f"{type(self).__name__} exceeds maximum length of 512 characters (got {len(stripped)})")
        object.__setattr__(self, "value", stripped)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SkillId(_BaseId):
    pass


@dataclass(frozen=True, slots=True)
class OperationId(_BaseId):
    pass


@dataclass(frozen=True, slots=True)
class DocumentId(_BaseId):
    pass


@dataclass(frozen=True, slots=True)
class OperandId(_BaseId):
    pass


@dataclass(frozen=True, slots=True)
class WorkflowId(_BaseId):
    pass


@dataclass(frozen=True, slots=True)
class ColourId(_BaseId):
    pass


@dataclass(frozen=True, slots=True)
class SchemaRef(_BaseId):
    pass


@dataclass(frozen=True, slots=True)
class CorrelationId(_BaseId):
    pass


@dataclass(frozen=True, slots=True)
class CausationId(_BaseId):
    pass


@dataclass(frozen=True, slots=True)
class IdempotencyKey(_BaseId):
    pass


@dataclass(frozen=True, slots=True)
class EstateRef(_BaseId):
    pass
