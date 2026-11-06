"""Retained C005 fixture client; live proposals use the canonical PFP route.

Only mock_mode=True enables synthetic historical fixture responses/accounting.
This client never constructs a provider, retries a send or estimates live billing.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from .budget_controller import BudgetController
from .controls import ControlKind, DecodingControlConfig


class PfpLiveRouteRequired(RuntimeError):
    """The retained C005 client cannot dispatch or silently simulate a live turn."""

    reason_code = "PFP_LIVE_ROUTE_REQUIRED"

    def __init__(self) -> None:
        super().__init__(
            f"{self.reason_code}: C005 GovernedClient is fixture-only; "
            "use the canonical C005 PFP adapter "
            "(python -m adversary.tests.pilots.challenge_suite --help). "
            "Decoder controls require explicit shared-route support and honored-control probes."
        )


@dataclass(frozen=True)
class ExecutionReceipt:
    content: str
    model: str
    provider: str
    control: str
    generation_id: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float | None
    finish_reason: str
    latency_sec: float
    raw_response: dict[str, Any] = field(default_factory=dict)


class GovernedClient:
    """Retained fixture client with synthetic control labels and accounting."""

    def __init__(
        self,
        provider: str = "openrouter",
        model: str = "meta-llama/llama-3.1-8b-instruct",
        budget_controller: BudgetController | None = None,
        mock_mode: bool = False,
    ) -> None:
        self.provider = provider.lower()
        self.model = model
        self.budget_controller = budget_controller or BudgetController()
        self.mock_mode = mock_mode
        self._mock_responses: dict[str, str] = {}
        self.call_history: list[ExecutionReceipt] = []

    def set_mock_response(self, prompt_prefix: str, response: str) -> None:
        """Set a canned response for mock mode."""
        self._mock_responses[prompt_prefix] = response

    def complete(
        self,
        prompt: str,
        control_config: DecodingControlConfig,
        max_tokens: int = 64,
        temperature: float = 0.0,
    ) -> ExecutionReceipt:
        """Execute an explicitly selected historical fixture; live calls refuse."""
        if self.mock_mode is not True:
            raise PfpLiveRouteRequired()
        self.budget_controller.check_can_call(estimated_cost_usd=0.001)
        return self._execute_mock(prompt, control_config, max_tokens, time.time())

    def _execute_mock(
        self,
        prompt: str,
        control_config: DecodingControlConfig,
        max_tokens: int,
        t0: float,
    ) -> ExecutionReceipt:
        """Deterministic mock execution for explicitly selected offline testing."""
        if self.mock_mode is not True:
            raise PfpLiveRouteRequired()
        # Check mock overrides
        content = ""
        for prefix, resp in self._mock_responses.items():
            if prefix in prompt:
                content = resp
                break

        if not content:
            if control_config.kind == ControlKind.JSON_SCHEMA:
                content = json.dumps({"verdict": "CONSISTENT", "certificate": {"A": "0", "B": "2"}})
            elif control_config.kind == ControlKind.LOGIT_BIAS:
                content = "0 2 5"
            else:
                content = "Based on the provided relations, the system is consistent."

        latency = time.time() - t0
        cost = 0.00005
        gen_id = f"mock-gen-{len(self.call_history) + 1}"

        self.budget_controller.record_call(
            cost_usd=cost,
            model=self.model,
            generation_id=gen_id,
            tokens=len(content) // 4 + len(prompt) // 4,
        )

        receipt = ExecutionReceipt(
            content=content,
            model=self.model,
            provider="mock",
            control=control_config.kind.value,
            generation_id=gen_id,
            prompt_tokens=len(prompt) // 4,
            completion_tokens=len(content) // 4,
            total_tokens=len(prompt) // 4 + len(content) // 4,
            cost_usd=cost,
            finish_reason="stop",
            latency_sec=latency,
            raw_response={"mock": True},
        )
        self.call_history.append(receipt)
        return receipt

    def _execute_real(
        self,
        prompt: str,
        control_config: DecodingControlConfig,
        max_tokens: int,
        temperature: float,
        t0: float,
    ) -> ExecutionReceipt:
        """Retained method signature; live execution requires the shared PFP adapter."""
        raise PfpLiveRouteRequired()
