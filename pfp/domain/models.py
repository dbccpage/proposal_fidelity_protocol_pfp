"""Domain models and value objects for the Symbol Game engine.

Enforces exact-type equality Invariant:
type(self) is type(other) in __eq__ and composite __hash__.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from types import MappingProxyType
from typing import Any, Mapping, Sequence, Tuple

from .exact.q import Q
from .exceptions import ForbiddenAuthorityError
from .shared_kernel.authority_effect import AuthorityEffect, validate_authority_effect_none



class StepVerdict(str, Enum):
    """Discrete step verdict in Symbol Game retraction manifold."""

    SELECT = "SELECT"
    HOLD = "HOLD"
    EXACT = "EXACT"
    DESCENT = "DESCENT"
    REFUSAL = "REFUSAL"
    FAIL = "FAIL"


@dataclass(frozen=True)
class SymbolToken:
    """Discrete symbol token with exact-type equality and dimension weighting."""

    token_id: str
    symbol_text: str
    dimension_weight: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.token_id, str) or not self.token_id.strip():
            raise ValueError("token_id must be a non-empty string")
        if not isinstance(self.symbol_text, str):
            raise TypeError("symbol_text must be a string")
        if not isinstance(self.dimension_weight, (int, float)) or self.dimension_weight < 0:
            raise ValueError("dimension_weight must be a non-negative float")
        object.__setattr__(self, "dimension_weight", float(self.dimension_weight))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.token_id == other.token_id
            and self.symbol_text == other.symbol_text
            and self.dimension_weight == other.dimension_weight
        )

    def __hash__(self) -> int:
        return hash((type(self), self.token_id, self.symbol_text, self.dimension_weight))


@dataclass(frozen=True)
class SymbolGameEnvelope:
    """Task-level retraction envelope with non-empty task binding."""

    task_id: str
    initial_input: str
    sparse_dimension: int = 28
    constraints: Tuple[str, ...] = ()
    authority_effect: AuthorityEffect | str = AuthorityEffect.NONE

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise ValueError("task_id must be a non-empty string")
        if not isinstance(self.initial_input, str):
            raise TypeError("initial_input must be a string")
        if not isinstance(self.sparse_dimension, int) or self.sparse_dimension <= 0:
            raise ValueError("sparse_dimension must be a positive integer")
        if not isinstance(self.constraints, tuple):
            object.__setattr__(self, "constraints", tuple(self.constraints))
        try:
            auth = (
                self.authority_effect
                if isinstance(self.authority_effect, AuthorityEffect)
                else AuthorityEffect(str(self.authority_effect))
            )
            validate_authority_effect_none(auth)
        except (ValueError, ForbiddenAuthorityError) as ex:
            raise ForbiddenAuthorityError(
                f"AuthorityEffect violation: expected 'None', got {self.authority_effect!r}"
            ) from ex
        object.__setattr__(self, "authority_effect", auth)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.task_id == other.task_id
            and self.initial_input == other.initial_input
            and self.sparse_dimension == other.sparse_dimension
            and self.constraints == other.constraints
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.task_id,
            self.initial_input,
            self.sparse_dimension,
            self.constraints,
            self.authority_effect,
        ))


def _coerce_outcome_value(val: Any, field_name: str) -> float | Fraction:
    if isinstance(val, Q):
        return Fraction(val.num, val.den)
    if isinstance(val, (int, float, Fraction)):
        return val
    raise TypeError(f"{field_name} must be float or Fraction, got {type(val).__name__}")


@dataclass(frozen=True)
class SymbolGameStepOutcome:
    """Discrete step outcome with typed StepVerdict and authority invariants."""

    step_id: str
    purity: Q | float | Fraction
    l1_obstruction: Q | float | Fraction
    is_exact: bool
    verdict: StepVerdict | str
    evidence_sha256: str
    authority_effect: AuthorityEffect | str = AuthorityEffect.NONE

    def __post_init__(self) -> None:
        if not isinstance(self.step_id, str) or not self.step_id.strip():
            raise ValueError("step_id must be a non-empty string")
        purity_val = _coerce_outcome_value(self.purity, "purity")
        l1_val = _coerce_outcome_value(self.l1_obstruction, "l1_obstruction")
        object.__setattr__(self, "purity", purity_val)
        object.__setattr__(self, "l1_obstruction", l1_val)
        object.__setattr__(self, "is_exact", bool(self.is_exact))

        v = self.verdict if isinstance(self.verdict, StepVerdict) else StepVerdict(str(self.verdict))
        object.__setattr__(self, "verdict", v)

        try:
            auth = (
                self.authority_effect
                if isinstance(self.authority_effect, AuthorityEffect)
                else AuthorityEffect(str(self.authority_effect))
            )
            validate_authority_effect_none(auth)
        except (ValueError, ForbiddenAuthorityError) as ex:
            raise ForbiddenAuthorityError(
                f"AuthorityEffect violation: expected 'None', got {self.authority_effect!r}"
            ) from ex
        object.__setattr__(self, "authority_effect", auth)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.step_id == other.step_id
            and self.purity == other.purity
            and self.l1_obstruction == other.l1_obstruction
            and self.is_exact == other.is_exact
            and self.verdict == other.verdict
            and self.evidence_sha256 == other.evidence_sha256
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.step_id,
            self.purity,
            self.l1_obstruction,
            self.is_exact,
            self.verdict,
            self.evidence_sha256,
            self.authority_effect,
        ))


def _exact_nonnegative(value: object, name: str) -> Fraction:
    if type(value) is bool or type(value) is float:
        raise TypeError(f"{name} must be an exact non-negative rational")
    if type(value) is int:
        parsed = Fraction(value)
    elif type(value) is Fraction:
        parsed = value
    elif type(value) is str:
        parsed = Fraction(value)
    else:
        raise TypeError(f"{name} must be an exact non-negative rational")
    if parsed < 0:
        raise ValueError(f"{name} must be a non-negative rational")
    return parsed


@dataclass(frozen=True)
class ObstructionScore:
    """Obstruction score measuring boundary defect Phi_1 and cycle obstruction Gamma_2."""

    gamma_2: Fraction
    phi_1: Fraction
    active_count: int
    active_obstruction_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "gamma_2", _exact_nonnegative(self.gamma_2, "gamma_2"))
        object.__setattr__(self, "phi_1", _exact_nonnegative(self.phi_1, "phi_1"))
        if type(self.active_count) is not int or self.active_count < 0:
            raise ValueError("active_count must be a non-negative int")
        if not isinstance(self.active_obstruction_ids, tuple):
            object.__setattr__(self, "active_obstruction_ids", tuple(self.active_obstruction_ids))

    @property
    def is_exact(self) -> bool:
        return self.gamma_2 == 0 and self.phi_1 == 0 and self.active_count == 0

    def strictly_improves(self, prior: ObstructionScore) -> bool:
        if type(self) is not type(prior):
            raise TypeError(f"Cannot compare ObstructionScore with {type(prior)}")
        if self.phi_1 < prior.phi_1 and self.gamma_2 <= prior.gamma_2:
            return True
        if self.phi_1 <= prior.phi_1 and self.gamma_2 < prior.gamma_2:
            return True
        return (
            self.phi_1 <= prior.phi_1
            and self.gamma_2 <= prior.gamma_2
            and self.active_count < prior.active_count
        )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.gamma_2 == other.gamma_2
            and self.phi_1 == other.phi_1
            and self.active_count == other.active_count
            and self.active_obstruction_ids == other.active_obstruction_ids
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.gamma_2,
            self.phi_1,
            self.active_count,
            self.active_obstruction_ids,
        ))



@dataclass(frozen=True)
class ProblemReductionResult:
    """Problem reduction outcome with immutable artifacts mapping and exact score."""

    task_id: str
    status: str
    steps_executed: int
    final_score: ObstructionScore
    is_resolved: bool
    artifacts: Mapping[str, Any] | Tuple[Tuple[str, Any], ...] = ()
    authority_effect: AuthorityEffect | str = AuthorityEffect.NONE

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise ValueError("task_id must be a non-empty string")
        if not isinstance(self.steps_executed, int) or self.steps_executed < 0:
            raise ValueError("steps_executed must be a non-negative int")
        if not isinstance(self.final_score, ObstructionScore):
            raise TypeError("final_score must be an ObstructionScore")
        object.__setattr__(self, "is_resolved", bool(self.is_resolved))

        if isinstance(self.artifacts, dict):
            object.__setattr__(self, "artifacts", MappingProxyType(dict(self.artifacts)))
        elif isinstance(self.artifacts, (list, tuple)):
            object.__setattr__(self, "artifacts", MappingProxyType(dict(self.artifacts)))
        elif not isinstance(self.artifacts, MappingProxyType):
            object.__setattr__(self, "artifacts", MappingProxyType({}))

        try:
            auth = (
                self.authority_effect
                if isinstance(self.authority_effect, AuthorityEffect)
                else AuthorityEffect(str(self.authority_effect))
            )
            validate_authority_effect_none(auth)
        except (ValueError, ForbiddenAuthorityError) as ex:
            raise ForbiddenAuthorityError(
                f"AuthorityEffect violation: expected 'None', got {self.authority_effect!r}"
            ) from ex
        object.__setattr__(self, "authority_effect", auth)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.task_id == other.task_id
            and self.status == other.status
            and self.steps_executed == other.steps_executed
            and self.final_score == other.final_score
            and self.is_resolved == other.is_resolved
            and dict(self.artifacts) == dict(other.artifacts)
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.task_id,
            self.status,
            self.steps_executed,
            self.final_score,
            self.is_resolved,
            tuple(sorted(self.artifacts.items())),
            self.authority_effect,
        ))


__all__ = [
    "AuthorityEffect",
    "ObstructionScore",
    "ProblemReductionResult",
    "StepVerdict",
    "SymbolGameEnvelope",
    "SymbolGameStepOutcome",
    "SymbolToken",
]
