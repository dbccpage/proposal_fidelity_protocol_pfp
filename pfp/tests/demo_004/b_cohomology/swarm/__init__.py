"""Compatibility names for the cohomology challenge front end."""

from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "BudgetController": "budget_controller",
    "BudgetExhaustedRefusal": "budget_controller",
    "CostLedger": "budget_controller",
    "CohomologyCertificate": "cohomology_solver",
    "CohomologySolver": "cohomology_solver",
    "verify_independent_certificate": "cohomology_solver",
    "DdcStepRecord": "ddc_tracer",
    "DdcTracer": "ddc_tracer",
    "LggrDetector": "lggr_detector",
    "LggrVerdict": "lggr_detector",
    "AdversaryCohomologyOverseer": "adversary_overseer",
    "AdversarySwarmResult": "adversary_overseer",
    "AdversaryBatteryResult": "adversary_overseer",
}
__all__ = list(_EXPORTS)


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(name)
    value = getattr(import_module(f".{_EXPORTS[name]}", __name__), name)
    globals()[name] = value
    return value
