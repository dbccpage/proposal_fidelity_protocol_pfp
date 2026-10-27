"""Python Development Office use cases and rule analyzers."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from operads.application.python_development_office.ast_utils import extract_imported_symbols, extract_module_imports
    from operads.application.python_development_office.project import ProjectScanner
    from operads.application.python_development_office.rules import ALL_PITFALL_RULES, ArchitectureRule, AstRule, BaseRule, CleanArchitectureDependencyRule, DomainMustNotImportFrameworkRule, RuleContext, RuleRegistry, ThinControllerRule
    from operads.application.python_development_office.visitor import RuleVisitor, scan_source_ast

__all__ = ('ProjectScanner', 'RuleVisitor', 'scan_source_ast', 'extract_imported_symbols', 'extract_module_imports', 'RuleRegistry', 'BaseRule', 'AstRule', 'ArchitectureRule', 'RuleContext', 'CleanArchitectureDependencyRule', 'DomainMustNotImportFrameworkRule', 'ThinControllerRule', 'ALL_PITFALL_RULES')

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'extract_imported_symbols': ('operads.application.python_development_office.ast_utils', 'extract_imported_symbols'),
    'extract_module_imports': ('operads.application.python_development_office.ast_utils', 'extract_module_imports'),
    'ProjectScanner': ('operads.application.python_development_office.project', 'ProjectScanner'),
    'ALL_PITFALL_RULES': ('operads.application.python_development_office.rules', 'ALL_PITFALL_RULES'),
    'ArchitectureRule': ('operads.application.python_development_office.rules', 'ArchitectureRule'),
    'AstRule': ('operads.application.python_development_office.rules', 'AstRule'),
    'BaseRule': ('operads.application.python_development_office.rules', 'BaseRule'),
    'CleanArchitectureDependencyRule': ('operads.application.python_development_office.rules', 'CleanArchitectureDependencyRule'),
    'DomainMustNotImportFrameworkRule': ('operads.application.python_development_office.rules', 'DomainMustNotImportFrameworkRule'),
    'RuleContext': ('operads.application.python_development_office.rules', 'RuleContext'),
    'RuleRegistry': ('operads.application.python_development_office.rules', 'RuleRegistry'),
    'ThinControllerRule': ('operads.application.python_development_office.rules', 'ThinControllerRule'),
    'RuleVisitor': ('operads.application.python_development_office.visitor', 'RuleVisitor'),
    'scan_source_ast': ('operads.application.python_development_office.visitor', 'scan_source_ast'),
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
