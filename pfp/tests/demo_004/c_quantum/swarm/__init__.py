"""Lazy exports; solver imports do not initialize optional host integrations."""

from importlib import import_module

_MODULES = {
    "BudgetController": "budget_controller",
    "BudgetExhaustedRefusal": "budget_controller",
    "CostEntry": "budget_controller",
    "CostLedger": "budget_controller",
    "DdcStepRecord": "ddc_tracer",
    "DdcTracer": "ddc_tracer",
    "Q40Certificate": "q40_solver",
    "Q40StabilizerSolver": "q40_solver",
    "WolandQuantumOverseer": "woland_overseer",
    "WolandQuantumSwarmResult": "woland_overseer",
}
__all__ = list(_MODULES)


def __getattr__(name):
    if name not in _MODULES:
        raise AttributeError(name)
    value = getattr(import_module(f"{__name__}.{_MODULES[name]}"), name)
    globals()[name] = value
    return value
