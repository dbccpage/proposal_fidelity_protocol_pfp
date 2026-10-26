"""Refuse CEC metrics until a concrete evaluator is configured.

No score or passing verdict can be inferred from a target identifier and
context keys. AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

from ...domain.ports.cec_bridge import ICecBridgeAdapter
from ...domain.shared_kernel.authority_effect import AuthorityEffect


class CecBridgeAdapter(ICecBridgeAdapter):
    """Unconfigured CEC port; preserve the dictionary result interface."""

    def evaluate_metric(self, target_id: str, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "target_id": target_id,
            "metric_score": None,
            "status": "REFUSED",
            "refusal_code": "CEC_EVALUATOR_UNAVAILABLE",
            "detail": "No CEC evaluator is configured; no metric was measured.",
            "context_keys": list(context.keys()),
            "authority_effect": AuthorityEffect.NONE.value,
        }
