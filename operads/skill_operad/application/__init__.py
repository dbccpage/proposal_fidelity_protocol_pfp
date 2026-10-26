"""Operad Application Layer.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .dto.operad_dto import DispatchResultDTO, ValidationReportDTO
    from .use_cases.dispatch_operation_use_case import DispatchOperationUseCase
    from .use_cases.record_trace_use_case import RecordTraceUseCase
    from .use_cases.validate_operad_use_case import ValidateOperadUseCase

__all__ = ['DispatchOperationUseCase', 'DispatchResultDTO', 'RecordTraceUseCase', 'ValidateOperadUseCase', 'ValidationReportDTO']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'DispatchResultDTO': ('.dto.operad_dto', 'DispatchResultDTO'),
    'ValidationReportDTO': ('.dto.operad_dto', 'ValidationReportDTO'),
    'DispatchOperationUseCase': ('.use_cases.dispatch_operation_use_case', 'DispatchOperationUseCase'),
    'RecordTraceUseCase': ('.use_cases.record_trace_use_case', 'RecordTraceUseCase'),
    'ValidateOperadUseCase': ('.use_cases.validate_operad_use_case', 'ValidateOperadUseCase'),
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
