"""OEWAS V3 Application Layer (Use Cases & Inward Ports)."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .commands import CompileCatalogHandler, CompileLicensedTermHandler, CompileProjectionHandler, VerifyCatalogHandler
    from .dtos import ApiErrorDTO, CompileCatalogCommand, CompileCatalogResultDTO, CompileLicensedTermCommand, CompileProjectionCommand, GetCatalogQuery, LicensedTermResultDTO, ProjectionResultDTO, ValidateWorkflowsQuery, VerifyCatalogCommand, VerifyCatalogResultDTO, WorkflowEdgeDTO, WorkflowNodeDTO, WorkflowValidationResultDTO
    from .ports import ClockPort, EstateSourcePort, IdGeneratorPort, JournalPort, LegacyCatalogReaderPort, OeopUnitOfWorkPort, ProjectionManifestPort, SkillDocumentParserPort, StrictOperadPort
    from .queries import GetCatalogHandler, ValidateWorkflowsHandler

__all__ = ['ApiErrorDTO', 'ClockPort', 'CompileCatalogCommand', 'CompileCatalogHandler', 'CompileCatalogResultDTO', 'CompileLicensedTermCommand', 'CompileLicensedTermHandler', 'CompileProjectionCommand', 'CompileProjectionHandler', 'EstateSourcePort', 'GetCatalogHandler', 'GetCatalogQuery', 'IdGeneratorPort', 'JournalPort', 'LegacyCatalogReaderPort', 'LicensedTermResultDTO', 'OeopUnitOfWorkPort', 'ProjectionManifestPort', 'ProjectionResultDTO', 'SkillDocumentParserPort', 'StrictOperadPort', 'ValidateWorkflowsHandler', 'ValidateWorkflowsQuery', 'VerifyCatalogCommand', 'VerifyCatalogHandler', 'VerifyCatalogResultDTO', 'WorkflowEdgeDTO', 'WorkflowNodeDTO', 'WorkflowValidationResultDTO']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'CompileCatalogHandler': ('.commands', 'CompileCatalogHandler'),
    'CompileLicensedTermHandler': ('.commands', 'CompileLicensedTermHandler'),
    'CompileProjectionHandler': ('.commands', 'CompileProjectionHandler'),
    'VerifyCatalogHandler': ('.commands', 'VerifyCatalogHandler'),
    'ApiErrorDTO': ('.dtos', 'ApiErrorDTO'),
    'CompileCatalogCommand': ('.dtos', 'CompileCatalogCommand'),
    'CompileCatalogResultDTO': ('.dtos', 'CompileCatalogResultDTO'),
    'CompileLicensedTermCommand': ('.dtos', 'CompileLicensedTermCommand'),
    'CompileProjectionCommand': ('.dtos', 'CompileProjectionCommand'),
    'GetCatalogQuery': ('.dtos', 'GetCatalogQuery'),
    'LicensedTermResultDTO': ('.dtos', 'LicensedTermResultDTO'),
    'ProjectionResultDTO': ('.dtos', 'ProjectionResultDTO'),
    'ValidateWorkflowsQuery': ('.dtos', 'ValidateWorkflowsQuery'),
    'VerifyCatalogCommand': ('.dtos', 'VerifyCatalogCommand'),
    'VerifyCatalogResultDTO': ('.dtos', 'VerifyCatalogResultDTO'),
    'WorkflowEdgeDTO': ('.dtos', 'WorkflowEdgeDTO'),
    'WorkflowNodeDTO': ('.dtos', 'WorkflowNodeDTO'),
    'WorkflowValidationResultDTO': ('.dtos', 'WorkflowValidationResultDTO'),
    'ClockPort': ('.ports', 'ClockPort'),
    'EstateSourcePort': ('.ports', 'EstateSourcePort'),
    'IdGeneratorPort': ('.ports', 'IdGeneratorPort'),
    'JournalPort': ('.ports', 'JournalPort'),
    'LegacyCatalogReaderPort': ('.ports', 'LegacyCatalogReaderPort'),
    'OeopUnitOfWorkPort': ('.ports', 'OeopUnitOfWorkPort'),
    'ProjectionManifestPort': ('.ports', 'ProjectionManifestPort'),
    'SkillDocumentParserPort': ('.ports', 'SkillDocumentParserPort'),
    'StrictOperadPort': ('.ports', 'StrictOperadPort'),
    'GetCatalogHandler': ('.queries', 'GetCatalogHandler'),
    'ValidateWorkflowsHandler': ('.queries', 'ValidateWorkflowsHandler'),
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
