"""
AST Cochain Complex & Boundary Evaluation Subsystem.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .cochain_extractor import ASTCochainExtractor
    from .cycle_analysis import CycleAnalysisLimits, DependencyAnalysisLimitError
    from .dependency_complex import DEFAULT_CLEAN_ARCH_LAYERS, ASTDependencyComplex
    from .metrics_evaluator import ASTMetricsEvaluator
    from .models import ASTDefect, ASTEvaluationReport
    from .source_parser import ASTSourceParser

__all__ = ['ASTDefect', 'CycleAnalysisLimits', 'DependencyAnalysisLimitError', 'ASTEvaluationReport', 'ASTSourceParser', 'ASTDependencyComplex', 'DEFAULT_CLEAN_ARCH_LAYERS', 'ASTMetricsEvaluator', 'ASTCochainExtractor']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ASTCochainExtractor': ('.cochain_extractor', 'ASTCochainExtractor'),
    'CycleAnalysisLimits': ('.cycle_analysis', 'CycleAnalysisLimits'),
    'DependencyAnalysisLimitError': ('.cycle_analysis', 'DependencyAnalysisLimitError'),
    'DEFAULT_CLEAN_ARCH_LAYERS': ('.dependency_complex', 'DEFAULT_CLEAN_ARCH_LAYERS'),
    'ASTDependencyComplex': ('.dependency_complex', 'ASTDependencyComplex'),
    'ASTMetricsEvaluator': ('.metrics_evaluator', 'ASTMetricsEvaluator'),
    'ASTDefect': ('.models', 'ASTDefect'),
    'ASTEvaluationReport': ('.models', 'ASTEvaluationReport'),
    'ASTSourceParser': ('.source_parser', 'ASTSourceParser'),
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
