"""Application layer surface for Omega Engine Agentic Swarm."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

from omega_engine_woland.stage.ddc_alphabet_source import install_ddc_alphabet

install_ddc_alphabet()

from .run_swarm import SwarmRuntimeV1, run_swarm

if TYPE_CHECKING:
    from .emission import (
        AntibodySink,
        CemeterySink,
        DdaSink,
        EmitterSuiteV1,
        GenealogySink,
        IntelligenceEventV1,
        SgtSink,
        SymbolGamePacketSink,
        UnsSink,
        UtsSink,
        build_intelligence_event,
        compute_sbe_metrics,
        emit_event,
    )
    from .oscillation_detector import (
        OscillationDetectorV1,
        extract_proposal_tokens,
        proposal_semantic_distance,
    )
    from .ports import (
        AntibodyStorePort,
        ContinuationPortV1,
        ContinueDecisionKindV1,
        ContinueDecisionV1,
        EventPortV1,
        GenealogyStorePort,
        HostPortV1,
        MemoryPortV1,
        ModelPortV1,
        SchedulerPortV1,
        SeatPortV1,
        SkillPortV1,
        ToolPortV1,
        ValuatorPortV1,
    )
    from .replay import (
        build_swarm_run_receipt,
        parse_swarm_run_receipt,
        verify_swarm_run_receipt,
    )
    from .scheduler import DeterministicSchedulerV1, validate_swarm_composition

__all__ = [
    "AntibodySink",
    "AntibodyStorePort",
    "CemeterySink",
    "ContinuationPortV1",
    "ContinueDecisionKindV1",
    "ContinueDecisionV1",
    "DdaSink",
    "DeterministicSchedulerV1",
    "EmitterSuiteV1",
    "EventPortV1",
    "GenealogySink",
    "GenealogyStorePort",
    "HostPortV1",
    "IntelligenceEventV1",
    "MemoryPortV1",
    "ModelPortV1",
    "OscillationDetectorV1",
    "SchedulerPortV1",
    "SeatPortV1",
    "SgtSink",
    "SkillPortV1",
    "SwarmRuntimeV1",
    "SymbolGamePacketSink",
    "ToolPortV1",
    "UnsSink",
    "UtsSink",
    "ValuatorPortV1",
    "build_intelligence_event",
    "build_swarm_run_receipt",
    "compute_sbe_metrics",
    "emit_event",
    "extract_proposal_tokens",
    "parse_swarm_run_receipt",
    "proposal_semantic_distance",
    "run_swarm",
    "validate_swarm_composition",
    "verify_swarm_run_receipt",
]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "AntibodySink": (".emission", "AntibodySink"),
    "CemeterySink": (".emission", "CemeterySink"),
    "DdaSink": (".emission", "DdaSink"),
    "EmitterSuiteV1": (".emission", "EmitterSuiteV1"),
    "GenealogySink": (".emission", "GenealogySink"),
    "IntelligenceEventV1": (".emission", "IntelligenceEventV1"),
    "SgtSink": (".emission", "SgtSink"),
    "SymbolGamePacketSink": (".emission", "SymbolGamePacketSink"),
    "UnsSink": (".emission", "UnsSink"),
    "UtsSink": (".emission", "UtsSink"),
    "build_intelligence_event": (".emission", "build_intelligence_event"),
    "compute_sbe_metrics": (".emission", "compute_sbe_metrics"),
    "emit_event": (".emission", "emit_event"),
    "OscillationDetectorV1": (".oscillation_detector", "OscillationDetectorV1"),
    "extract_proposal_tokens": (".oscillation_detector", "extract_proposal_tokens"),
    "proposal_semantic_distance": (".oscillation_detector", "proposal_semantic_distance"),
    "AntibodyStorePort": (".ports", "AntibodyStorePort"),
    "ContinuationPortV1": (".ports", "ContinuationPortV1"),
    "ContinueDecisionKindV1": (".ports", "ContinueDecisionKindV1"),
    "ContinueDecisionV1": (".ports", "ContinueDecisionV1"),
    "EventPortV1": (".ports", "EventPortV1"),
    "GenealogyStorePort": (".ports", "GenealogyStorePort"),
    "HostPortV1": (".ports", "HostPortV1"),
    "MemoryPortV1": (".ports", "MemoryPortV1"),
    "ModelPortV1": (".ports", "ModelPortV1"),
    "SchedulerPortV1": (".ports", "SchedulerPortV1"),
    "SeatPortV1": (".ports", "SeatPortV1"),
    "SkillPortV1": (".ports", "SkillPortV1"),
    "ToolPortV1": (".ports", "ToolPortV1"),
    "ValuatorPortV1": (".ports", "ValuatorPortV1"),
    "build_swarm_run_receipt": (".replay", "build_swarm_run_receipt"),
    "parse_swarm_run_receipt": (".replay", "parse_swarm_run_receipt"),
    "verify_swarm_run_receipt": (".replay", "verify_swarm_run_receipt"),
    "DeterministicSchedulerV1": (".scheduler", "DeterministicSchedulerV1"),
    "validate_swarm_composition": (".scheduler", "validate_swarm_composition"),
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
