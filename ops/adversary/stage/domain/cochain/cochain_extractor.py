"""
cochain_extractor.py
====================

Top-level AST Cochain Extractor and PR Unified Diff Auditor.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Dict, Optional

from .cycle_analysis import CycleAnalysisLimits, _validated_limits
from .metrics_evaluator import ASTMetricsEvaluator
from .models import ASTEvaluationReport


class ASTCochainExtractor:
    """High-level facade extracting 1-cochains and scoring obstruction metrics over source trees."""

    def __init__(
        self, layer_rules: Optional[Dict[str, int]] = None, *, limits: CycleAnalysisLimits | None = None
    ):
        self.evaluator = ASTMetricsEvaluator(layer_rules=layer_rules, limits=_validated_limits(limits))

    def score_source_tree(self, sources: Dict[str, str]) -> ASTEvaluationReport:
        return self.evaluator.evaluate_sources(sources)

    def audit_pr_diff(
        self,
        diff_text: str,
        base_sources: Optional[Dict[str, str]] = None,
    ) -> ASTEvaluationReport:
        sources = base_sources if base_sources is not None else {}
        limits = _validated_limits(self.evaluator.complex.limits)
        limits.admit_sources(sources)
        limits.check("max_total_source_chars", len(diff_text))
        sources = dict(sources)
        diff_sources = self._apply_diff_to_sources(diff_text, sources)
        return self.evaluator.evaluate_sources(diff_sources)

    def _apply_diff_to_sources(self, diff_text: str, sources: Dict[str, str]) -> Dict[str, str]:
        result = dict(sources)
        current_file = None
        new_lines = []

        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                if current_file and new_lines:
                    mod_name = self._path_to_mod(current_file)
                    result[mod_name] = "\n".join(new_lines)
                current_file = line[6:].strip()
                new_lines = []
            elif line.startswith("+") and not line.startswith("+++"):
                new_lines.append(line[1:])
            elif line.startswith(" ") and not line.startswith("@@"):
                new_lines.append(line[1:])
            elif not line.startswith("-") and not line.startswith("@@") and not line.startswith("---") and not line.startswith("+++"):
                new_lines.append(line)

        if current_file and new_lines:
            mod_name = self._path_to_mod(current_file)
            result[mod_name] = "\n".join(new_lines)

        return result

    @staticmethod
    def _path_to_mod(path_str: str) -> str:
        clean = path_str.replace("/", ".").replace("\\", ".")
        if clean.endswith(".py"):
            clean = clean[:-3]
        return clean
