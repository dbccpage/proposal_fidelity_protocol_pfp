"""Domain package for Reasoning Benchmarks, Problem Banks, Topologies, and Protocols.

AuthorityEffect: None.
Clean Architecture Layer: Domain
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from operations.domain.benchmarks.ablation import AblationAxis, AblationAxisOutcome, AblationComparisonReceiptV1, AblationDomainError, AblationFailureMode, AblationRunConfig, InvalidAblationConfigError, ReceiptIntegrityError
    from operations.domain.benchmarks.models import AdversarialTrapType, AuthorityEffectKind, AuthorityElevationError, BenchmarkError, BenchmarkMetrics, BenchmarkProblem, BenchmarkRunResult, BenchmarkTopology, BenchmarkVerdict, BudgetExhaustedError, BudgetExhaustionReceipt, BudgetExhaustionRecord, CandidateRollout, CandidateType, ExecutionMode, ExhaustionStatus, InvalidBudgetError, LlmAdapterOutput, MachineBlockParseError, QuantitativeMetrics, ScalingCurvePoint, SchemaMismatchError, SearchStrategy, SimplicialMesh, StepRecord, TokenUsage, canonical_rfc8785_json, compute_sha256, sorted_compact_json
    from operations.domain.benchmarks.problem_bank import ProblemBank, build_genus_0_mesh, build_genus_2_mesh, build_problem_bank, build_torus_t2_mesh, create_genus_0_problem, create_genus_2_problem, create_torus_t2_problem, generate_problem_bank, get_canonical_problem
    from operations.domain.benchmarks.protocols import BenchmarkReasonerProtocol, LlmAdapterProtocol, LlmProviderProtocol, SimulationEngineProtocol

__all__ = ['AblationAxis', 'AblationFailureMode', 'AdversarialTrapType', 'AuthorityEffectKind', 'BenchmarkTopology', 'BenchmarkVerdict', 'CandidateType', 'ExecutionMode', 'ExhaustionStatus', 'SearchStrategy', 'AblationAxisOutcome', 'AblationComparisonReceiptV1', 'AblationRunConfig', 'BenchmarkMetrics', 'BenchmarkProblem', 'BenchmarkRunResult', 'BudgetExhaustionReceipt', 'BudgetExhaustionRecord', 'CandidateRollout', 'LlmAdapterOutput', 'QuantitativeMetrics', 'ScalingCurvePoint', 'SimplicialMesh', 'StepRecord', 'TokenUsage', 'build_genus_0_mesh', 'build_genus_2_mesh', 'build_problem_bank', 'build_torus_t2_mesh', 'sorted_compact_json', 'canonical_rfc8785_json', 'compute_sha256', 'create_genus_0_problem', 'create_genus_2_problem', 'create_torus_t2_problem', 'generate_problem_bank', 'get_canonical_problem', 'ProblemBank', 'BenchmarkReasonerProtocol', 'LlmAdapterProtocol', 'LlmProviderProtocol', 'SimulationEngineProtocol', 'AblationDomainError', 'AuthorityElevationError', 'BenchmarkError', 'BudgetExhaustedError', 'InvalidAblationConfigError', 'InvalidBudgetError', 'MachineBlockParseError', 'ReceiptIntegrityError', 'SchemaMismatchError']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'AblationAxis': ('operations.domain.benchmarks.ablation', 'AblationAxis'),
    'AblationAxisOutcome': ('operations.domain.benchmarks.ablation', 'AblationAxisOutcome'),
    'AblationComparisonReceiptV1': ('operations.domain.benchmarks.ablation', 'AblationComparisonReceiptV1'),
    'AblationDomainError': ('operations.domain.benchmarks.ablation', 'AblationDomainError'),
    'AblationFailureMode': ('operations.domain.benchmarks.ablation', 'AblationFailureMode'),
    'AblationRunConfig': ('operations.domain.benchmarks.ablation', 'AblationRunConfig'),
    'InvalidAblationConfigError': ('operations.domain.benchmarks.ablation', 'InvalidAblationConfigError'),
    'ReceiptIntegrityError': ('operations.domain.benchmarks.ablation', 'ReceiptIntegrityError'),
    'AdversarialTrapType': ('operations.domain.benchmarks.models', 'AdversarialTrapType'),
    'AuthorityEffectKind': ('operations.domain.benchmarks.models', 'AuthorityEffectKind'),
    'AuthorityElevationError': ('operations.domain.benchmarks.models', 'AuthorityElevationError'),
    'BenchmarkError': ('operations.domain.benchmarks.models', 'BenchmarkError'),
    'BenchmarkMetrics': ('operations.domain.benchmarks.models', 'BenchmarkMetrics'),
    'BenchmarkProblem': ('operations.domain.benchmarks.models', 'BenchmarkProblem'),
    'BenchmarkRunResult': ('operations.domain.benchmarks.models', 'BenchmarkRunResult'),
    'BenchmarkTopology': ('operations.domain.benchmarks.models', 'BenchmarkTopology'),
    'BenchmarkVerdict': ('operations.domain.benchmarks.models', 'BenchmarkVerdict'),
    'BudgetExhaustedError': ('operations.domain.benchmarks.models', 'BudgetExhaustedError'),
    'BudgetExhaustionReceipt': ('operations.domain.benchmarks.models', 'BudgetExhaustionReceipt'),
    'BudgetExhaustionRecord': ('operations.domain.benchmarks.models', 'BudgetExhaustionRecord'),
    'CandidateRollout': ('operations.domain.benchmarks.models', 'CandidateRollout'),
    'CandidateType': ('operations.domain.benchmarks.models', 'CandidateType'),
    'ExecutionMode': ('operations.domain.benchmarks.models', 'ExecutionMode'),
    'ExhaustionStatus': ('operations.domain.benchmarks.models', 'ExhaustionStatus'),
    'InvalidBudgetError': ('operations.domain.benchmarks.models', 'InvalidBudgetError'),
    'LlmAdapterOutput': ('operations.domain.benchmarks.models', 'LlmAdapterOutput'),
    'MachineBlockParseError': ('operations.domain.benchmarks.models', 'MachineBlockParseError'),
    'QuantitativeMetrics': ('operations.domain.benchmarks.models', 'QuantitativeMetrics'),
    'ScalingCurvePoint': ('operations.domain.benchmarks.models', 'ScalingCurvePoint'),
    'SchemaMismatchError': ('operations.domain.benchmarks.models', 'SchemaMismatchError'),
    'SearchStrategy': ('operations.domain.benchmarks.models', 'SearchStrategy'),
    'SimplicialMesh': ('operations.domain.benchmarks.models', 'SimplicialMesh'),
    'StepRecord': ('operations.domain.benchmarks.models', 'StepRecord'),
    'TokenUsage': ('operations.domain.benchmarks.models', 'TokenUsage'),
    'canonical_rfc8785_json': ('operations.domain.benchmarks.models', 'canonical_rfc8785_json'),
    'compute_sha256': ('operations.domain.benchmarks.models', 'compute_sha256'),
    'sorted_compact_json': ('operations.domain.benchmarks.models', 'sorted_compact_json'),
    'ProblemBank': ('operations.domain.benchmarks.problem_bank', 'ProblemBank'),
    'build_genus_0_mesh': ('operations.domain.benchmarks.problem_bank', 'build_genus_0_mesh'),
    'build_genus_2_mesh': ('operations.domain.benchmarks.problem_bank', 'build_genus_2_mesh'),
    'build_problem_bank': ('operations.domain.benchmarks.problem_bank', 'build_problem_bank'),
    'build_torus_t2_mesh': ('operations.domain.benchmarks.problem_bank', 'build_torus_t2_mesh'),
    'create_genus_0_problem': ('operations.domain.benchmarks.problem_bank', 'create_genus_0_problem'),
    'create_genus_2_problem': ('operations.domain.benchmarks.problem_bank', 'create_genus_2_problem'),
    'create_torus_t2_problem': ('operations.domain.benchmarks.problem_bank', 'create_torus_t2_problem'),
    'generate_problem_bank': ('operations.domain.benchmarks.problem_bank', 'generate_problem_bank'),
    'get_canonical_problem': ('operations.domain.benchmarks.problem_bank', 'get_canonical_problem'),
    'BenchmarkReasonerProtocol': ('operations.domain.benchmarks.protocols', 'BenchmarkReasonerProtocol'),
    'LlmAdapterProtocol': ('operations.domain.benchmarks.protocols', 'LlmAdapterProtocol'),
    'LlmProviderProtocol': ('operations.domain.benchmarks.protocols', 'LlmProviderProtocol'),
    'SimulationEngineProtocol': ('operations.domain.benchmarks.protocols', 'SimulationEngineProtocol'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
