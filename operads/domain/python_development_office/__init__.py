"""Domain package for python_development_office bounded context.

Contains pure domain entities, value objects, enumerations, aggregates, and configuration.
AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from operads.domain.python_development_office.antipattern_finding import AntipatternFinding
    from operads.domain.python_development_office.architecture_config import ArchitectureConfig, DependencyException
    from operads.domain.python_development_office.errors import ArchitecturePolicyViolationError, MalformedConfigurationError, PythonDevOfficeDomainError
    from operads.domain.python_development_office.finding_severity import FindingSeverity
    from operads.domain.python_development_office.imported_symbol import ImportedSymbol
    from operads.domain.python_development_office.module_info import ModuleInfo
    from operads.domain.python_development_office.protocols import AntipatternRuleProtocol, ArchitectureAuditorProtocol, AstScannerProtocol, PythonCodeReviewerProtocol
    from operads.domain.python_development_office.rule_category import RuleCategory
    from operads.domain.python_development_office.scan_result import ScanResult

__all__ = ['AntipatternFinding', 'AntipatternRuleProtocol', 'ArchitectureAuditorProtocol', 'ArchitectureConfig', 'ArchitecturePolicyViolationError', 'AstScannerProtocol', 'DependencyException', 'FindingSeverity', 'ImportedSymbol', 'MalformedConfigurationError', 'ModuleInfo', 'PythonCodeReviewerProtocol', 'PythonDevOfficeDomainError', 'RuleCategory', 'ScanResult']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'AntipatternFinding': ('operads.domain.python_development_office.antipattern_finding', 'AntipatternFinding'),
    'ArchitectureConfig': ('operads.domain.python_development_office.architecture_config', 'ArchitectureConfig'),
    'DependencyException': ('operads.domain.python_development_office.architecture_config', 'DependencyException'),
    'ArchitecturePolicyViolationError': ('operads.domain.python_development_office.errors', 'ArchitecturePolicyViolationError'),
    'MalformedConfigurationError': ('operads.domain.python_development_office.errors', 'MalformedConfigurationError'),
    'PythonDevOfficeDomainError': ('operads.domain.python_development_office.errors', 'PythonDevOfficeDomainError'),
    'FindingSeverity': ('operads.domain.python_development_office.finding_severity', 'FindingSeverity'),
    'ImportedSymbol': ('operads.domain.python_development_office.imported_symbol', 'ImportedSymbol'),
    'ModuleInfo': ('operads.domain.python_development_office.module_info', 'ModuleInfo'),
    'AntipatternRuleProtocol': ('operads.domain.python_development_office.protocols', 'AntipatternRuleProtocol'),
    'ArchitectureAuditorProtocol': ('operads.domain.python_development_office.protocols', 'ArchitectureAuditorProtocol'),
    'AstScannerProtocol': ('operads.domain.python_development_office.protocols', 'AstScannerProtocol'),
    'PythonCodeReviewerProtocol': ('operads.domain.python_development_office.protocols', 'PythonCodeReviewerProtocol'),
    'RuleCategory': ('operads.domain.python_development_office.rule_category', 'RuleCategory'),
    'ScanResult': ('operads.domain.python_development_office.scan_result', 'ScanResult'),
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
