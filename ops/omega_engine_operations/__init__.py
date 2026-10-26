"""Operations package with lazy domain compatibility exports."""
from __future__ import annotations
import importlib
import sys
from typing import Any

_this_module = sys.modules[__name__]
for _identity in ("omega_engine_operations", "omega_engine.omega_engine_operations"):
    _existing = sys.modules.get(_identity)
    if _existing is not None and _existing is not _this_module and getattr(_existing,"__file__",None) != __file__:
        raise ImportError(f"conflicting public module identity: {_identity}")
    sys.modules[_identity] = _this_module
_parent = sys.modules.get("omega_engine")
if _parent is not None:
    setattr(_parent, "omega_engine_operations", _this_module)

__all__ = ('AdvisoryFindingV1', 'AntipatternFinding', 'ArchitectureConfig', 'CandidateManifestEntryV1', 'CandidateManifestV1', 'CanonicalCandidateManifestV1', 'EvaluatorAnchorV1', 'FindingSeverity', 'GATE_CATALOG_V3', 'GateDisposition', 'GateEvaluationV1', 'GateId', 'GateResult', 'GateRouteV1', 'GateSpec', 'GateStatus', 'ImportedSymbol', 'LocalCiExecutionReceiptV3', 'LocalCiInvocationV1', 'LocalCiReceiptError', 'LocalCiReceiptErrorCode', 'LocalCiVerdict', 'LocalCiVerificationInputsV1', 'ModuleInfo', 'OearsJobStoreProtocol', 'RuleCategory', 'ScanResult', 'active_gate_specs', 'load_gate_catalog_yaml')


_CATALOG_BOUND_NAMES = frozenset({
    "GATE_CATALOG_V3",
    "active_gate_specs",
    "load_gate_catalog_yaml",
})


def __getattr__(name: str) -> Any:
    if name in __all__:
        if name in _CATALOG_BOUND_NAMES:
            from omega_engine_operations.infrastructure.cicd.gate_catalog_loader import (
                ensure_gate_catalog,
            )

            ensure_gate_catalog()
        value = getattr(importlib.import_module(".domain", __name__), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
