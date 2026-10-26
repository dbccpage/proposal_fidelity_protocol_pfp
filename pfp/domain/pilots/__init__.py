"""PFP Pilots and Fail-Closed Verification Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .certified_ladder import DebtMetric, EvaluationReport, HypothesisDefinition, HypothesisVerdict, P0ControlItem, P0GateControlReceipt, P0ItemResult, build_evaluation_report, evaluate_h0, evaluate_h1, evaluate_h2, evaluate_h3, evaluate_h4, evaluate_h5, evaluate_h6, evaluate_h7, evaluate_h8, evaluate_h9, evaluate_h10, evaluate_h11, evaluate_h12, evaluate_h13
    from .dimension_models import DimensionEntry, DimensionRegister, DimensionVocabulary, OutcomeEntry, RegistrySyncReport
    from .fail_closed_gate import FailClosedRefusalGate, GateEvaluationResult
    from .pilot import LlmPilotFamily, NoLlmPilotFamily, ParameterAxis, PilotBudget, PilotCatalog, PilotInstance, PilotRun

__all__ = ['DebtMetric', 'DimensionEntry', 'DimensionRegister', 'DimensionVocabulary', 'EvaluationReport', 'FailClosedRefusalGate', 'GateEvaluationResult', 'HypothesisDefinition', 'HypothesisVerdict', 'LlmPilotFamily', 'NoLlmPilotFamily', 'OutcomeEntry', 'P0ControlItem', 'P0GateControlReceipt', 'P0ItemResult', 'ParameterAxis', 'PilotBudget', 'PilotCatalog', 'PilotInstance', 'PilotRun', 'RegistrySyncReport', 'build_evaluation_report', 'evaluate_h0', 'evaluate_h1', 'evaluate_h2', 'evaluate_h3', 'evaluate_h4', 'evaluate_h5', 'evaluate_h6', 'evaluate_h7', 'evaluate_h8', 'evaluate_h9', 'evaluate_h10', 'evaluate_h11', 'evaluate_h12', 'evaluate_h13']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'DebtMetric': ('.certified_ladder', 'DebtMetric'),
    'EvaluationReport': ('.certified_ladder', 'EvaluationReport'),
    'HypothesisDefinition': ('.certified_ladder', 'HypothesisDefinition'),
    'HypothesisVerdict': ('.certified_ladder', 'HypothesisVerdict'),
    'P0ControlItem': ('.certified_ladder', 'P0ControlItem'),
    'P0GateControlReceipt': ('.certified_ladder', 'P0GateControlReceipt'),
    'P0ItemResult': ('.certified_ladder', 'P0ItemResult'),
    'build_evaluation_report': ('.certified_ladder', 'build_evaluation_report'),
    'evaluate_h0': ('.certified_ladder', 'evaluate_h0'),
    'evaluate_h1': ('.certified_ladder', 'evaluate_h1'),
    'evaluate_h2': ('.certified_ladder', 'evaluate_h2'),
    'evaluate_h3': ('.certified_ladder', 'evaluate_h3'),
    'evaluate_h4': ('.certified_ladder', 'evaluate_h4'),
    'evaluate_h5': ('.certified_ladder', 'evaluate_h5'),
    'evaluate_h6': ('.certified_ladder', 'evaluate_h6'),
    'evaluate_h7': ('.certified_ladder', 'evaluate_h7'),
    'evaluate_h8': ('.certified_ladder', 'evaluate_h8'),
    'evaluate_h9': ('.certified_ladder', 'evaluate_h9'),
    'evaluate_h10': ('.certified_ladder', 'evaluate_h10'),
    'evaluate_h11': ('.certified_ladder', 'evaluate_h11'),
    'evaluate_h12': ('.certified_ladder', 'evaluate_h12'),
    'evaluate_h13': ('.certified_ladder', 'evaluate_h13'),
    'DimensionEntry': ('.dimension_models', 'DimensionEntry'),
    'DimensionRegister': ('.dimension_models', 'DimensionRegister'),
    'DimensionVocabulary': ('.dimension_models', 'DimensionVocabulary'),
    'OutcomeEntry': ('.dimension_models', 'OutcomeEntry'),
    'RegistrySyncReport': ('.dimension_models', 'RegistrySyncReport'),
    'FailClosedRefusalGate': ('.fail_closed_gate', 'FailClosedRefusalGate'),
    'GateEvaluationResult': ('.fail_closed_gate', 'GateEvaluationResult'),
    'LlmPilotFamily': ('.pilot', 'LlmPilotFamily'),
    'NoLlmPilotFamily': ('.pilot', 'NoLlmPilotFamily'),
    'ParameterAxis': ('.pilot', 'ParameterAxis'),
    'PilotBudget': ('.pilot', 'PilotBudget'),
    'PilotCatalog': ('.pilot', 'PilotCatalog'),
    'PilotInstance': ('.pilot', 'PilotInstance'),
    'PilotRun': ('.pilot', 'PilotRun'),
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
