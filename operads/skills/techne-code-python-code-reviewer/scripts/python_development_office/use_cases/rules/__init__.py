"""Rules package for python_development_office."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from python_development_office.use_cases.rules.base import ArchitectureRule, AstRule, BaseRule, RuleContext
    from python_development_office.use_cases.rules.clean_arch import CleanArchitectureDependencyRule
    from python_development_office.use_cases.rules.ddd import DomainMustNotImportFrameworkRule
    from python_development_office.use_cases.rules.mvc import ThinControllerRule
    from python_development_office.use_cases.rules.python_pitfalls import ALL_PITFALL_RULES
    from python_development_office.use_cases.rules.registry import RuleRegistry

__all__ = ('ArchitectureRule', 'AstRule', 'BaseRule', 'RuleContext', 'CleanArchitectureDependencyRule', 'DomainMustNotImportFrameworkRule', 'ThinControllerRule', 'ALL_PITFALL_RULES', 'RuleRegistry')

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ArchitectureRule': ('python_development_office.use_cases.rules.base', 'ArchitectureRule'),
    'AstRule': ('python_development_office.use_cases.rules.base', 'AstRule'),
    'BaseRule': ('python_development_office.use_cases.rules.base', 'BaseRule'),
    'RuleContext': ('python_development_office.use_cases.rules.base', 'RuleContext'),
    'CleanArchitectureDependencyRule': ('python_development_office.use_cases.rules.clean_arch', 'CleanArchitectureDependencyRule'),
    'DomainMustNotImportFrameworkRule': ('python_development_office.use_cases.rules.ddd', 'DomainMustNotImportFrameworkRule'),
    'ThinControllerRule': ('python_development_office.use_cases.rules.mvc', 'ThinControllerRule'),
    'ALL_PITFALL_RULES': ('python_development_office.use_cases.rules.python_pitfalls', 'ALL_PITFALL_RULES'),
    'RuleRegistry': ('python_development_office.use_cases.rules.registry', 'RuleRegistry'),
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
