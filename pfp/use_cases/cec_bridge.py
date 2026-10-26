"""Continuous Evaluation Criterion (CEC) Bridge Use Cases."""

from __future__ import annotations

from typing import Any

from ..domain import AuthorityEffect
from ..domain.ports import ICecBridgeAdapter


class EvaluateCecMetricUseCase:
    """Evaluates task execution against continuous evaluation criterion."""

    def __init__(self, adapter: ICecBridgeAdapter | None = None) -> None:
        self._adapter = adapter

    def execute(self, target_id: str, context: dict[str, Any]) -> dict[str, Any]:
        if self._adapter is not None:
            return self._adapter.evaluate_metric(target_id, context)
        # No evaluator is configured; no metric was measured.
        return {
            "target_id": target_id,
            "metric_score": None,
            "passed": False,
            "status": "REFUSED",
            "refusal_code": "CEC_EVALUATOR_UNAVAILABLE",
            "authority_effect": AuthorityEffect.NONE.value,
        }
