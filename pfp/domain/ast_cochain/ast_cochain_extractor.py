"""Bounded AST dependency-cochain extraction.

AuthorityEffect: None.
"""
from __future__ import annotations

from typing import Dict, Optional, Sequence

from .ast_dependency_complex import DEFAULT_LAYER_RANKS, DependencyComplexBuilder
from .ast_metrics_evaluator import ASTMetricsEvaluator
from .ast_models import ASTDefect, ASTEvaluationReport
from .ast_source_parser import PythonSourceParser


class ASTCochainExtractor:
    """Application facade: parse -> build dependency complex -> evaluate."""

    LAYER_RANKS = DEFAULT_LAYER_RANKS

    def __init__(self, layer_rules: Optional[Dict[str, int]] = None):
        self.layer_ranks = layer_rules or self.LAYER_RANKS
        self._parser = PythonSourceParser()
        self._builder = DependencyComplexBuilder(self.layer_ranks)
        self._evaluator = ASTMetricsEvaluator()

    def extract_from_source_dict(self, sources: Dict[str, str]) -> ASTEvaluationReport:
        if not sources:
            return self._evaluator.empty_report()
        parsed = self._parser.parse(sources)
        complex_ = self._builder.build(parsed)
        return self._evaluator.evaluate(complex_)

    def _get_module_layer(self, module_name: str) -> Optional[int]:
        return self._builder.module_layer(module_name)

    def _resolve_target_module(self, target_import: str, known_modules: Sequence[str]) -> Optional[str]:
        return self._builder.resolve_target_module(target_import, known_modules)


__all__ = ["ASTDefect", "ASTEvaluationReport", "ASTCochainExtractor"]
