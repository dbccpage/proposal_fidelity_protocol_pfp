"""Railway-Oriented Programming (ROP) result monad and domain error primitives.

Zero host I/O, zero external framework imports.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Callable, Generic, List, Optional, Tuple, TypeVar, cast

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


class TerminalStatus(str, Enum):
    """PFP Canonical terminal statuses."""

    EXACT = "Exact"
    STABILIZED_SURVIVOR = "StabilizedSurvivor"
    OPEN_OBSTRUCTION = "OpenObstruction"
    REFUSED = "Refused"
    VERIFIED = "Verified"
    VERIFIED_WITH_RESIDUALS = "VerifiedWithResiduals"
    BLOCKED_BY_EVIDENCE = "BlockedByEvidence"
    NEEDS_EXTERNAL_ORACLE = "NeedsExternalOracle"
    BUDGET_EXHAUSTED = "BudgetExhausted"
    INFRASTRUCTURE_FAILURE = "InfrastructureFailure"


class RefusalCode(str, Enum):
    """PFP Canonical typed refusal codes."""

    ENUMERATION_LIMIT_EXCEEDED = "ENUMERATION_LIMIT_EXCEEDED"
    MAP_UNDEFINED = "MAP_UNDEFINED"
    CARRIER_REGRESS = "CARRIER_REGRESS"
    NILPOTENCY_BROKEN = "NILPOTENCY_BROKEN"
    DUALITY_GAP_NONZERO = "DUALITY_GAP_NONZERO"
    SYNTAX_VIOLATION = "SYNTAX_VIOLATION"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    CELL_BOUND_EXCEEDED = "CELL_BOUND_EXCEEDED"
    HOMOLOGY_CYCLE_OBSTRUCTION = "HOMOLOGY_CYCLE_OBSTRUCTION"
    TORSION_OBSTRUCTION = "TORSION_OBSTRUCTION"
    NON_INTEGRAL_BOUNDARY = "NON_INTEGRAL_BOUNDARY"
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    GATE_REJECTED = "GATE_REJECTED"
    UNFILLED_SLOTS = "UNFILLED_SLOTS"
    MISSING_GOVERNANCE = "MISSING_GOVERNANCE"
    BYTE_BUDGET_EXCEEDED = "BYTE_BUDGET_EXCEEDED"
    PARSER_ERROR = "PARSER_ERROR"
    UNKNOWN_STAGE = "UNKNOWN_STAGE"
    UNKNOWN_MODE = "UNKNOWN_MODE"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"
    UNKNOWN_DEMO = "UNKNOWN_DEMO"
    HOST_VERIFIER_UNAVAILABLE = "HOST_VERIFIER_UNAVAILABLE"
    HOST_CHECK_FAILED = "HOST_CHECK_FAILED"
    MISSING_ATTESTATION = "MISSING_ATTESTATION"
    CATALOG_UNAVAILABLE = "CATALOG_UNAVAILABLE"
    TYPING_VIOLATION = "TYPING_VIOLATION"
    CRYPTOGRAPHIC_BINDING_FAILURE = "CRYPTOGRAPHIC_BINDING_FAILURE"
    UNEARNED_VERDICT = "UNEARNED_VERDICT"

    SINGULAR_SYSTEM_OBSTRUCTION = "SINGULAR_SYSTEM_OBSTRUCTION"
    MISSING_PREMISE = "MISSING_PREMISE"
    SIGN_INVERSION = "SIGN_INVERSION"
    ARITHMETIC_ERROR = "ARITHMETIC_ERROR"
    COMPOSITE_INCLUSION = "COMPOSITE_INCLUSION"
    ORDERING_VIOLATION = "ORDERING_VIOLATION"
    BOUNDARY_OMISSION = "BOUNDARY_OMISSION"
    INVALID_VERDICT_VALUE = "INVALID_VERDICT_VALUE"
    DEDUCTION_MISMATCH = "DEDUCTION_MISMATCH"
    PREMISE_COUNT_MISMATCH = "PREMISE_COUNT_MISMATCH"
    UNGROUNDED_HALLUCINATION = "UNGROUNDED_HALLUCINATION"
    MISSING_EPISTEMIC_GROUNDING = "MISSING_EPISTEMIC_GROUNDING"
    DETERMINANT_SIGN_FLIP = "DETERMINANT_SIGN_FLIP"


@dataclass(frozen=True)
class DomainError:
    """Typed domain error for ROP failure tracks."""

    code: RefusalCode
    message: str
    stage: Optional[int] = None
    gate_name: Optional[str] = None
    authority_effect: str = "None"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, DomainError):
            return False
        return (
            self.code == other.code
            and self.message == other.message
            and self.stage == other.stage
            and self.gate_name == other.gate_name
            and self.authority_effect == other.authority_effect
        )


@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Railway-Oriented Programming (ROP) result monad."""

    _value: Optional[T]
    _error: Optional[E]
    _is_ok: bool

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, Result):
            return False
        return (
            self._is_ok == other._is_ok
            and self._value == other._value
            and self._error == other._error
        )

    @classmethod
    def ok(cls, val: T) -> Result[T, E]:
        return cls(_value=val, _error=None, _is_ok=True)

    @classmethod
    def err(cls, error: E) -> Result[T, E]:
        return cls(_value=None, _error=error, _is_ok=False)

    @property
    def is_ok(self) -> bool:
        return self._is_ok

    @property
    def is_err(self) -> bool:
        return not self._is_ok

    @property
    def value(self) -> Optional[T]:
        return self._value

    @property
    def error(self) -> Optional[E]:
        return self._error

    def unwrap(self) -> T:
        if not self._is_ok:
            raise ValueError(f"Called unwrap on Err: {self._error}")
        return cast(T, self._value)

    def unwrap_err(self) -> E:
        if self._is_ok:
            raise ValueError("Called unwrap_err on Ok")
        return cast(E, self._error)

    def unwrap_or(self, default: T) -> T:
        return cast(T, self._value) if self._is_ok else default

    def map(self, fn: Callable[[T], U]) -> Result[U, E]:
        if self._is_ok:
            return Result.ok(fn(self.unwrap()))
        return Result.err(self.unwrap_err())

    def map_err(self, fn: Callable[[E], U]) -> Result[T, U]:
        if self._is_ok:
            return Result.ok(self.unwrap())
        return Result.err(fn(self.unwrap_err()))

    def and_then(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        if self._is_ok:
            return fn(self.unwrap())
        return Result.err(self.unwrap_err())

    bind = and_then


def refuse_if(
    condition: bool,
    code: RefusalCode,
    message: str,
    stage: Optional[int] = None,
    gate_name: Optional[str] = None,
) -> Result[bool, DomainError]:
    """Helper creating a typed refusal Result if condition is true."""
    if condition:
        return Result.err(
            DomainError(
                code=code,
                message=message,
                stage=stage,
                gate_name=gate_name,
                authority_effect="None",
            )
        )
    return Result.ok(True)


def collect_results(results: List[Result[T, E]]) -> Result[Tuple[T, ...], E]:
    """Short-circuiting collector for a sequence of ROP results."""
    values: List[T] = []
    for r in results:
        if r.is_err:
            return Result.err(r.unwrap_err())
        values.append(r.unwrap())
    return Result.ok(tuple(values))


@dataclass(frozen=True)
class EvaluationVerdict:
    """Deterministic PFP evaluation verdict emitted by the host gate."""

    packet_id: str
    status: TerminalStatus
    phi1: Fraction
    gamma2: Fraction
    duality_gap: Optional[Fraction]
    evidence_ceiling: str = "LocalReplay"
    authority_effect: str = "None"
    remaining_delta: Tuple[str, ...] = ()
    refusal_code: Optional[RefusalCode] = None


@dataclass(frozen=True)
class GenesisCycleVerdict:
    """Deterministic verdict for Genesis cycle balance."""

    proposal_id: str
    is_balanced: bool
    status: TerminalStatus
    h1_free_rank: int
    torsion_coefficients: Tuple[int, ...]
    invariant_factors: Tuple[int, ...]
    boundary_preimage: Optional[Tuple[int, ...]] = None
    cocycle_witness: Optional[Tuple[int, ...]] = None
    cycle_boundary: Tuple[int, ...] = ()
    evidence_ceiling: str = "ExactIntegerSmithNormalForm"
    authority_effect: str = "None"
    refusal_code: Optional[RefusalCode] = None
    message: str = ""
