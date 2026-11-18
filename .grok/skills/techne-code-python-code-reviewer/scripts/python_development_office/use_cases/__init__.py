"""Python Development Office use cases and rule analyzers."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from python_development_office.use_cases.ast_utils import extract_imported_symbols, extract_module_imports
    from python_development_office.use_cases.project import ProjectScanner
    from python_development_office.use_cases.rules import ALL_PITFALL_RULES, ArchitectureRule, AstRule, BaseRule, CleanArchitectureDependencyRule, DomainMustNotImportFrameworkRule, RuleContext, RuleRegistry, ThinControllerRule
    from python_development_office.use_cases.visitor import RuleVisitor, scan_file_ast

__all__ = ('ProjectScanner', 'RuleVisitor', 'scan_file_ast', 'extract_imported_symbols', 'extract_module_imports', 'RuleRegistry', 'BaseRule', 'AstRule', 'ArchitectureRule', 'RuleContext', 'CleanArchitectureDependencyRule', 'DomainMustNotImportFrameworkRule', 'ThinControllerRule', 'ALL_PITFALL_RULES')

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'extract_imported_symbols': ('python_development_office.use_cases.ast_utils', 'extract_imported_symbols'),
    'extract_module_imports': ('python_development_office.use_cases.ast_utils', 'extract_module_imports'),
    'ProjectScanner': ('python_development_office.use_cases.project', 'ProjectScanner'),
    'ALL_PITFALL_RULES': ('python_development_office.use_cases.rules', 'ALL_PITFALL_RULES'),
    'ArchitectureRule': ('python_development_office.use_cases.rules', 'ArchitectureRule'),
    'AstRule': ('python_development_office.use_cases.rules', 'AstRule'),
    'BaseRule': ('python_development_office.use_cases.rules', 'BaseRule'),
    'CleanArchitectureDependencyRule': ('python_development_office.use_cases.rules', 'CleanArchitectureDependencyRule'),
    'DomainMustNotImportFrameworkRule': ('python_development_office.use_cases.rules', 'DomainMustNotImportFrameworkRule'),
    'RuleContext': ('python_development_office.use_cases.rules', 'RuleContext'),
    'RuleRegistry': ('python_development_office.use_cases.rules', 'RuleRegistry'),
    'ThinControllerRule': ('python_development_office.use_cases.rules', 'ThinControllerRule'),
    'RuleVisitor': ('python_development_office.use_cases.visitor', 'RuleVisitor'),
    'scan_file_ast': ('python_development_office.use_cases.visitor', 'scan_file_ast'),
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
