"""Rules package for python_development_office."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from operads.application.python_development_office.rules.base import ArchitectureRule, AstRule, BaseRule, RuleContext
    from operads.application.python_development_office.rules.clean_arch import CleanArchitectureDependencyRule
    from operads.application.python_development_office.rules.ddd import DomainMustNotImportFrameworkRule
    from operads.application.python_development_office.rules.mvc import ThinControllerRule
    from operads.application.python_development_office.rules.python_pitfalls import ALL_PITFALL_RULES
    from operads.application.python_development_office.rules.registry import RuleRegistry

__all__ = ('ArchitectureRule', 'AstRule', 'BaseRule', 'RuleContext', 'CleanArchitectureDependencyRule', 'DomainMustNotImportFrameworkRule', 'ThinControllerRule', 'ALL_PITFALL_RULES', 'RuleRegistry')

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ArchitectureRule': ('operads.application.python_development_office.rules.base', 'ArchitectureRule'),
    'AstRule': ('operads.application.python_development_office.rules.base', 'AstRule'),
    'BaseRule': ('operads.application.python_development_office.rules.base', 'BaseRule'),
    'RuleContext': ('operads.application.python_development_office.rules.base', 'RuleContext'),
    'CleanArchitectureDependencyRule': ('operads.application.python_development_office.rules.clean_arch', 'CleanArchitectureDependencyRule'),
    'DomainMustNotImportFrameworkRule': ('operads.application.python_development_office.rules.ddd', 'DomainMustNotImportFrameworkRule'),
    'ThinControllerRule': ('operads.application.python_development_office.rules.mvc', 'ThinControllerRule'),
    'ALL_PITFALL_RULES': ('operads.application.python_development_office.rules.python_pitfalls', 'ALL_PITFALL_RULES'),
    'RuleRegistry': ('operads.application.python_development_office.rules.registry', 'RuleRegistry'),
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
