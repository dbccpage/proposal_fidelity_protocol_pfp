"""Domain package for python_development_office bounded context.

Contains pure domain entities, value objects, enumerations, aggregates, and configuration.
AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from python_development_office.domain.antipattern_finding import AntipatternFinding
    from python_development_office.domain.architecture_config import ArchitectureConfig, DependencyException
    from python_development_office.domain.finding_severity import FindingSeverity
    from python_development_office.domain.imported_symbol import ImportedSymbol
    from python_development_office.domain.module_info import ModuleInfo
    from python_development_office.domain.rule_category import RuleCategory
    from python_development_office.domain.scan_result import ScanResult

__all__ = ['AntipatternFinding', 'ArchitectureConfig', 'DependencyException', 'FindingSeverity', 'ImportedSymbol', 'ModuleInfo', 'RuleCategory', 'ScanResult']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'AntipatternFinding': ('python_development_office.domain.antipattern_finding', 'AntipatternFinding'),
    'ArchitectureConfig': ('python_development_office.domain.architecture_config', 'ArchitectureConfig'),
    'DependencyException': ('python_development_office.domain.architecture_config', 'DependencyException'),
    'FindingSeverity': ('python_development_office.domain.finding_severity', 'FindingSeverity'),
    'ImportedSymbol': ('python_development_office.domain.imported_symbol', 'ImportedSymbol'),
    'ModuleInfo': ('python_development_office.domain.module_info', 'ModuleInfo'),
    'RuleCategory': ('python_development_office.domain.rule_category', 'RuleCategory'),
    'ScanResult': ('python_development_office.domain.scan_result', 'ScanResult'),
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
