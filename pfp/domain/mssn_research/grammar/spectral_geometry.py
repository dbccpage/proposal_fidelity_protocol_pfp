"""Value Objects for the Grammar Bounded Context.

Enforces:
- Exact-Type Equality (RULE_VO_EXACT_TYPE_EQUALITY_001)
- Immutability and Pure Python language types
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from pfp.domain.mssn_research.shared_kernel.value_objects import (
    ContentDigest,
    Rational,
    StageLevel,
)

from .exact_structures import ExactRationalMatrix


def _require_instance(value: object, expected: type[object], field_name: str) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{field_name} must be a {expected.__name__}")


def _require_exact_int(value: object, field_name: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an int")


class ZetaType(int, Enum):
    """Zeta function type specification."""
    DYNAMIC_TRANSFER = 0 # <0>: Dynamic transfer zeta det(I - z A)^-1
    IHARA_GRAPH = 1      # <1>: Ihara graph zeta


@dataclass(frozen=True)
class TraceEntry:
    """Step power and trace integer value Tr(A^n)."""
    step_power: int
    trace_val: int

    def __post_init__(self) -> None:
        if not isinstance(self.step_power, int) or self.step_power <= 0:
            raise ValueError("step_power must be positive integer")
        if not isinstance(self.trace_val, int):
            raise TypeError("trace_val must be int")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, TraceEntry)
        return self.step_power == other.step_power and self.trace_val == other.trace_val

    def __hash__(self) -> int:
        return hash((type(self), self.step_power, self.trace_val))


@dataclass(frozen=True)
class ZetaShadowPacket:
    """Level 19: Discrete Ihara / transfer operator spectral shadow packet."""
    zeta_type: ZetaType
    graph_dimension: int
    transfer_traces: tuple[TraceEntry, ...]
    orbit_polynomial_coefficients: tuple[int, ...]
    quarantine_fence_status: str = "FENCED_COMBINATORIAL_MODEL"
    is_exact_rational_poly: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.zeta_type, ZetaType):
            raise TypeError("zeta_type must be ZetaType")
        if not isinstance(self.graph_dimension, int) or self.graph_dimension <= 0:
            raise ValueError("graph_dimension must be positive integer")
        if not isinstance(self.transfer_traces, tuple):
            object.__setattr__(self, "transfer_traces", tuple(self.transfer_traces))
        if not isinstance(self.orbit_polynomial_coefficients, tuple):
            object.__setattr__(self, "orbit_polynomial_coefficients", tuple(self.orbit_polynomial_coefficients))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ZetaShadowPacket)
        return (
            self.zeta_type == other.zeta_type
            and self.graph_dimension == other.graph_dimension
            and self.transfer_traces == other.transfer_traces
            and self.orbit_polynomial_coefficients == other.orbit_polynomial_coefficients
            and self.quarantine_fence_status == other.quarantine_fence_status
            and self.is_exact_rational_poly == other.is_exact_rational_poly
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.zeta_type,
            self.graph_dimension,
            self.transfer_traces,
            self.orbit_polynomial_coefficients,
            self.quarantine_fence_status,
            self.is_exact_rational_poly,
        ))


# ---------------------------------------------------------------------------
# Level 20: Autopoietic Reflection & Expansion Cycle Detection
# ---------------------------------------------------------------------------

class CycleRemediationAction(int, Enum):
    """Remediation action upon expansion cycle detection."""
    HALT_FAIL_STOP = 0      # <0>: Immediate fail-stop
    FREEZE_AUDIT = 1        # <1>: Context freeze with audit dump
    OPERATOR_ESCALATION = 2 # <2>: Ejection to operator boundary

    def to_wire_atom(self) -> str:
        return f"<{self.value}>"


@dataclass(frozen=True)
class AutopoieticExpansionCyclePacket:
    """Level 20: Autopoietic reflection and expansion cycle detection packet."""
    state_digest_initial: ContentDigest
    state_digest_repeated: ContentDigest
    step_distance: int
    linking_rule: str
    progress_delta: int
    action_code: CycleRemediationAction = CycleRemediationAction.HALT_FAIL_STOP
    is_strictly_decreasing: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.state_digest_initial, ContentDigest) or not isinstance(self.state_digest_repeated, ContentDigest):
            raise TypeError("state digests must be ContentDigest")
        if not isinstance(self.step_distance, int) or self.step_distance < 0:
            raise ValueError("step_distance must be non-negative integer")
        if not isinstance(self.linking_rule, str):
            raise TypeError("linking_rule must be a str")
        if not isinstance(self.progress_delta, int):
            raise TypeError("progress_delta must be an int")
        if not isinstance(self.action_code, CycleRemediationAction):
            raise TypeError("action_code must be CycleRemediationAction")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, AutopoieticExpansionCyclePacket)
        return (
            self.state_digest_initial == other.state_digest_initial
            and self.state_digest_repeated == other.state_digest_repeated
            and self.step_distance == other.step_distance
            and self.linking_rule == other.linking_rule
            and self.progress_delta == other.progress_delta
            and self.action_code == other.action_code
            and self.is_strictly_decreasing == other.is_strictly_decreasing
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.state_digest_initial,
            self.state_digest_repeated,
            self.step_distance,
            self.linking_rule,
            self.progress_delta,
            self.action_code,
            self.is_strictly_decreasing,
        ))


# ---------------------------------------------------------------------------
# Level 21: Discrete 4D Regge Metric Deficit & Simplicial Curvature
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Simplex4D:
    """A 4-simplex with exactly 10 squared edge lengths."""
    simplex_id: str
    squared_edge_lengths: tuple[Rational, ...]  # exactly 10 lengths

    def __post_init__(self) -> None:
        if not isinstance(self.simplex_id, str):
            raise TypeError("simplex_id must be a str")
        if not isinstance(self.squared_edge_lengths, tuple):
            object.__setattr__(self, "squared_edge_lengths", tuple(self.squared_edge_lengths))
        if len(self.squared_edge_lengths) != 10:
            raise ValueError(f"4-simplex requires exactly 10 squared edge lengths, got {len(self.squared_edge_lengths)}")
        for length in self.squared_edge_lengths:
            if not isinstance(length, Rational) or length.numerator <= 0:
                raise ValueError(f"Squared edge lengths must be positive Rational, got {length}")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, Simplex4D)
        return self.simplex_id == other.simplex_id and self.squared_edge_lengths == other.squared_edge_lengths

    def __hash__(self) -> int:
        return hash((type(self), self.simplex_id, self.squared_edge_lengths))


@dataclass(frozen=True)
class HingeDeficit:
    """Deficit angle around an internal 2-face (triangle) hinge."""
    triangle_hinge_id: str
    deficit_angle_rat: Rational

    def __post_init__(self) -> None:
        if not isinstance(self.triangle_hinge_id, str):
            raise TypeError("triangle_hinge_id must be a str")
        if not isinstance(self.deficit_angle_rat, Rational):
            raise TypeError("deficit_angle_rat must be a Rational")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, HingeDeficit)
        return (
            self.triangle_hinge_id == other.triangle_hinge_id
            and self.deficit_angle_rat == other.deficit_angle_rat
        )

    def __hash__(self) -> int:
        return hash((type(self), self.triangle_hinge_id, self.deficit_angle_rat))


@dataclass(frozen=True)
class Regge4DPacket:
    """Level 21: Discrete 4D Regge metric deficit and simplicial curvature packet."""
    complex_id: str
    simplices: tuple[Simplex4D, ...]
    cayley_menger_det: Rational
    hinge_deficits: tuple[HingeDeficit, ...]
    bianchi_closure_satisfied: bool
    uses_scalar_sum_only: bool = False
    gram_matrix: Optional[ExactRationalMatrix] = None

    def __post_init__(self) -> None:
        if not isinstance(self.complex_id, str):
            raise TypeError("complex_id must be a str")
        if not isinstance(self.simplices, tuple):
            object.__setattr__(self, "simplices", tuple(self.simplices))
        if not isinstance(self.cayley_menger_det, Rational):
            raise TypeError("cayley_menger_det must be a Rational")
        if not isinstance(self.hinge_deficits, tuple):
            object.__setattr__(self, "hinge_deficits", tuple(self.hinge_deficits))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, Regge4DPacket)
        return (
            self.complex_id == other.complex_id
            and self.simplices == other.simplices
            and self.cayley_menger_det == other.cayley_menger_det
            and self.hinge_deficits == other.hinge_deficits
            and self.bianchi_closure_satisfied == other.bianchi_closure_satisfied
            and self.uses_scalar_sum_only == other.uses_scalar_sum_only
            and self.gram_matrix == other.gram_matrix
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.complex_id,
            self.simplices,
            self.cayley_menger_det,
            self.hinge_deficits,
            self.bianchi_closure_satisfied,
            self.uses_scalar_sum_only,
            self.gram_matrix,
        ))


class LiftGoal(str, Enum):
    """Declared formal goal for an attempted stage lift."""
    IRREFLEXIVE_WITNESSED_RELATION = "IRREFLEXIVE_WITNESSED_RELATION"
    BARE_ASSERTION = "BARE_ASSERTION"
    DISTINCT_NAME_GENERATION = "DISTINCT_NAME_GENERATION"
    DIRECTED_PATH_COMPOSITION = "DIRECTED_PATH_COMPOSITION"
    DIRECTED_CYCLE_THREE = "DIRECTED_CYCLE_THREE"
    TRANSITIVE_CLOSURE_GAP = "TRANSITIVE_CLOSURE_GAP"


@dataclass(frozen=True)
class LiftNecessityCertificate:
    """Candidate finite lift evidence; the supplied flag does not replace host replay."""
    source_stage: StageLevel
    target_stage: StageLevel
    goal: LiftGoal
    carrier_size_source: int
    carrier_size_target: int
    evaluated_configurations_count: int
    surviving_obstruction_code: str
    exhaustion_proof_digest: ContentDigest
    target_resolution_witness: str
    is_verified: bool

    def __post_init__(self) -> None:
        _require_instance(self.source_stage, StageLevel, "source_stage")
        _require_instance(self.target_stage, StageLevel, "target_stage")
        _require_instance(self.goal, LiftGoal, "goal")
        _require_exact_int(self.carrier_size_source, "carrier_size_source")
        _require_exact_int(self.carrier_size_target, "carrier_size_target")
        _require_exact_int(self.evaluated_configurations_count, "evaluated_configurations_count")
        if self.carrier_size_source < 1 or self.carrier_size_target < 1:
            raise ValueError("lift carrier sizes must be positive")
        if self.evaluated_configurations_count < 0:
            raise ValueError("evaluated_configurations_count cannot be negative")
        _require_instance(self.surviving_obstruction_code, str, "surviving_obstruction_code")
        _require_instance(self.exhaustion_proof_digest, ContentDigest, "exhaustion_proof_digest")
        _require_instance(self.target_resolution_witness, str, "target_resolution_witness")
        _require_instance(self.is_verified, bool, "is_verified")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, LiftNecessityCertificate)
        return (
            self.source_stage == other.source_stage
            and self.target_stage == other.target_stage
            and self.goal == other.goal
            and self.carrier_size_source == other.carrier_size_source
            and self.carrier_size_target == other.carrier_size_target
            and self.evaluated_configurations_count == other.evaluated_configurations_count
            and self.surviving_obstruction_code == other.surviving_obstruction_code
            and self.exhaustion_proof_digest == other.exhaustion_proof_digest
            and self.target_resolution_witness == other.target_resolution_witness
            and self.is_verified == other.is_verified
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.source_stage,
            self.target_stage,
            self.goal,
            self.carrier_size_source,
            self.carrier_size_target,
            self.evaluated_configurations_count,
            self.surviving_obstruction_code,
            self.exhaustion_proof_digest,
            self.target_resolution_witness,
            self.is_verified,
        ))
