"""AST cochain domain package.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .ast_cochain_extractor import ASTCochainExtractor
    from .ast_dependency_complex import DEFAULT_LAYER_RANKS, DependencyComplex, DependencyComplexBuilder
    from .ast_metrics_evaluator import ASTMetricsEvaluator, gamma2, solve_phi, verify_exactness
    from .ast_models import ASTDefect, ASTEvaluationReport
    from .ast_source_parser import ParsedSourceTree, PythonSourceParser
    from .models import AstCochainReceipt, DependencyEdge, LggrVerdict

__all__ = ['ASTCochainExtractor', 'ASTDefect', 'ASTEvaluationReport', 'ASTMetricsEvaluator', 'AstCochainReceipt', 'DEFAULT_LAYER_RANKS', 'DependencyComplex', 'DependencyComplexBuilder', 'DependencyEdge', 'LggrVerdict', 'ParsedSourceTree', 'PythonSourceParser', 'gamma2', 'solve_phi', 'verify_exactness']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ASTCochainExtractor': ('.ast_cochain_extractor', 'ASTCochainExtractor'),
    'DEFAULT_LAYER_RANKS': ('.ast_dependency_complex', 'DEFAULT_LAYER_RANKS'),
    'DependencyComplex': ('.ast_dependency_complex', 'DependencyComplex'),
    'DependencyComplexBuilder': ('.ast_dependency_complex', 'DependencyComplexBuilder'),
    'ASTMetricsEvaluator': ('.ast_metrics_evaluator', 'ASTMetricsEvaluator'),
    'gamma2': ('.ast_metrics_evaluator', 'gamma2'),
    'solve_phi': ('.ast_metrics_evaluator', 'solve_phi'),
    'verify_exactness': ('.ast_metrics_evaluator', 'verify_exactness'),
    'ASTDefect': ('.ast_models', 'ASTDefect'),
    'ASTEvaluationReport': ('.ast_models', 'ASTEvaluationReport'),
    'ParsedSourceTree': ('.ast_source_parser', 'ParsedSourceTree'),
    'PythonSourceParser': ('.ast_source_parser', 'PythonSourceParser'),
    'AstCochainReceipt': ('.models', 'AstCochainReceipt'),
    'DependencyEdge': ('.models', 'DependencyEdge'),
    'LggrVerdict': ('.models', 'LggrVerdict'),
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
