"""Rules package for python_development_office."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omega_engine_operads.application.python_development_office.rules.base import ArchitectureRule, AstRule, BaseRule, RuleContext
    from omega_engine_operads.application.python_development_office.rules.clean_arch import CleanArchitectureDependencyRule
    from omega_engine_operads.application.python_development_office.rules.ddd import DomainMustNotImportFrameworkRule
    from omega_engine_operads.application.python_development_office.rules.mvc import ThinControllerRule
    from omega_engine_operads.application.python_development_office.rules.python_pitfalls import ALL_PITFALL_RULES
    from omega_engine_operads.application.python_development_office.rules.registry import RuleRegistry

__all__ = ('ArchitectureRule', 'AstRule', 'BaseRule', 'RuleContext', 'CleanArchitectureDependencyRule', 'DomainMustNotImportFrameworkRule', 'ThinControllerRule', 'ALL_PITFALL_RULES', 'RuleRegistry')

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ArchitectureRule': ('omega_engine_operads.application.python_development_office.rules.base', 'ArchitectureRule'),
    'AstRule': ('omega_engine_operads.application.python_development_office.rules.base', 'AstRule'),
    'BaseRule': ('omega_engine_operads.application.python_development_office.rules.base', 'BaseRule'),
    'RuleContext': ('omega_engine_operads.application.python_development_office.rules.base', 'RuleContext'),
    'CleanArchitectureDependencyRule': ('omega_engine_operads.application.python_development_office.rules.clean_arch', 'CleanArchitectureDependencyRule'),
    'DomainMustNotImportFrameworkRule': ('omega_engine_operads.application.python_development_office.rules.ddd', 'DomainMustNotImportFrameworkRule'),
    'ThinControllerRule': ('omega_engine_operads.application.python_development_office.rules.mvc', 'ThinControllerRule'),
    'ALL_PITFALL_RULES': ('omega_engine_operads.application.python_development_office.rules.python_pitfalls', 'ALL_PITFALL_RULES'),
    'RuleRegistry': ('omega_engine_operads.application.python_development_office.rules.registry', 'RuleRegistry'),
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
