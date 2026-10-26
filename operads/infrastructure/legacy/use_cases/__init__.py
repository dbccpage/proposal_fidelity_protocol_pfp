"""Use cases for parsing the estate, compiling operad terms, and validating workflows."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .compile_operad_terms import CompileOperadTermsUseCase
    from .parse_estate import ParseEstateUseCase
    from .validate_workflows import ValidateWorkflowsUseCase, WorkflowValidationReport

__all__ = ['CompileOperadTermsUseCase', 'ParseEstateUseCase', 'ValidateWorkflowsUseCase', 'WorkflowValidationReport']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'CompileOperadTermsUseCase': ('.compile_operad_terms', 'CompileOperadTermsUseCase'),
    'ParseEstateUseCase': ('.parse_estate', 'ParseEstateUseCase'),
    'ValidateWorkflowsUseCase': ('.validate_workflows', 'ValidateWorkflowsUseCase'),
    'WorkflowValidationReport': ('.validate_workflows', 'WorkflowValidationReport'),
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
