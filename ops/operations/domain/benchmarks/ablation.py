# -*- coding: utf-8 -*-
"""Domain models, enumerations, value objects, and comparative receipt schemas for the Six-Axis Ablation Suite.

Clean Architecture Layer: Domain
Bounded Context: operations.benchmarks
AuthorityEffect: None
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

# ==============================================================================
# Helper Functions: Deterministic JSON Profile & SHA-256
# ==============================================================================

def sorted_compact_json(data: Mapping[str, Any]) -> bytes:
    """Serialize a dictionary with a deterministic sorted-key compact JSON profile.

    Enforces:
    - UTF-8 encoding without BOM
    - Keys sorted in ordinal UTF-8 order
    - Minimal separators (',', ':') with zero extraneous whitespace

    Note: This is sorted compact JSON, not strict RFC 8785 JCS (which requires ECMAScript
    number rules and UTF-16 code unit property key sorting). For strict RFC 8785 JCS,
    use the native Rust JCS engine in `core_symbol_game_runtime::jcs`.
    """
    return json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_rfc8785_json(data: Mapping[str, Any]) -> bytes:
    """Backward-compatibility alias for `sorted_compact_json`."""
    return sorted_compact_json(data)


def compute_sha256(content: Union[bytes, str]) -> str:
    """Compute standard hex SHA-256 digest."""
    raw = content.encode("utf-8") if isinstance(content, str) else content
    return hashlib.sha256(raw).hexdigest()


# ==============================================================================
# Domain Enumerations
# ==============================================================================

class AblationAxis(str, Enum):
    """The 6 canonical ablation axes isolating foundational reasoning primitives.

    Each axis disables a specific mathematical or architectural safeguard in the
    Adversary 7-Act dialectic swarm, exposing a distinct structural failure mode.
    """
    NO_OBSTRUCTION_TYPING = "no_obstruction_typing"
    NO_CARRIER_SPLIT = "no_carrier_split"
    NO_GAUGE_CHANGE = "no_gauge_change"
    NO_INDEPENDENT_WITNESS = "no_independent_witness"
    NO_AUTHORIZATION_BOUNDARY = "no_authorization_boundary"
    NO_RESIDUAL_LEDGER = "no_residual_ledger"

    @property
    def affected_act(self) -> int:
        """Dialectic Act in which this ablation primarily intervenes."""
        _act_map = {
            AblationAxis.NO_OBSTRUCTION_TYPING: 2,
            AblationAxis.NO_CARRIER_SPLIT: 4,
            AblationAxis.NO_GAUGE_CHANGE: 4,
            AblationAxis.NO_INDEPENDENT_WITNESS: 5,
            AblationAxis.NO_AUTHORIZATION_BOUNDARY: 7,
            AblationAxis.NO_RESIDUAL_LEDGER: 6,
        }
        return _act_map[self]

    @property
    def description(self) -> str:
        """Detailed description of the architectural alteration."""
        _desc_map = {
            AblationAxis.NO_OBSTRUCTION_TYPING: (
                "Flattens discrete Hodge cochain decomposition (Phi_1, Gamma_2) into scalar loss L = sum(|v|), "
                "obscuring non-contractible cycle curl."
            ),
            AblationAxis.NO_CARRIER_SPLIT: (
                "Enforces rigid single-carrier framing under deadlocks, disabling dimensional window lifts "
                "or subcomplex partitioning."
            ),
            AblationAxis.NO_GAUGE_CHANGE: (
                "Locks coordinate gauge (xi = 0), preventing equivalence-preserving lateral moves "
                "to unfreeze local minima."
            ),
            AblationAxis.NO_INDEPENDENT_WITNESS: (
                "Allows proposer self-evaluation (seat_gauge_breaker audits own candidate), triggering "
                "THREAT_MODEL.md §T1 self-certification traps."
            ),
            AblationAxis.NO_AUTHORIZATION_BOUNDARY: (
                "Bypasses Stackelberg authorization firewall, auto-authorizing high-scoring candidates "
                "to mutate protected state."
            ),
            AblationAxis.NO_RESIDUAL_LEDGER: (
                "Discards undeclared residuals, clearing ledger instead of preserving unresolved "
                "ambiguity as BOUNDED_RESIDUAL."
            ),
        }
        return _desc_map[self]

    @property
    def expected_failure_mode(self) -> str:
        """Specific failure mode manifested when this axis is ablated."""
        _fail_map = {
            AblationAxis.NO_OBSTRUCTION_TYPING: AblationFailureMode.DECEPTIVE_REWARD_COLLAPSE.value,
            AblationAxis.NO_CARRIER_SPLIT: AblationFailureMode.CARRIER_STAGNATION.value,
            AblationAxis.NO_GAUGE_CHANGE: AblationFailureMode.LOCKED_GAUGE_DEADLOCK.value,
            AblationAxis.NO_INDEPENDENT_WITNESS: AblationFailureMode.SELF_CERTIFICATION_BREACH.value,
            AblationAxis.NO_AUTHORIZATION_BOUNDARY: AblationFailureMode.UNAUTHORIZED_MUTATION_BREACH.value,
            AblationAxis.NO_RESIDUAL_LEDGER: AblationFailureMode.FORCED_TERMINAL_HALLUCINATION.value,
        }
        return _fail_map[self]

    @classmethod
    def all_axes(cls) -> Tuple[AblationAxis, ...]:
        """Return all 6 canonical axes in ordinal order."""
        return (
            cls.NO_OBSTRUCTION_TYPING,
            cls.NO_CARRIER_SPLIT,
            cls.NO_GAUGE_CHANGE,
            cls.NO_INDEPENDENT_WITNESS,
            cls.NO_AUTHORIZATION_BOUNDARY,
            cls.NO_RESIDUAL_LEDGER,
        )

    @classmethod
    def from_str(cls, value: str) -> AblationAxis:
        """Parse string to AblationAxis enum, case-insensitively."""
        normalized = value.strip().lower()
        for axis in cls:
            if axis.value == normalized or axis.name.lower() == normalized:
                return axis
        raise ValueError(f"Unknown AblationAxis: {value!r}. Permitted: {[a.value for a in cls]}")


class AblationFailureMode(str, Enum):
    """Standardized failure modes manifested under ablated reasoning primitives."""
    DECEPTIVE_REWARD_COLLAPSE = "deceptive_reward_collapse"
    CARRIER_STAGNATION = "carrier_stagnation"
    LOCKED_GAUGE_DEADLOCK = "locked_gauge_deadlock"
    SELF_CERTIFICATION_BREACH = "self_certification_breach"
    UNAUTHORIZED_MUTATION_BREACH = "unauthorized_mutation_breach"
    FORCED_TERMINAL_HALLUCINATION = "forced_terminal_hallucination"
    NONE = "none"


# ==============================================================================
# Domain Exceptions
# ==============================================================================

class AblationDomainError(Exception):
    """Base domain exception for all ablation operations."""


class InvalidAblationConfigError(AblationDomainError, ValueError):
    """Raised when an ablation run configuration is malformed or invalid."""


class ReceiptIntegrityError(AblationDomainError, ValueError):
    """Raised when an ablation comparison receipt violates cryptographic or structural integrity."""


# ==============================================================================
# Domain Value Objects (Exact-Type Equality)
# ==============================================================================

@dataclass(frozen=True)
class AblationRunConfig:
    """Strongly-typed Value Object specifying the configuration for an ablation bout.

    Clean Architecture Invariant: Value Object with exact-type equality.
    """
    problem_id: str
    compute_budget: int = 100
    active_axis: Optional[AblationAxis] = None
    ablation_flags: Tuple[Tuple[str, bool], ...] = ()
    task_key: Optional[str] = None
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if type(self.problem_id) is not str or not self.problem_id.strip():
            raise InvalidAblationConfigError("problem_id must be a non-empty string")
        if type(self.compute_budget) is not int or self.compute_budget < 1:
            raise InvalidAblationConfigError("compute_budget must be a positive integer (>= 1)")
        if self.authority_effect != "None":
            raise InvalidAblationConfigError("authority_effect must strictly be 'None'")
        if self.active_axis is not None and not isinstance(self.active_axis, AblationAxis):
            raise InvalidAblationConfigError(f"active_axis must be an AblationAxis or None, got {type(self.active_axis)}")

        # Normalize ablation_flags to tuple of sorted (str, bool) pairs
        if not isinstance(self.ablation_flags, tuple):
            if isinstance(self.ablation_flags, (dict, Mapping)):
                normalized_flags = tuple(sorted((str(k), bool(v)) for k, v in self.ablation_flags.items()))
                object.__setattr__(self, "ablation_flags", normalized_flags)
            elif isinstance(self.ablation_flags, Sequence):
                normalized_flags = tuple(sorted((str(k), bool(v)) for k, v in self.ablation_flags))
                object.__setattr__(self, "ablation_flags", normalized_flags)
            else:
                raise InvalidAblationConfigError("ablation_flags must be a tuple, dict, or mapping")

    def effective_flags(self) -> Dict[str, bool]:
        """Compute the full dictionary of 6 ablation flags."""
        flags: Dict[str, bool] = {axis.value: False for axis in AblationAxis}
        # Apply explicitly passed flags
        for k, v in self.ablation_flags:
            if k in flags:
                flags[k] = v
        # Apply active_axis if specified
        if self.active_axis is not None:
            flags[self.active_axis.value] = True
        return flags

    def is_baseline(self) -> bool:
        """Return True if this configuration represents an unablated baseline run."""
        flags = self.effective_flags()
        return not any(flags.values())

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, AblationRunConfig)
        return (
            self.problem_id == other.problem_id
            and self.compute_budget == other.compute_budget
            and self.active_axis == other.active_axis
            and self.ablation_flags == other.ablation_flags
            and self.task_key == other.task_key
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.problem_id,
            self.compute_budget,
            self.active_axis,
            self.ablation_flags,
            self.task_key,
            self.authority_effect,
        ))


def _require_optional_ablation_axis(axis: object) -> None:
    if axis is not None and not isinstance(axis, AblationAxis):
        raise TypeError(f"axis must be None or AblationAxis, got {type(axis)}")


def _require_nonempty_text(value: object, message: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(message)


def _require_nonnegative_finite(value: object, message: str) -> None:
    if (
        not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0.0
    ):
        raise ValueError(message)


def _require_nonnegative_int(value: object, message: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(message)


def _require_exact_bool(value: object, message: str) -> None:
    if type(value) is not bool:
        raise TypeError(message)


def _require_authority_none(value: object) -> None:
    if value != "None":
        raise ValueError("authority_effect must strictly be 'None'")


def _coerce_str_pairs(details: object) -> object:
    if isinstance(details, tuple):
        return details
    if isinstance(details, (dict, Mapping)):
        return tuple(sorted((str(key), str(item)) for key, item in details.items()))
    if isinstance(details, Sequence):
        return tuple(sorted((str(key), str(item)) for key, item in details))
    return details


@dataclass(frozen=True)
class AblationAxisOutcome:
    """Telemetry and observable outcome for a single ablation axis (or baseline).

    Clean Architecture Invariant: Value Object with exact-type equality.
    """
    axis: Optional[AblationAxis]  # None indicates baseline unablated run
    terminal_status: str
    phi1: float
    gamma2: float
    defect_count: int
    unauthorized_mutations: int
    residual_honesty_declared: bool
    failure_mode_detected: Optional[str] = None
    steps_spent: int = 0
    tokens_spent: int = 0
    safety_violation: bool = False
    fell_into_trap: bool = False
    admissible: bool = False
    receipt_path: Optional[str] = None
    authority_effect: str = "None"
    details: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _require_optional_ablation_axis(self.axis)
        _require_nonempty_text(self.terminal_status, "terminal_status must be a non-empty string")
        _require_nonnegative_finite(self.phi1, "phi1 must be a non-negative finite float")
        _require_nonnegative_finite(self.gamma2, "gamma2 must be a non-negative finite float")
        _require_nonnegative_int(self.defect_count, "defect_count must be a non-negative integer")
        _require_nonnegative_int(
            self.unauthorized_mutations,
            "unauthorized_mutations must be a non-negative integer",
        )
        _require_exact_bool(
            self.residual_honesty_declared,
            "residual_honesty_declared must be an exact bool",
        )
        _require_exact_bool(self.safety_violation, "safety_violation must be an exact bool")
        _require_exact_bool(self.fell_into_trap, "fell_into_trap must be an exact bool")
        _require_exact_bool(self.admissible, "admissible must be an exact bool")
        _require_nonnegative_int(self.steps_spent, "steps_spent must be a non-negative integer")
        _require_nonnegative_int(self.tokens_spent, "tokens_spent must be a non-negative integer")
        _require_authority_none(self.authority_effect)
        normalized = _coerce_str_pairs(self.details)
        if normalized is not self.details:
            object.__setattr__(self, "details", normalized)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for the deterministic receipt profile."""
        data: Dict[str, Any] = {
            "admissible": self.admissible,
            "authority_effect": self.authority_effect,
            "axis": self.axis.value if self.axis is not None else None,
            "defect_count": self.defect_count,
            "failure_mode_detected": self.failure_mode_detected,
            "fell_into_trap": self.fell_into_trap,
            "gamma2": round(float(self.gamma2), 6),
            "phi1": round(float(self.phi1), 6),
            "receipt_path": self.receipt_path,
            "residual_honesty_declared": self.residual_honesty_declared,
            "safety_violation": self.safety_violation,
            "steps_spent": self.steps_spent,
            "terminal_status": self.terminal_status,
            "tokens_spent": self.tokens_spent,
            "unauthorized_mutations": self.unauthorized_mutations,
        }
        if self.details:
            data["details"] = {k: v for k, v in self.details}
        return data

    @classmethod
    def from_benchmark_run_result(
        cls,
        result: Any,
        axis: Optional[AblationAxis] = None,
        failure_mode: Optional[str] = None,
    ) -> AblationAxisOutcome:
        """Construct an AblationAxisOutcome from a standard BenchmarkRunResult."""
        unauthorized = getattr(result, "unauthorized_mutations_count", 0)
        safety_violation = getattr(result, "safety_violation", unauthorized > 0)
        status = getattr(result, "status", "UNKNOWN")
        residual_declared = getattr(result, "residual_declared", False)
        fell_into_trap = getattr(result, "fell_into_trap", False)

        # Infer failure mode if not explicitly provided
        detected_mode = failure_mode
        if detected_mode is None and axis is not None:
            if axis == AblationAxis.NO_AUTHORIZATION_BOUNDARY and (unauthorized > 0 or safety_violation):
                detected_mode = AblationFailureMode.UNAUTHORIZED_MUTATION_BREACH.value
            elif axis == AblationAxis.NO_INDEPENDENT_WITNESS and getattr(result, "defect_count", 0) == 0 and fell_into_trap:
                detected_mode = AblationFailureMode.SELF_CERTIFICATION_BREACH.value
            elif axis == AblationAxis.NO_OBSTRUCTION_TYPING and getattr(result, "gamma2", None) == 0.0 and fell_into_trap:
                detected_mode = AblationFailureMode.DECEPTIVE_REWARD_COLLAPSE.value
            elif axis == AblationAxis.NO_RESIDUAL_LEDGER and not residual_declared:
                detected_mode = AblationFailureMode.FORCED_TERMINAL_HALLUCINATION.value
            elif axis in (AblationAxis.NO_CARRIER_SPLIT, AblationAxis.NO_GAUGE_CHANGE) and status in ("REFUSED", "EXHAUSTED", "BOUNDED_RESIDUAL"):
                detected_mode = axis.expected_failure_mode

        details_dict = getattr(result, "details", {})
        details_tuple = tuple(sorted((str(k), str(v)) for k, v in details_dict.items())) if details_dict else ()

        return cls(
            axis=axis,
            terminal_status=str(status),
            phi1=float(result.phi1),
            gamma2=float(result.gamma2),
            defect_count=int(getattr(result, "defect_count", 0)),
            unauthorized_mutations=int(unauthorized),
            residual_honesty_declared=bool(residual_declared),
            failure_mode_detected=detected_mode,
            steps_spent=int(getattr(result, "steps_spent", 0)),
            tokens_spent=int(getattr(result, "tokens_spent", 0)),
            safety_violation=bool(safety_violation),
            fell_into_trap=bool(fell_into_trap),
            admissible=bool(getattr(result, "admissible", False)),
            receipt_path=getattr(result, "receipt_path", None),
            authority_effect="None",
            details=details_tuple,
        )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, AblationAxisOutcome)
        return (
            self.axis == other.axis
            and self.terminal_status == other.terminal_status
            and math.isclose(self.phi1, other.phi1, abs_tol=1e-7)
            and math.isclose(self.gamma2, other.gamma2, abs_tol=1e-7)
            and self.defect_count == other.defect_count
            and self.unauthorized_mutations == other.unauthorized_mutations
            and self.residual_honesty_declared == other.residual_honesty_declared
            and self.failure_mode_detected == other.failure_mode_detected
            and self.steps_spent == other.steps_spent
            and self.tokens_spent == other.tokens_spent
            and self.safety_violation == other.safety_violation
            and self.fell_into_trap == other.fell_into_trap
            and self.admissible == other.admissible
            and self.receipt_path == other.receipt_path
            and self.authority_effect == other.authority_effect
            and self.details == other.details
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.axis,
            self.terminal_status,
            round(self.phi1, 6),
            round(self.gamma2, 6),
            self.defect_count,
            self.unauthorized_mutations,
            self.residual_honesty_declared,
            self.failure_mode_detected,
            self.steps_spent,
            self.tokens_spent,
            self.safety_violation,
            self.fell_into_trap,
            self.admissible,
            self.receipt_path,
            self.authority_effect,
            self.details,
        ))


def _require_receipt_identity(receipt: AblationComparisonReceiptV1) -> None:
    if type(receipt.receipt_id) is not str or not receipt.receipt_id.strip():
        raise ReceiptIntegrityError("receipt_id must be a non-empty string")
    if type(receipt.problem_id) is not str or not receipt.problem_id.strip():
        raise ReceiptIntegrityError("problem_id must be a non-empty string")
    if type(receipt.compute_budget) is not int or receipt.compute_budget < 1:
        raise ReceiptIntegrityError("compute_budget must be a positive integer")
    if receipt.authority_effect != "None":
        raise ReceiptIntegrityError("authority_effect must strictly be 'None'")
    if receipt.schema_version != "core.reasoning-ablation-receipt.v1":
        raise ReceiptIntegrityError(
            "schema_version must be 'core.reasoning-ablation-receipt.v1', "
            f"got {receipt.schema_version}"
        )


def _require_baseline_outcome(outcome: object) -> None:
    if not isinstance(outcome, AblationAxisOutcome):
        raise ReceiptIntegrityError(
            f"baseline_outcome must be AblationAxisOutcome, got {type(outcome)}"
        )
    if outcome.axis is not None:
        raise ReceiptIntegrityError(
            f"baseline_outcome.axis must be None, got {outcome.axis}"
        )


def _coerce_axis_outcomes(outcomes: object) -> tuple:
    if isinstance(outcomes, tuple):
        return outcomes
    if isinstance(outcomes, (list, Sequence)):
        return tuple(outcomes)
    if isinstance(outcomes, (dict, Mapping)):
        return tuple(outcomes.values())
    raise ReceiptIntegrityError(
        "axis_outcomes must be a tuple, list, or mapping of AblationAxisOutcome"
    )


def _require_distinct_axes(outcomes: tuple) -> None:
    seen_axes: set[AblationAxis] = set()
    for outcome in outcomes:
        if not isinstance(outcome, AblationAxisOutcome):
            raise ReceiptIntegrityError(
                "All axis_outcomes elements must be AblationAxisOutcome, "
                f"got {type(outcome)}"
            )
        if outcome.axis is None:
            raise ReceiptIntegrityError(
                "AblationAxisOutcome in axis_outcomes must declare an active AblationAxis"
            )
        if outcome.axis in seen_axes:
            raise ReceiptIntegrityError(
                f"Duplicate axis {outcome.axis.value} in axis_outcomes is strictly forbidden"
            )
        seen_axes.add(outcome.axis)
    if len(seen_axes) != len(outcomes):
        raise ReceiptIntegrityError("Duplicate ablation axis detected in axis_outcomes")


@dataclass(frozen=True)
class AblationComparisonReceiptV1:
    """Deterministic comparative receipt for a six-axis ablation sweep.

    Binds the unablated baseline outcome against each of the 6 ablated axes
    under an invariant problem instance and compute budget C.

    Clean Architecture Invariant: Value Object with exact-type equality.
    """
    receipt_id: str
    problem_id: str
    compute_budget: int
    baseline_outcome: AblationAxisOutcome
    axis_outcomes: Tuple[AblationAxisOutcome, ...]
    receipt_sha256: str = ""
    timestamp: float = field(default_factory=time.time)
    schema_version: str = "core.reasoning-ablation-receipt.v1"
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _require_receipt_identity(self)
        _require_baseline_outcome(self.baseline_outcome)
        outcomes = _coerce_axis_outcomes(self.axis_outcomes)
        if outcomes is not self.axis_outcomes:
            object.__setattr__(self, "axis_outcomes", outcomes)
        _require_distinct_axes(self.axis_outcomes)

    def get_outcome(self, axis: Union[AblationAxis, str]) -> Optional[AblationAxisOutcome]:
        """Lookup the outcome for a specific ablation axis."""
        target_str = axis.value if isinstance(axis, AblationAxis) else str(axis).lower()
        for outcome in self.axis_outcomes:
            if outcome.axis is not None and outcome.axis.value == target_str:
                return outcome
        return None

    def safety_breach_axes(self) -> Tuple[AblationAxis, ...]:
        """Return all ablation axes that resulted in unauthorized state mutations."""
        breaches: List[AblationAxis] = []
        for outcome in self.axis_outcomes:
            if outcome.axis is not None and (outcome.unauthorized_mutations > 0 or outcome.safety_violation):
                breaches.append(outcome.axis)
        return tuple(breaches)

    def hallucination_axes(self) -> Tuple[AblationAxis, ...]:
        """Return all ablation axes that resulted in forced terminal hallucinations."""
        hallucinations: List[AblationAxis] = []
        for outcome in self.axis_outcomes:
            if outcome.axis is not None and (not outcome.residual_honesty_declared or outcome.failure_mode_detected == AblationFailureMode.FORCED_TERMINAL_HALLUCINATION.value):
                hallucinations.append(outcome.axis)
        return tuple(hallucinations)

    def deceptive_trap_axes(self) -> Tuple[AblationAxis, ...]:
        """Return all ablation axes that fell into deceptive reward traps."""
        trapped: List[AblationAxis] = []
        for outcome in self.axis_outcomes:
            if outcome.axis is not None and outcome.fell_into_trap:
                trapped.append(outcome.axis)
        return tuple(trapped)

    def to_dict(self, include_sha256: bool = True) -> Dict[str, Any]:
        """Produce a dictionary for deterministic sorted-key serialization."""
        axis_dict: Dict[str, Any] = {}
        for outcome in sorted(self.axis_outcomes, key=lambda o: (o.axis.value if o.axis else "")):
            if outcome.axis is not None:
                axis_dict[outcome.axis.value] = outcome.to_dict()

        payload: Dict[str, Any] = {
            "ablation_axes_evaluated": axis_dict,
            "authority_effect": self.authority_effect,
            "baseline_metrics": self.baseline_outcome.to_dict(),
            "compute_budget_c": self.compute_budget,
            "problem_id": self.problem_id,
            "receipt_id": self.receipt_id,
            "schema_version": self.schema_version,
            "timestamp": round(self.timestamp, 3),
        }
        if include_sha256 and self.receipt_sha256:
            payload["receipt_sha256"] = self.receipt_sha256
        return payload

    def canonical_rfc8785_bytes(self, include_sha256: bool = False) -> bytes:
        """Produce bytes using the legacy-named deterministic JSON profile.

        By default, excludes receipt_sha256 to allow self-contained digest
        calculation. The method name is retained for API compatibility and does
        not establish complete RFC 8785 conformance.
        """
        payload = self.to_dict(include_sha256=include_sha256)
        return canonical_rfc8785_json(payload)

    def compute_digest(self) -> str:
        """Compute the profile-bound SHA-256 digest over the receipt content."""
        canonical_bytes = self.canonical_rfc8785_bytes(include_sha256=False)
        return compute_sha256(canonical_bytes)

    def with_computed_digest(self) -> AblationComparisonReceiptV1:
        """Return a copy of this receipt with receipt_sha256 populated."""
        digest = self.compute_digest()
        return AblationComparisonReceiptV1(
            receipt_id=self.receipt_id,
            problem_id=self.problem_id,
            compute_budget=self.compute_budget,
            baseline_outcome=self.baseline_outcome,
            axis_outcomes=self.axis_outcomes,
            receipt_sha256=digest,
            timestamp=self.timestamp,
            schema_version=self.schema_version,
            authority_effect=self.authority_effect,
        )

    def verify_integrity(self) -> Tuple[bool, Optional[str]]:
        """Verify cryptographic integrity against receipt_sha256."""
        if not self.receipt_sha256:
            return False, "receipt_sha256 is empty"
        expected = self.compute_digest()
        if self.receipt_sha256 != expected:
            return False, f"Digest mismatch: recorded {self.receipt_sha256} != recomputed {expected}"
        return True, None

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, AblationComparisonReceiptV1)
        return (
            self.receipt_id == other.receipt_id
            and self.problem_id == other.problem_id
            and self.compute_budget == other.compute_budget
            and self.baseline_outcome == other.baseline_outcome
            and self.axis_outcomes == other.axis_outcomes
            and self.receipt_sha256 == other.receipt_sha256
            and math.isclose(self.timestamp, other.timestamp, abs_tol=1e-3)
            and self.schema_version == other.schema_version
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.receipt_id,
            self.problem_id,
            self.compute_budget,
            self.baseline_outcome,
            self.axis_outcomes,
            self.receipt_sha256,
            round(self.timestamp, 3),
            self.schema_version,
            self.authority_effect,
        ))


__all__ = [
    # Helpers
    "sorted_compact_json",
    "canonical_rfc8785_json",
    "compute_sha256",
    # Enums
    "AblationAxis",
    "AblationFailureMode",
    # Exceptions
    "AblationDomainError",
    "InvalidAblationConfigError",
    "ReceiptIntegrityError",
    # Value Objects
    "AblationRunConfig",
    "AblationAxisOutcome",
    "AblationComparisonReceiptV1",
]
