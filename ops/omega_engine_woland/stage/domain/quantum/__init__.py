"""
Quantum Density Matrix & Symmetry Breaking Engine (SBE) Subsystem.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .analyzer import SBEAnalyzer
    from .density_matrix import DensityMatrixCandidate, DensityMatrixConfig, NumericalDensityMatrix, QuantumDensityEngine
    from .density_report import SBE_DIMENSION, SBEDensityReport
    from .state_projector import TextStateProjector

__all__ = ['SBE_DIMENSION', 'SBEDensityReport', 'TextStateProjector', 'SBEAnalyzer', 'DensityMatrixCandidate', 'DensityMatrixConfig', 'NumericalDensityMatrix', 'QuantumDensityEngine']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'SBEAnalyzer': ('.analyzer', 'SBEAnalyzer'),
    'DensityMatrixCandidate': ('.density_matrix', 'DensityMatrixCandidate'),
    'DensityMatrixConfig': ('.density_matrix', 'DensityMatrixConfig'),
    'NumericalDensityMatrix': ('.density_matrix', 'NumericalDensityMatrix'),
    'QuantumDensityEngine': ('.density_matrix', 'QuantumDensityEngine'),
    'SBE_DIMENSION': ('.density_report', 'SBE_DIMENSION'),
    'SBEDensityReport': ('.density_report', 'SBEDensityReport'),
    'TextStateProjector': ('.state_projector', 'TextStateProjector'),
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
