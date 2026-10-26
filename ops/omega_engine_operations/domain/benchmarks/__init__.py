"""Domain package for Reasoning Benchmarks, Problem Banks, Topologies, and Protocols.

AuthorityEffect: None.
Clean Architecture Layer: Domain
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omega_engine_operations.domain.benchmarks.ablation import AblationAxis, AblationAxisOutcome, AblationComparisonReceiptV1, AblationDomainError, AblationFailureMode, AblationRunConfig, InvalidAblationConfigError, ReceiptIntegrityError
    from omega_engine_operations.domain.benchmarks.models import AdversarialTrapType, AuthorityEffectKind, AuthorityElevationError, BenchmarkError, BenchmarkMetrics, BenchmarkProblem, BenchmarkRunResult, BenchmarkTopology, BenchmarkVerdict, BudgetExhaustedError, BudgetExhaustionReceipt, BudgetExhaustionRecord, CandidateRollout, CandidateType, ExecutionMode, ExhaustionStatus, InvalidBudgetError, LlmAdapterOutput, MachineBlockParseError, QuantitativeMetrics, ScalingCurvePoint, SchemaMismatchError, SearchStrategy, SimplicialMesh, StepRecord, TokenUsage, canonical_rfc8785_json, compute_sha256, sorted_compact_json
    from omega_engine_operations.domain.benchmarks.problem_bank import ProblemBank, build_genus_0_mesh, build_genus_2_mesh, build_problem_bank, build_torus_t2_mesh, create_genus_0_problem, create_genus_2_problem, create_torus_t2_problem, generate_problem_bank, get_canonical_problem
    from omega_engine_operations.domain.benchmarks.protocols import BenchmarkReasonerProtocol, LlmAdapterProtocol, LlmProviderProtocol, SimulationEngineProtocol

__all__ = ['AblationAxis', 'AblationFailureMode', 'AdversarialTrapType', 'AuthorityEffectKind', 'BenchmarkTopology', 'BenchmarkVerdict', 'CandidateType', 'ExecutionMode', 'ExhaustionStatus', 'SearchStrategy', 'AblationAxisOutcome', 'AblationComparisonReceiptV1', 'AblationRunConfig', 'BenchmarkMetrics', 'BenchmarkProblem', 'BenchmarkRunResult', 'BudgetExhaustionReceipt', 'BudgetExhaustionRecord', 'CandidateRollout', 'LlmAdapterOutput', 'QuantitativeMetrics', 'ScalingCurvePoint', 'SimplicialMesh', 'StepRecord', 'TokenUsage', 'build_genus_0_mesh', 'build_genus_2_mesh', 'build_problem_bank', 'build_torus_t2_mesh', 'sorted_compact_json', 'canonical_rfc8785_json', 'compute_sha256', 'create_genus_0_problem', 'create_genus_2_problem', 'create_torus_t2_problem', 'generate_problem_bank', 'get_canonical_problem', 'ProblemBank', 'BenchmarkReasonerProtocol', 'LlmAdapterProtocol', 'LlmProviderProtocol', 'SimulationEngineProtocol', 'AblationDomainError', 'AuthorityElevationError', 'BenchmarkError', 'BudgetExhaustedError', 'InvalidAblationConfigError', 'InvalidBudgetError', 'MachineBlockParseError', 'ReceiptIntegrityError', 'SchemaMismatchError']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'AblationAxis': ('omega_engine_operations.domain.benchmarks.ablation', 'AblationAxis'),
    'AblationAxisOutcome': ('omega_engine_operations.domain.benchmarks.ablation', 'AblationAxisOutcome'),
    'AblationComparisonReceiptV1': ('omega_engine_operations.domain.benchmarks.ablation', 'AblationComparisonReceiptV1'),
    'AblationDomainError': ('omega_engine_operations.domain.benchmarks.ablation', 'AblationDomainError'),
    'AblationFailureMode': ('omega_engine_operations.domain.benchmarks.ablation', 'AblationFailureMode'),
    'AblationRunConfig': ('omega_engine_operations.domain.benchmarks.ablation', 'AblationRunConfig'),
    'InvalidAblationConfigError': ('omega_engine_operations.domain.benchmarks.ablation', 'InvalidAblationConfigError'),
    'ReceiptIntegrityError': ('omega_engine_operations.domain.benchmarks.ablation', 'ReceiptIntegrityError'),
    'AdversarialTrapType': ('omega_engine_operations.domain.benchmarks.models', 'AdversarialTrapType'),
    'AuthorityEffectKind': ('omega_engine_operations.domain.benchmarks.models', 'AuthorityEffectKind'),
    'AuthorityElevationError': ('omega_engine_operations.domain.benchmarks.models', 'AuthorityElevationError'),
    'BenchmarkError': ('omega_engine_operations.domain.benchmarks.models', 'BenchmarkError'),
    'BenchmarkMetrics': ('omega_engine_operations.domain.benchmarks.models', 'BenchmarkMetrics'),
    'BenchmarkProblem': ('omega_engine_operations.domain.benchmarks.models', 'BenchmarkProblem'),
    'BenchmarkRunResult': ('omega_engine_operations.domain.benchmarks.models', 'BenchmarkRunResult'),
    'BenchmarkTopology': ('omega_engine_operations.domain.benchmarks.models', 'BenchmarkTopology'),
    'BenchmarkVerdict': ('omega_engine_operations.domain.benchmarks.models', 'BenchmarkVerdict'),
    'BudgetExhaustedError': ('omega_engine_operations.domain.benchmarks.models', 'BudgetExhaustedError'),
    'BudgetExhaustionReceipt': ('omega_engine_operations.domain.benchmarks.models', 'BudgetExhaustionReceipt'),
    'BudgetExhaustionRecord': ('omega_engine_operations.domain.benchmarks.models', 'BudgetExhaustionRecord'),
    'CandidateRollout': ('omega_engine_operations.domain.benchmarks.models', 'CandidateRollout'),
    'CandidateType': ('omega_engine_operations.domain.benchmarks.models', 'CandidateType'),
    'ExecutionMode': ('omega_engine_operations.domain.benchmarks.models', 'ExecutionMode'),
    'ExhaustionStatus': ('omega_engine_operations.domain.benchmarks.models', 'ExhaustionStatus'),
    'InvalidBudgetError': ('omega_engine_operations.domain.benchmarks.models', 'InvalidBudgetError'),
    'LlmAdapterOutput': ('omega_engine_operations.domain.benchmarks.models', 'LlmAdapterOutput'),
    'MachineBlockParseError': ('omega_engine_operations.domain.benchmarks.models', 'MachineBlockParseError'),
    'QuantitativeMetrics': ('omega_engine_operations.domain.benchmarks.models', 'QuantitativeMetrics'),
    'ScalingCurvePoint': ('omega_engine_operations.domain.benchmarks.models', 'ScalingCurvePoint'),
    'SchemaMismatchError': ('omega_engine_operations.domain.benchmarks.models', 'SchemaMismatchError'),
    'SearchStrategy': ('omega_engine_operations.domain.benchmarks.models', 'SearchStrategy'),
    'SimplicialMesh': ('omega_engine_operations.domain.benchmarks.models', 'SimplicialMesh'),
    'StepRecord': ('omega_engine_operations.domain.benchmarks.models', 'StepRecord'),
    'TokenUsage': ('omega_engine_operations.domain.benchmarks.models', 'TokenUsage'),
    'canonical_rfc8785_json': ('omega_engine_operations.domain.benchmarks.models', 'canonical_rfc8785_json'),
    'compute_sha256': ('omega_engine_operations.domain.benchmarks.models', 'compute_sha256'),
    'sorted_compact_json': ('omega_engine_operations.domain.benchmarks.models', 'sorted_compact_json'),
    'ProblemBank': ('omega_engine_operations.domain.benchmarks.problem_bank', 'ProblemBank'),
    'build_genus_0_mesh': ('omega_engine_operations.domain.benchmarks.problem_bank', 'build_genus_0_mesh'),
    'build_genus_2_mesh': ('omega_engine_operations.domain.benchmarks.problem_bank', 'build_genus_2_mesh'),
    'build_problem_bank': ('omega_engine_operations.domain.benchmarks.problem_bank', 'build_problem_bank'),
    'build_torus_t2_mesh': ('omega_engine_operations.domain.benchmarks.problem_bank', 'build_torus_t2_mesh'),
    'create_genus_0_problem': ('omega_engine_operations.domain.benchmarks.problem_bank', 'create_genus_0_problem'),
    'create_genus_2_problem': ('omega_engine_operations.domain.benchmarks.problem_bank', 'create_genus_2_problem'),
    'create_torus_t2_problem': ('omega_engine_operations.domain.benchmarks.problem_bank', 'create_torus_t2_problem'),
    'generate_problem_bank': ('omega_engine_operations.domain.benchmarks.problem_bank', 'generate_problem_bank'),
    'get_canonical_problem': ('omega_engine_operations.domain.benchmarks.problem_bank', 'get_canonical_problem'),
    'BenchmarkReasonerProtocol': ('omega_engine_operations.domain.benchmarks.protocols', 'BenchmarkReasonerProtocol'),
    'LlmAdapterProtocol': ('omega_engine_operations.domain.benchmarks.protocols', 'LlmAdapterProtocol'),
    'LlmProviderProtocol': ('omega_engine_operations.domain.benchmarks.protocols', 'LlmProviderProtocol'),
    'SimulationEngineProtocol': ('omega_engine_operations.domain.benchmarks.protocols', 'SimulationEngineProtocol'),
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
