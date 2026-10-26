"""DTOs for OEWAS V3 Application Layer."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .api_error_dto import ApiErrorDTO
    from .command_dtos import CompileCatalogCommand, CompileLicensedTermCommand, CompileProjectionCommand, VerifyCatalogCommand
    from .query_dtos import GetCatalogQuery, ValidateWorkflowsQuery, WorkflowEdgeDTO, WorkflowNodeDTO
    from .success_dtos import CompileCatalogResultDTO, LicensedTermResultDTO, ProjectionResultDTO, VerifyCatalogResultDTO, WorkflowValidationResultDTO

__all__ = ['ApiErrorDTO', 'CompileCatalogCommand', 'CompileCatalogResultDTO', 'CompileLicensedTermCommand', 'CompileProjectionCommand', 'GetCatalogQuery', 'LicensedTermResultDTO', 'ProjectionResultDTO', 'ValidateWorkflowsQuery', 'VerifyCatalogCommand', 'VerifyCatalogResultDTO', 'WorkflowEdgeDTO', 'WorkflowNodeDTO', 'WorkflowValidationResultDTO']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ApiErrorDTO': ('.api_error_dto', 'ApiErrorDTO'),
    'CompileCatalogCommand': ('.command_dtos', 'CompileCatalogCommand'),
    'CompileLicensedTermCommand': ('.command_dtos', 'CompileLicensedTermCommand'),
    'CompileProjectionCommand': ('.command_dtos', 'CompileProjectionCommand'),
    'VerifyCatalogCommand': ('.command_dtos', 'VerifyCatalogCommand'),
    'GetCatalogQuery': ('.query_dtos', 'GetCatalogQuery'),
    'ValidateWorkflowsQuery': ('.query_dtos', 'ValidateWorkflowsQuery'),
    'WorkflowEdgeDTO': ('.query_dtos', 'WorkflowEdgeDTO'),
    'WorkflowNodeDTO': ('.query_dtos', 'WorkflowNodeDTO'),
    'CompileCatalogResultDTO': ('.success_dtos', 'CompileCatalogResultDTO'),
    'LicensedTermResultDTO': ('.success_dtos', 'LicensedTermResultDTO'),
    'ProjectionResultDTO': ('.success_dtos', 'ProjectionResultDTO'),
    'VerifyCatalogResultDTO': ('.success_dtos', 'VerifyCatalogResultDTO'),
    'WorkflowValidationResultDTO': ('.success_dtos', 'WorkflowValidationResultDTO'),
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
