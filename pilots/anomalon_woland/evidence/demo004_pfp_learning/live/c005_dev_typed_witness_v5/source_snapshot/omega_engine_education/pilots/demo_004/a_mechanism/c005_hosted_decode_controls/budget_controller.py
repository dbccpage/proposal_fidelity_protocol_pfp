"""
budget_controller.py — Budget enforcement controller for Challenge C005.

Enforces:
- $0.10 billed inference ceiling per arm variant (Challenge C005 spec).
- Target spend <= $0.05 per execution.
- Hard kill ceiling at $0.25 per execution.
- Fail-closed behavior on missing or unreported costs.

AuthorityEffect: None.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any


class BudgetExceededError(RuntimeError):
    """Raised when an inference call would exceed the allocated budget ceiling."""


@dataclass
class BudgetController:
    ceiling_usd: float = 0.10
    target_spend_usd: float = 0.05
    hard_kill_usd: float = 0.25
    fail_closed_on_unreported: bool = True
    total_billed_usd: float = 0.0
    call_count: int = 0
    history: list[dict[str, float | str | None]] = field(default_factory=list)
    _lock: Any = field(default_factory=threading.Lock, repr=False)

    def check_can_call(self, estimated_cost_usd: float = 0.0) -> None:
        """Pre-call guard: raises BudgetExceededError if adding estimated_cost breaches ceiling."""
        with self._lock:
            projected = self.total_billed_usd + estimated_cost_usd
            if projected > self.ceiling_usd:
                raise BudgetExceededError(
                    f"Budget ceiling breached: projected spend ${projected:.4f} > ceiling ${self.ceiling_usd:.4f}"
                )
            if projected > self.hard_kill_usd:
                raise BudgetExceededError(
                    f"Hard kill ceiling breached: projected spend ${projected:.4f} > ${self.hard_kill_usd:.4f}"
                )

    def record_call(
        self,
        cost_usd: float | None,
        model: str,
        generation_id: str = "",
        tokens: int = 0,
    ) -> None:
        """Post-call recording: updates billed spend and asserts fail-closed invariant."""
        with self._lock:
            if cost_usd is None:
                if self.fail_closed_on_unreported:
                    raise BudgetExceededError(
                        f"Unreported cost from provider for model {model} (generation_id={generation_id}). "
                        "Fail-closed invariant triggered."
                    )
                # Default conservative assumption if not failing closed
                cost_usd = 0.001

            self.total_billed_usd += cost_usd
            self.call_count += 1
            self.history.append(
                {
                    "call_index": self.call_count,
                    "model": model,
                    "generation_id": generation_id,
                    "tokens": tokens,
                    "cost_usd": cost_usd,
                    "cumulative_usd": round(self.total_billed_usd, 6),
                }
            )

            if self.total_billed_usd > self.ceiling_usd:
                raise BudgetExceededError(
                    f"Post-call budget breached: total ${self.total_billed_usd:.4f} > ceiling ${self.ceiling_usd:.4f}"
                )
