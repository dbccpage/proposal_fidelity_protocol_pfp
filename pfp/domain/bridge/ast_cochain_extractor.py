"""Compatibility re-exports for AST Cochain Extractor from adversary.stage.

Imports remain available if the sister package fails, but any use refuses
with the captured dependency error instead of returning a fabricated result.
AuthorityEffect: None.
"""
from __future__ import annotations


class BridgeUnavailableError(RuntimeError):
    """The optional AST cochain bridge could not be imported."""

try:
    from ..ast_cochain.ast_cochain_extractor import (
        ASTCochainExtractor,
        ASTDefect,
        ASTEvaluationReport,
    )
    from ..ast_cochain.ast_dependency_complex import (
        DEFAULT_LAYER_RANKS as DEFAULT_CLEAN_ARCH_LAYERS,
    )
    from ..ast_cochain.ast_dependency_complex import (
        DependencyComplex as ASTDependencyComplex,
    )
    from ..ast_cochain.ast_metrics_evaluator import ASTMetricsEvaluator
    from ..ast_cochain.ast_source_parser import PythonSourceParser as ASTSourceParser
except Exception as exc:
    _unavailable_reason = f"AST cochain bridge unavailable: {type(exc).__name__}: {exc}"

    class _UnavailableComponent:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise BridgeUnavailableError(_unavailable_reason)

    class _UnavailableLayers:
        def __iter__(self):
            raise BridgeUnavailableError(_unavailable_reason)

        def __len__(self) -> int:
            raise BridgeUnavailableError(_unavailable_reason)

    ASTCochainExtractor = _UnavailableComponent  # type: ignore[misc,assignment]
    ASTDefect = _UnavailableComponent  # type: ignore[misc,assignment]
    ASTEvaluationReport = _UnavailableComponent  # type: ignore[misc,assignment]
    ASTDependencyComplex = _UnavailableComponent  # type: ignore[misc,assignment]
    DEFAULT_CLEAN_ARCH_LAYERS = _UnavailableLayers()  # type: ignore[assignment]
    ASTMetricsEvaluator = _UnavailableComponent  # type: ignore[misc,assignment]
    ASTSourceParser = _UnavailableComponent  # type: ignore[misc,assignment]

__all__ = [
    "BridgeUnavailableError",
    "ASTCochainExtractor",
    "ASTDefect",
    "ASTEvaluationReport",
    "ASTDependencyComplex",
    "DEFAULT_CLEAN_ARCH_LAYERS",
    "ASTMetricsEvaluator",
    "ASTSourceParser",
]
