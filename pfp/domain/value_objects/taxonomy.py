"""Strongly typed Domain Taxonomy and Categorical Value Objects.

AuthorityEffect: None.
Eliminates primitive obsession for domain categories, execution modes, and evaluation statuses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


from .base import ValueObject
from .task_family_tokens import TASK_FAMILY_TOKENS


VALID_TASK_FAMILIES = TASK_FAMILY_TOKENS

_DYNAMIC_TASK_FAMILIES: set[str] = set()
_TASK_FAMILY_PROVIDERS: list = []


def register_task_family_provider(provider) -> None:
    _TASK_FAMILY_PROVIDERS.append(provider)


def register_task_family_token(token: str) -> None:
    """Register an extensional task family token dynamically into the domain taxonomy."""
    _DYNAMIC_TASK_FAMILIES.add(token)


def get_valid_task_families() -> frozenset[str]:
    """Retrieve all valid bedrock and dynamically registered task family tokens."""
    families = set(VALID_TASK_FAMILIES) | _DYNAMIC_TASK_FAMILIES
    for provider in _TASK_FAMILY_PROVIDERS:
        families.update(provider())
    return frozenset(families)


VALID_EXECUTION_MODES = frozenset(
    {
        "offline_fixture",
        "live_manual_dispatch",
        "live_gateway_dispatch",
    }
)

VALID_EVALUATION_STATUSES = frozenset(
    {
        "ACCEPTED",
        "WRONG_ANSWER",
        "FALSE_CERTAINTY",
        "MALFORMED",
        "NOT_RUN",
        "REFUSED",
    }
)

VALID_TRIAL_STATUSES = frozenset(
    {
        "NOT_RUN",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "REFUSED",
        "PASS",
        "FAIL",
    }
)

VALID_SPAN_ROLES = frozenset(
    {
        "PREAMBLE",
        "GROUND_TRUTH",
        "STIMULUS",
        "PROMPT_BODY",
        "FENCE",
        "EPILOGUE",
    }
)


def _validate_token(name: str, value: Any, allowed: frozenset[str]) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be str, got {type(value).__name__}")
    if value not in allowed:
        raise ValueError(f"Invalid {name}: {value!r}. Must be one of {sorted(allowed)}")
    return value


@dataclass(frozen=True)
class TaskFamilyVO(ValueObject):
    """Strongly typed task family category."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "value", _validate_token("TaskFamilyVO", self.value, get_valid_task_families())
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ExecutionModeVO(ValueObject):
    """Strongly typed dispatch execution mode."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "value", _validate_token("ExecutionModeVO", self.value, VALID_EXECUTION_MODES)
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class EvaluationStatusVO(ValueObject):
    """Strongly typed evaluation outcome status."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _validate_token("EvaluationStatusVO", self.value, VALID_EVALUATION_STATUSES),
        )

    @property
    def is_accepted(self) -> bool:
        return self.value == "ACCEPTED"

    @property
    def is_refused(self) -> bool:
        return self.value == "REFUSED"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TrialStatusVO(ValueObject):
    """Strongly typed execution trial status."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "value", _validate_token("TrialStatusVO", self.value, VALID_TRIAL_STATUSES)
        )

    @property
    def is_terminal(self) -> bool:
        return self.value in {"COMPLETED", "FAILED", "REFUSED", "PASS", "FAIL"}

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class SpanRoleVO(ValueObject):
    """Strongly typed byte span functional role."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "value", _validate_token("SpanRoleVO", self.value, VALID_SPAN_ROLES)
        )

    def __str__(self) -> str:
        return self.value


VALID_ARITHMETIC_DOMAINS = frozenset(
    {
        "EXACT_INTEGER",
    }
)

VALID_CLAIMED_MOVES = frozenset(
    {
        "ATTACH_2CELL",
    }
)

VALID_VERIFICATION_RULES = frozenset(
    {
        "STATIC_CELL_BOUNDS_CHECK",
        "CHAIN_COMPLEX_NILPOTENCY_CHECK",
        "INTEGER_SMITH_NORMAL_FORM_CYCLE_BALANCE",
    }
)

VALID_VERIFICATION_STATUSES = frozenset(
    {
        "UNVERIFIED",
        "VERIFIED",
    }
)


@dataclass(frozen=True)
class ArithmeticDomainVO(ValueObject):
    """Strongly typed algebraic/arithmetic coefficient domain."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _validate_token("ArithmeticDomainVO", self.value, VALID_ARITHMETIC_DOMAINS),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ClaimedMoveVO(ValueObject):
    """Strongly typed topological candidate modification move."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "value", _validate_token("ClaimedMoveVO", self.value, VALID_CLAIMED_MOVES)
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class VerificationRuleVO(ValueObject):
    """Strongly typed verification rule identifier."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _validate_token("VerificationRuleVO", self.value, VALID_VERIFICATION_RULES),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class VerificationStatusVO(ValueObject):
    """Strongly typed verification status (UNVERIFIED / VERIFIED)."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _validate_token("VerificationStatusVO", self.value, VALID_VERIFICATION_STATUSES),
        )

    @property
    def is_verified(self) -> bool:
        return self.value == "VERIFIED"

    def __str__(self) -> str:
        return self.value
