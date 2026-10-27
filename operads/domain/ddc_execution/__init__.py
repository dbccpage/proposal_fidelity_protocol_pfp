"""Operad Bounded Context Domain Layer.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from operads.domain.ddc_execution.constants import ADMITTED_FINITE_COLOURS, EVIDENCE_TRACE_SCHEMA, REQUIRED_CONTRACTIVE_RUNS
    from operads.domain.ddc_execution.entities import OperadMorphism
    from operads.domain.ddc_execution.enums import MorphismExecutionStatus, OperadColour, ResidualEffect
    from operads.domain.ddc_execution.errors import ArityMismatchError, ColourMismatchError, OperadDomainError, PermissionDeniedError, ResidualHonestyError, TraceLedgerStorageError, UnknownMorphismError
    from operads.domain.ddc_execution.protocols import MorphismEvaluatorPort, OperadRegistryPort, TraceStoragePort
    from operads.domain.ddc_execution.value_objects import ArtifactOutput, ColourSignature, EvidenceTraceReport, ExecutionRunRecord, OperadOperation

__all__ = ['ADMITTED_FINITE_COLOURS', 'EVIDENCE_TRACE_SCHEMA', 'REQUIRED_CONTRACTIVE_RUNS', 'OperadMorphism', 'MorphismExecutionStatus', 'OperadColour', 'ResidualEffect', 'ArityMismatchError', 'ColourMismatchError', 'OperadDomainError', 'PermissionDeniedError', 'ResidualHonestyError', 'TraceLedgerStorageError', 'UnknownMorphismError', 'MorphismEvaluatorPort', 'OperadRegistryPort', 'TraceStoragePort', 'ArtifactOutput', 'ColourSignature', 'EvidenceTraceReport', 'ExecutionRunRecord', 'OperadOperation']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ADMITTED_FINITE_COLOURS': ('operads.domain.ddc_execution.constants', 'ADMITTED_FINITE_COLOURS'),
    'EVIDENCE_TRACE_SCHEMA': ('operads.domain.ddc_execution.constants', 'EVIDENCE_TRACE_SCHEMA'),
    'REQUIRED_CONTRACTIVE_RUNS': ('operads.domain.ddc_execution.constants', 'REQUIRED_CONTRACTIVE_RUNS'),
    'OperadMorphism': ('operads.domain.ddc_execution.entities', 'OperadMorphism'),
    'MorphismExecutionStatus': ('operads.domain.ddc_execution.enums', 'MorphismExecutionStatus'),
    'OperadColour': ('operads.domain.ddc_execution.enums', 'OperadColour'),
    'ResidualEffect': ('operads.domain.ddc_execution.enums', 'ResidualEffect'),
    'ArityMismatchError': ('operads.domain.ddc_execution.errors', 'ArityMismatchError'),
    'ColourMismatchError': ('operads.domain.ddc_execution.errors', 'ColourMismatchError'),
    'OperadDomainError': ('operads.domain.ddc_execution.errors', 'OperadDomainError'),
    'PermissionDeniedError': ('operads.domain.ddc_execution.errors', 'PermissionDeniedError'),
    'ResidualHonestyError': ('operads.domain.ddc_execution.errors', 'ResidualHonestyError'),
    'TraceLedgerStorageError': ('operads.domain.ddc_execution.errors', 'TraceLedgerStorageError'),
    'UnknownMorphismError': ('operads.domain.ddc_execution.errors', 'UnknownMorphismError'),
    'MorphismEvaluatorPort': ('operads.domain.ddc_execution.protocols', 'MorphismEvaluatorPort'),
    'OperadRegistryPort': ('operads.domain.ddc_execution.protocols', 'OperadRegistryPort'),
    'TraceStoragePort': ('operads.domain.ddc_execution.protocols', 'TraceStoragePort'),
    'ArtifactOutput': ('operads.domain.ddc_execution.value_objects', 'ArtifactOutput'),
    'ColourSignature': ('operads.domain.ddc_execution.value_objects', 'ColourSignature'),
    'EvidenceTraceReport': ('operads.domain.ddc_execution.value_objects', 'EvidenceTraceReport'),
    'ExecutionRunRecord': ('operads.domain.ddc_execution.value_objects', 'ExecutionRunRecord'),
    'OperadOperation': ('operads.domain.ddc_execution.value_objects', 'OperadOperation'),
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
