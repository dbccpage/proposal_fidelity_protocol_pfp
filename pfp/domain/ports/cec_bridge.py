"""CEC Bridge Port Protocol."""

from __future__ import annotations

from typing import Any, Protocol


class ICecBridgeAdapter(Protocol):
    """Protocol for Continuous Evaluation Criterion (CEC) bridge operations."""

    def evaluate_metric(self, target_id: str, context: dict[str, Any]) -> dict[str, Any]:
        ...
