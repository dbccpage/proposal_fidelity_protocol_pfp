# -*- coding: utf-8 -*-
"""Domain models, enumerations, value objects, and errors for benchmarks.

Clean Architecture Layer: Domain
AuthorityEffect: None
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple

# ==============================================================================
# Helper Functions: RFC 8785 Canonical JSON & SHA-256
# ==============================================================================

def sorted_compact_json(data: Mapping[str, Any]) -> bytes:
    """Serialize dictionary with deterministic sorted-key compact JSON profile.

    Enforces:
    - UTF-8 encoding without BOM
    - Keys sorted in ordinal UTF-8 order
    - Minimal separators (',', ':') with zero extraneous whitespace

    Note: This is sorted compact JSON, not strict RFC 8785 JCS (which requires ECMAScript
    number rules and UTF-16 code unit property key sorting). For strict RFC 8785 JCS,
    use the native Rust JCS engine in `omega_symbol_game_runtime::jcs`.
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


def compute_sha256(content: bytes | str) -> str:
    """Compute standard hex SHA-256 digest."""
    raw = content.encode("utf-8") if isinstance(content, str) else content
    return hashlib.sha256(raw).hexdigest()


# ==============================================================================
# Domain Enumerations
# ==============================================================================

class ExecutionMode(str, Enum):
    """Execution mode of the benchmark harness."""
    DETERMINISTIC_SIMULATION = "DETERMINISTIC_SIMULATION"
    LIVE_LLM_ADAPTER = "LIVE_LLM_ADAPTER"


class BenchmarkVerdict(str, Enum):
    """Terminal disposition of a benchmark run."""
    EXACT_TERMINAL = "EXACT_TERMINAL"
    AUTHORIZED = "AUTHORIZED"
    REFUSED = "REFUSED"
    BOUNDED_WITH_OPEN_RESIDUAL = "BOUNDED_WITH_OPEN_RESIDUAL"
    BOUNDED_RESIDUAL = "BOUNDED_RESIDUAL"
    AUTHORIZED_MUTATION = "AUTHORIZED_MUTATION"
    FAILED_TRAP = "FAILED_TRAP"
    SAFETY_BREACH = "SAFETY_BREACH"
    EXHAUSTED = "EXHAUSTED"


class ExhaustionStatus(str, Enum):
    """Honest budget exhaustion verdict matching THREAT_MODEL.md §T7."""
    BOUNDED_WITH_UNJOINED_PEAK = "BoundedWithUnjoinedPeak"
    BUDGET_EXHAUSTED = "BudgetExhausted"


class AuthorityEffectKind(str, Enum):
    """Authority effect declared on packets and adapters."""
    NONE = "None"
    EVIDENCE_ONLY = "evidence_only"


class CandidateType(str, Enum):
    """Permitted candidate types per llm_adapter.contract.yaml."""
    CANDIDATE_RESPONSE = "CandidateResponse"
    CANDIDATE_TRACE = "CandidateTrace"
    DECLARED_ACTION_CANDIDATE = "DeclaredActionCandidate"
    CANDIDATE_REPAIR_PROPOSAL = "CandidateRepairProposal"
    ORACLE_CANDIDATE_SUGGESTION = "OracleCandidateSuggestion"


class BenchmarkTopology(str, Enum):
    """Simplicial cell complex topology kinds."""
    GENUS_0 = "genus_0"
    TORUS_T2 = "torus_t2"
    GENUS_2_M2 = "genus_2_m2"


class AdversarialTrapType(str, Enum):
    """Adversarial trap categories embedding structural failure modes."""
    IRREVERSIBLE_MUTATION = "irreversible_mutation"
    DECEPTIVE_REWARD = "deceptive_reward"
    TOPOLOGICAL_OBSTRUCTION = "topological_obstruction"


class SearchStrategy(str, Enum):
    """Operational inference-time reasoning search strategies."""
    BEST_OF_N = "best_of_n"
    MCTS = "mcts"
    VERIFIER_VOTING = "verifier_voting"
    SELF_CORRECTION = "self_correction"


# ==============================================================================
# Domain Exceptions
# ==============================================================================

class BenchmarkError(Exception):
    """Base domain exception for all benchmark operations."""


class InvalidBudgetError(BenchmarkError, ValueError):
    """Raised when compute budget is non-positive or malformed."""


class BudgetExhaustedError(BenchmarkError):
    """Raised when budget is fully depleted and execution cannot proceed."""


class AuthorityElevationError(BenchmarkError, ValueError):
    """Raised when a model or payload attempts to claim or elevate authority."""


class MachineBlockParseError(BenchmarkError, ValueError):
    """Raised when raw response text fails machine block JSON extraction."""


class SchemaMismatchError(BenchmarkError, ValueError):
    """Raised when parsed candidate payload violates the declared candidate schema."""


# ==============================================================================
# Domain Value Objects (Exact-Type Equality)
# ==============================================================================

@dataclass(frozen=True)
class SimplicialMesh:
    """Strongly-typed discrete cell complex (C0, C1, C2) representing topology."""
    nodes: Tuple[int, ...]
    edges: Tuple[Tuple[int, int], ...]
    faces: Tuple[Tuple[int, int, int], ...]
    betti_0: int
    betti_1: int
    euler_characteristic: int
    name: str

    def __post_init__(self) -> None:
        if type(self.nodes) is not tuple:
            object.__setattr__(self, "nodes", tuple(self.nodes))
        if type(self.edges) is not tuple:
            object.__setattr__(self, "edges", tuple(tuple(e) for e in self.edges))
        if type(self.faces) is not tuple:
            object.__setattr__(self, "faces", tuple(tuple(f) for f in self.faces))
        if type(self.betti_0) is not int or self.betti_0 < 0:
            raise ValueError("betti_0 must be a non-negative int")
        if type(self.betti_1) is not int or self.betti_1 < 0:
            raise ValueError("betti_1 must be a non-negative int")
        if type(self.euler_characteristic) is not int:
            raise TypeError("euler_characteristic must be an int")
        if type(self.name) is not str or not self.name:
            raise ValueError("name must be a non-empty str")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, SimplicialMesh)
        return (
            self.nodes == other.nodes
            and self.edges == other.edges
            and self.faces == other.faces
            and self.betti_0 == other.betti_0
            and self.betti_1 == other.betti_1
            and self.euler_characteristic == other.euler_characteristic
            and self.name == other.name
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.nodes,
            self.edges,
            self.faces,
            self.betti_0,
            self.betti_1,
            self.euler_characteristic,
            self.name,
        ))


def _coerce_problem_topology(problem: BenchmarkProblem) -> None:
    if type(problem.topology) is str:
        return
    if isinstance(problem.topology, BenchmarkTopology):
        object.__setattr__(problem, "topology", problem.topology.value)
        return
    raise TypeError("topology must be a str")


def _coerce_problem_trap(problem: BenchmarkProblem) -> None:
    if problem.trap_type is None or type(problem.trap_type) is str:
        return
    if isinstance(problem.trap_type, AdversarialTrapType):
        object.__setattr__(problem, "trap_type", problem.trap_type.value)
        return
    raise TypeError("trap_type must be None or str")


def _sync_protected_edges(problem: BenchmarkProblem) -> None:
    if problem.protected_boundaries and not problem.protected_edges:
        object.__setattr__(problem, "protected_edges", tuple(problem.protected_boundaries))
        return
    if problem.protected_edges and not problem.protected_boundaries:
        object.__setattr__(problem, "protected_boundaries", tuple(problem.protected_edges))
        return
    object.__setattr__(problem, "protected_boundaries", tuple(problem.protected_boundaries))
    object.__setattr__(problem, "protected_edges", tuple(problem.protected_edges))


@dataclass(frozen=True)
class BenchmarkProblem:
    """Canonical Benchmark Problem matching PROJECT.md Interface Contracts."""
    problem_id: str
    topology: str
    trap_type: Optional[str]
    ground_truth_admissible: bool
    initial_cochains: Dict[str, Any]
    admissible_authorization_target: str
    protected_boundaries: Tuple[str, ...] = ()
    protected_edges: Tuple[str, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        if type(self.problem_id) is not str or not self.problem_id:
            raise ValueError("problem_id must be a non-empty string")
        _coerce_problem_topology(self)
        _coerce_problem_trap(self)
        if type(self.ground_truth_admissible) is not bool:
            raise TypeError("ground_truth_admissible must be bool")
        if not isinstance(self.initial_cochains, (dict, Mapping)):
            raise TypeError("initial_cochains must be a dict or Mapping")
        if type(self.admissible_authorization_target) is not str:
            raise TypeError("admissible_authorization_target must be a str")
        _sync_protected_edges(self)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, BenchmarkProblem)
        return (
            self.problem_id == other.problem_id
            and self.topology == other.topology
            and self.trap_type == other.trap_type
            and self.ground_truth_admissible == other.ground_truth_admissible
            and dict(self.initial_cochains) == dict(other.initial_cochains)
            and self.admissible_authorization_target == other.admissible_authorization_target
            and self.protected_boundaries == other.protected_boundaries
            and self.protected_edges == other.protected_edges
            and self.description == other.description
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.problem_id,
                self.topology,
                self.trap_type,
                self.ground_truth_admissible,
                tuple(sorted((k, str(v)) for k, v in self.initial_cochains.items())),
                self.admissible_authorization_target,
                self.protected_boundaries,
                self.protected_edges,
                self.description,
            )
        )


@dataclass(frozen=True)
class StepRecord:
    """Audit log entry for a single budget consumption step."""
    step_index: int
    operation: str
    cost: int
    remaining_budget: int
    timestamp: float = field(default_factory=time.time)
    tokens_consumed: int = 0

    def __post_init__(self) -> None:
        if type(self.step_index) is not int or self.step_index < 1:
            raise ValueError("step_index must be a positive integer")
        if type(self.operation) is not str or not self.operation:
            raise ValueError("operation must be a non-empty string")
        if type(self.cost) is not int or self.cost < 0:
            raise ValueError("cost must be a non-negative integer")
        if type(self.remaining_budget) is not int or self.remaining_budget < 0:
            raise ValueError("remaining_budget must be a non-negative integer")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, StepRecord)
        return (
            self.step_index == other.step_index
            and self.operation == other.operation
            and self.cost == other.cost
            and self.remaining_budget == other.remaining_budget
            and self.tokens_consumed == other.tokens_consumed
            and math.isclose(self.timestamp, other.timestamp, abs_tol=1e-3)
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.step_index,
            self.operation,
            self.cost,
            self.remaining_budget,
            self.tokens_consumed,
            round(self.timestamp, 3),
        ))


@dataclass(frozen=True)
class TokenUsage:
    """Token consumption accounting metrics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    def __post_init__(self) -> None:
        if type(self.prompt_tokens) is not int or self.prompt_tokens < 0:
            raise ValueError("prompt_tokens must be non-negative integer")
        if type(self.completion_tokens) is not int or self.completion_tokens < 0:
            raise ValueError("completion_tokens must be non-negative integer")
        if type(self.total_tokens) is not int or self.total_tokens < 0:
            raise ValueError("total_tokens must be non-negative integer")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, TokenUsage)
        return (
            self.prompt_tokens == other.prompt_tokens
            and self.completion_tokens == other.completion_tokens
            and self.total_tokens == other.total_tokens
        )

    def __hash__(self) -> int:
        return hash((type(self), self.prompt_tokens, self.completion_tokens, self.total_tokens))


@dataclass(frozen=True)
class BudgetExhaustionRecord:
    """Honest budget exhaustion artifact emitted when compute budget is spent."""
    status: str = BenchmarkVerdict.BOUNDED_WITH_OPEN_RESIDUAL.value
    steps_inspected: int = 0
    step_budget: int = 0
    verdict: str = ExhaustionStatus.BOUNDED_WITH_UNJOINED_PEAK.value
    authority_effect: str = AuthorityEffectKind.NONE.value

    def __post_init__(self) -> None:
        if type(self.steps_inspected) is not int or self.steps_inspected < 0:
            raise ValueError("steps_inspected must be a non-negative integer")
        if type(self.step_budget) is not int or self.step_budget < 1:
            raise ValueError("step_budget must be a positive integer")
        if self.authority_effect != AuthorityEffectKind.NONE.value:
            raise ValueError("authority_effect must be 'None'")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, BudgetExhaustionRecord)
        return (
            self.status == other.status
            and self.steps_inspected == other.steps_inspected
            and self.step_budget == other.step_budget
            and self.verdict == other.verdict
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.status,
            self.steps_inspected,
            self.step_budget,
            self.verdict,
            self.authority_effect,
        ))


# Backward compatibility alias
BudgetExhaustionReceipt = BudgetExhaustionRecord


@dataclass(frozen=True)
class LlmAdapterOutput:
    """Structure matching llm_adapter.contract.yaml LlmAdapterOutput struct."""
    packet_id: str
    candidate_id: str
    candidate_type: str
    request_hash: str
    raw_response_hash: str
    mapping_witness_ref: str
    schema_ref: str
    parser_version: str
    adapter_version: str
    authority_effect: str = AuthorityEffectKind.NONE.value
    parsed_payload: Dict[str, Any] = field(default_factory=dict)
    tokens_used: Optional[TokenUsage] = None

    def __post_init__(self) -> None:
        if type(self.packet_id) is not str or not self.packet_id:
            raise ValueError("packet_id must be non-empty string")
        if type(self.candidate_id) is not str or not self.candidate_id:
            raise ValueError("candidate_id must be non-empty string")
        if self.authority_effect not in (
            AuthorityEffectKind.NONE.value,
            AuthorityEffectKind.EVIDENCE_ONLY.value,
        ):
            raise ValueError("authority_effect must be 'None' or 'evidence_only'")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, LlmAdapterOutput)
        return (
            self.packet_id == other.packet_id
            and self.candidate_id == other.candidate_id
            and self.candidate_type == other.candidate_type
            and self.request_hash == other.request_hash
            and self.raw_response_hash == other.raw_response_hash
            and self.mapping_witness_ref == other.mapping_witness_ref
            and self.schema_ref == other.schema_ref
            and self.parser_version == other.parser_version
            and self.adapter_version == other.adapter_version
            and self.authority_effect == other.authority_effect
            and dict(self.parsed_payload) == dict(other.parsed_payload)
            and self.tokens_used == other.tokens_used
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.packet_id,
            self.candidate_id,
            self.candidate_type,
            self.request_hash,
            self.raw_response_hash,
            self.mapping_witness_ref,
            self.schema_ref,
            self.parser_version,
            self.adapter_version,
            self.authority_effect,
            self.tokens_used,
        ))


@dataclass(frozen=True)
class CandidateRollout:
    """Typed candidate trajectory proposal."""
    rollout_id: str
    steps: Tuple[Any, ...] = ()
    phi1: float = 0.0
    gamma2: float = 0.0
    score: float = 0.0
    is_unauthorized_mutation: bool = False
    is_terminal: bool = False

    def __post_init__(self) -> None:
        if type(self.rollout_id) is not str or not self.rollout_id:
            raise ValueError("rollout_id must be a non-empty string")
        if type(self.steps) is not tuple:
            object.__setattr__(self, "steps", tuple(self.steps))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, CandidateRollout)
        return (
            self.rollout_id == other.rollout_id
            and self.steps == other.steps
            and math.isclose(self.phi1, other.phi1, abs_tol=1e-7)
            and math.isclose(self.gamma2, other.gamma2, abs_tol=1e-7)
            and math.isclose(self.score, other.score, abs_tol=1e-7)
            and self.is_unauthorized_mutation == other.is_unauthorized_mutation
            and self.is_terminal == other.is_terminal
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.rollout_id,
            self.steps,
            round(self.phi1, 6),
            round(self.gamma2, 6),
            round(self.score, 6),
            self.is_unauthorized_mutation,
            self.is_terminal,
        ))


@dataclass(frozen=True)
class BenchmarkRunResult:
    """Unified telemetry and evaluation record for a single benchmark problem run."""
    task_key: str
    system_id: str  # "baseline_operational" or "woland_algebraic"
    problem_id: str
    compute_budget: int
    status: str  # "AUTHORIZED", "REFUSED", "BOUNDED_RESIDUAL", "AUTHORIZED_MUTATION", "EXHAUSTED"
    steps_spent: int
    tokens_spent: int
    phi1: float
    gamma2: float
    defect_count: int
    residual_declared: bool
    is_authorized: bool
    unauthorized_mutations_count: int
    safety_violation: bool
    fell_into_trap: bool
    admissible: bool
    receipt_path: Optional[str] = None
    novella_path: Optional[str] = None
    ddc_path: Optional[str] = None
    summary_path: Optional[str] = None
    authority_effect: str = "None"
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if type(self.task_key) is not str or not self.task_key:
            raise ValueError("task_key must be non-empty string")
        if type(self.system_id) is not str:
            raise TypeError("system_id must be string")
        if type(self.compute_budget) is not int or self.compute_budget < 1:
            raise ValueError("compute_budget must be positive integer")
        if type(self.steps_spent) is not int or self.steps_spent < 0:
            raise ValueError("steps_spent must be non-negative integer")
        if type(self.residual_declared) is not bool or type(self.is_authorized) is not bool:
            raise TypeError("residual_declared and is_authorized must be exact bool")
        if type(self.safety_violation) is not bool or type(self.fell_into_trap) is not bool:
            raise TypeError("safety_violation and fell_into_trap must be exact bool")
        if self.authority_effect != "None":
            raise ValueError("authority_effect must be 'None'")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, BenchmarkRunResult)
        return (
            self.task_key == other.task_key
            and self.system_id == other.system_id
            and self.problem_id == other.problem_id
            and self.compute_budget == other.compute_budget
            and self.status == other.status
            and self.steps_spent == other.steps_spent
            and self.tokens_spent == other.tokens_spent
            and math.isclose(self.phi1, other.phi1, abs_tol=1e-7)
            and math.isclose(self.gamma2, other.gamma2, abs_tol=1e-7)
            and self.defect_count == other.defect_count
            and self.residual_declared == other.residual_declared
            and self.is_authorized == other.is_authorized
            and self.unauthorized_mutations_count == other.unauthorized_mutations_count
            and self.safety_violation == other.safety_violation
            and self.fell_into_trap == other.fell_into_trap
            and self.admissible == other.admissible
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.task_key,
            self.system_id,
            self.problem_id,
            self.compute_budget,
            self.status,
            self.steps_spent,
            round(self.phi1, 6),
            round(self.gamma2, 6),
            self.defect_count,
            self.residual_declared,
            self.is_authorized,
            self.unauthorized_mutations_count,
            self.safety_violation,
            self.fell_into_trap,
            self.admissible,
            self.authority_effect,
        ))


@dataclass(frozen=True)
class ScalingCurvePoint:
    """Individual data point on a compute scaling curve."""
    budget: int
    accuracy: float
    sample_count: int = 0

    def __post_init__(self) -> None:
        if type(self.budget) is not int or self.budget < 1:
            raise ValueError("budget must be a positive integer")
        if not isinstance(self.accuracy, (int, float)) or not (0.0 <= self.accuracy <= 1.0):
            raise ValueError("accuracy must be in range [0.0, 1.0]")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ScalingCurvePoint)
        return (
            self.budget == other.budget
            and math.isclose(self.accuracy, other.accuracy, abs_tol=1e-7)
            and self.sample_count == other.sample_count
        )

    def __hash__(self) -> int:
        return hash((type(self), self.budget, round(self.accuracy, 6), self.sample_count))


@dataclass(frozen=True)
class QuantitativeMetrics:
    """The 6 standard quantitative benchmark metrics evaluated across a suite."""
    s_c_scaling_curve: Dict[int, float]  # Budget C -> Task Accuracy in [0.0, 1.0]
    r_detection_rate: float  # Injected Defects Detected / Total Injected
    r_repair_rate: float  # Detected Defects Resolved / Detected Defects
    brier_score: float  # Mean squared error of confidence calibration
    expected_calibration_error: float  # ECE across confidence bins
    e_sample_efficiency: float  # Budget C required to achieve target accuracy
    h_residual_honesty: float  # Declared Open Residuals / (Declared + Hallucinated Terminals)
    s_safety_rate: float  # 1.0 - (Unauthorized Mutations / Trap Opportunities)
    t_transfer_score: float  # Accuracy on (T2 + M2) / Accuracy on Genus 0

    def __post_init__(self) -> None:
        for f_name in (
            "r_detection_rate", "r_repair_rate", "brier_score",
            "expected_calibration_error", "h_residual_honesty",
            "s_safety_rate", "t_transfer_score",
        ):
            val = getattr(self, f_name)
            if not isinstance(val, (int, float)) or not math.isfinite(val):
                raise ValueError(f"{f_name} must be a finite float")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, QuantitativeMetrics)
        return (
            dict(self.s_c_scaling_curve) == dict(other.s_c_scaling_curve)
            and math.isclose(self.r_detection_rate, other.r_detection_rate, abs_tol=1e-7)
            and math.isclose(self.r_repair_rate, other.r_repair_rate, abs_tol=1e-7)
            and math.isclose(self.brier_score, other.brier_score, abs_tol=1e-7)
            and math.isclose(self.expected_calibration_error, other.expected_calibration_error, abs_tol=1e-7)
            and math.isclose(self.e_sample_efficiency, other.e_sample_efficiency, abs_tol=1e-7)
            and math.isclose(self.h_residual_honesty, other.h_residual_honesty, abs_tol=1e-7)
            and math.isclose(self.s_safety_rate, other.s_safety_rate, abs_tol=1e-7)
            and math.isclose(self.t_transfer_score, other.t_transfer_score, abs_tol=1e-7)
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            tuple(sorted(self.s_c_scaling_curve.items())),
            round(self.r_detection_rate, 5),
            round(self.r_repair_rate, 5),
            round(self.brier_score, 5),
            round(self.expected_calibration_error, 5),
            round(self.e_sample_efficiency, 5),
            round(self.h_residual_honesty, 5),
            round(self.s_safety_rate, 5),
            round(self.t_transfer_score, 5),
        ))


# Backward compatibility alias
BenchmarkMetrics = QuantitativeMetrics
