"""Standalone Symbol Game Engine Package.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = (
    "ObstructionScore",
    "PacketCodec",
    "ProblemReductionResult",
    "ProposalEvaluator",
    "StepVerdict",
    "SymbolGameController",
    "SymbolGameEngine",
    "SymbolGameEnvelope",
    "SymbolGameStepOutcome",
    "SymbolToken",
    "initialize_exact_ports",
    "ModeCluster",
    "ModeContract",
    "ModesManifest",
    "find_modes_dir",
    "discover_modes_manifest",
    "load_all_mode_contracts",
    "load_mode_contract",
    "validate_mode_catalog_closure",
    "ListModesUseCase",
    "GetModeUseCase",
    "ValidateModesUseCase",
)

_EXPORTS: dict[str, tuple[str, str]] = {
    "ObstructionScore": (".domain.models", "ObstructionScore"),
    "PacketCodec": (".domain.packet_codec", "PacketCodec"),
    "ProblemReductionResult": (".domain.models", "ProblemReductionResult"),
    "ProposalEvaluator": (".domain.evaluator", "ProposalEvaluator"),
    "StepVerdict": (".domain.models", "StepVerdict"),
    "SymbolGameController": (".controllers.symbol_game_controller", "SymbolGameController"),
    "SymbolGameEngine": (".controllers.symbol_game_engine", "SymbolGameEngine"),
    "SymbolGameEnvelope": (".domain.models", "SymbolGameEnvelope"),
    "SymbolGameStepOutcome": (".domain.models", "SymbolGameStepOutcome"),
    "SymbolToken": (".domain.models", "SymbolToken"),
    "ModeCluster": (".domain.modes", "ModeCluster"),
    "ModeContract": (".domain.modes", "ModeContract"),
    "ModesManifest": (".domain.modes", "ModesManifest"),
    "find_modes_dir": (".infrastructure.adapters.mode_discovery", "find_modes_dir"),
    "discover_modes_manifest": (
        ".infrastructure.adapters.mode_discovery",
        "discover_modes_manifest",
    ),
    "load_all_mode_contracts": (
        ".infrastructure.adapters.mode_discovery",
        "load_all_mode_contracts",
    ),
    "load_mode_contract": (".infrastructure.adapters.mode_discovery", "load_mode_contract"),
    "validate_mode_catalog_closure": (
        ".infrastructure.adapters.mode_discovery",
        "validate_mode_catalog_closure",
    ),
    "ListModesUseCase": (".use_cases.modes", "ListModesUseCase"),
    "GetModeUseCase": (".use_cases.modes", "GetModeUseCase"),
    "ValidateModesUseCase": (".use_cases.modes", "ValidateModesUseCase"),
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        module_path, attr_name = _EXPORTS[name]
        module = importlib.import_module(module_path, __name__)
        val = getattr(module, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))


def initialize_exact_ports() -> None:
    """Install the native exact adapter behind the domain ports.

    A host binary that is not built is not an error here: the adapter records
    why and refuses at first use. Anything else raised while wiring the ports is
    a defect, so it propagates instead of leaving them silently unset.
    """
    from .domain.exact.linalg import set_linear_algebra_port
    from .domain.ports.cohomology_port import register_default_cohomology_solver
    from .domain.ports.scoring_port import register_default_scoring_port
    from .domain.solvers.kinds import set_functional_port, set_holonomy_port, set_homology_port
    from .infrastructure.adapters.exact_rust_adapter import RustExactEngineAdapter
    from .infrastructure.adapters.rust_cohomology_adapter import RustCohomologySolverAdapter
    from .infrastructure.adapters.scoring_rust import RustScoringAdapter

    adapter = RustExactEngineAdapter()
    set_linear_algebra_port(adapter)
    set_homology_port(adapter)
    set_holonomy_port(adapter)
    set_functional_port(adapter)
    register_default_cohomology_solver(RustCohomologySolverAdapter())
    register_default_scoring_port(RustScoringAdapter())


_initialize_exact_ports = initialize_exact_ports

_EXPORTS.update(
    {
        "Carrier": (".domain.homology.carrier", "Carrier"),
        "Cochain": (".domain.homology.cochain", "Cochain"),
        "ContractAuditReceipt": (".domain.contracts.contracts", "ContractAuditReceipt"),
        "ContractSpec": (".domain.contracts.contracts", "ContractSpec"),
        "CycleBalanceQuartet": (".domain.homology.cycle_balance", "CycleBalanceQuartet"),
        "DDCTape": (".domain.homology.ddc", "DDCTape"),
        "DemoCatalog": (".domain.stages.demos", "DemoCatalog"),
        "DemoRunReceipt": (".domain.stages.demos", "DemoRunReceipt"),
        "DemoSpec": (".domain.stages.demos", "DemoSpec"),
        "DomainError": (".domain.kernel.result", "DomainError"),
        "EvaluationVerdict": (".domain.kernel.result", "EvaluationVerdict"),
        "GateReceipt": (".domain.contracts.gates", "GateReceipt"),
        "GateRegister": (".domain.contracts.gate_types", "GateRegister"),
        "GateSpec": (".domain.contracts.gates", "GateSpec"),
        "GateVerdict": (".domain.contracts.gates", "GateVerdict"),
        "ModeFile": (".domain.stages.modes", "ModeFile"),
        "NormalFormContract": (".domain.normal_forms", "NormalFormContract"),
        "PacketEnvelope": (".domain.prompts.packets", "PacketEnvelope"),
        "PfpPrompt": (".domain.prompts.pfp_prompt", "PfpPrompt"),
        "PromptPacket": (".domain.prompts.prompts", "PromptPacket"),
        "PromptTemplate": (".domain.prompts.prompts", "PromptTemplate"),
        "RefusalCode": (".domain.kernel.result", "RefusalCode"),
        "Result": (".domain.kernel.result", "Result"),
        "RewriteReceipt": (".domain.rewriting.rewrites", "RewriteReceipt"),
        "RewriteRequest": (".domain.rewriting.rewrites", "RewriteRequest"),
        "SpanPartition": (".domain.rewriting.rewriting_types", "SpanPartition"),
        "TerminalStatus": (".domain.kernel.result", "TerminalStatus"),
        "WolandGateId": (".domain.contracts.gates", "WolandGateId"),
        "PfpController": (".controllers.pfp_controller", "PfpController"),
        "build_parser": (".entrypoints.cli.pfp", "build_parser"),
        "main": (".entrypoints.cli.pfp", "main"),
        "EvaluatePilotSuiteUseCase": (
            ".use_cases.evaluate_pilot_suite",
            "EvaluatePilotSuiteUseCase",
        ),
        "PipelineExecutionReceipt": (
            ".use_cases.execute_stage_pipeline",
            "PipelineExecutionReceipt",
        ),
    }
)
__all__ = list(dict.fromkeys([*__all__, *_EXPORTS]))
