"""
client.py — Governed inference client and provider wrapper for Challenge C005.

Supports:
- Hosted open-weights models (Llama-3.1-8B, Qwen2.5-7B)
- Frontier >70B models (Llama-3.1-405B, Qwen2.5-72B, Claude 3.5 Sonnet, Gemini 1.5 Pro)
- Governed routing parameters: allow_fallbacks=False, require_parameters=True
- Budget enforcement and structured call receipts
- Offline deterministic mock for offline test verification

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

from .budget_controller import BudgetController
from .controls import ControlKind, DecodingControlConfig


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
    """Governed client executing completions under decoding controls and budget ceilings."""

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
        """Execute one completion under the configured control."""
        # 1. Budget pre-check
        self.budget_controller.check_can_call(estimated_cost_usd=0.001)

        t0 = time.time()

        if self.mock_mode or not os.getenv("OPENROUTER_API_KEY"):
            return self._execute_mock(prompt, control_config, max_tokens, t0)

        # 2. Real API Execution via OpenRouter / OpenAI client
        return self._execute_real(prompt, control_config, max_tokens, temperature, t0)

    def _execute_mock(
        self,
        prompt: str,
        control_config: DecodingControlConfig,
        max_tokens: int,
        t0: float,
    ) -> ExecutionReceipt:
        """Deterministic mock execution for offline testing."""
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
        """Live OpenRouter / OpenAI client execution."""
        from openai import OpenAI

        api_key = os.getenv("OPENROUTER_API_KEY", "")
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            timeout=60.0,
            max_retries=1,
        )

        body: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            # Governed routing parameters: no unannounced fallbacks, require specified params
            "extra_body": {
                "provider": {
                    "allow_fallbacks": False,
                    "require_parameters": True,
                }
            },
        }

        # Inject decoding control parameters
        if control_config.kind == ControlKind.LOGIT_BIAS:
            body["logit_bias"] = control_config.parameters.get("logit_bias", {})
        elif control_config.kind == ControlKind.JSON_SCHEMA:
            body["response_format"] = control_config.parameters.get("response_format", {})
        elif control_config.kind == ControlKind.GBNF:
            # OpenRouter passes grammar via extra_body or plugins if route supports it
            body["extra_body"]["grammar"] = control_config.parameters.get("grammar", "")

        resp = client.chat.completions.create(**body)
        latency = time.time() - t0

        choice = resp.choices[0]
        content = choice.message.content or ""
        finish_reason = getattr(choice, "finish_reason", "unknown") or "unknown"
        gen_id = getattr(resp, "id", f"gen-{int(t0)}")

        usage = getattr(resp, "usage", None)
        p_tok = getattr(usage, "prompt_tokens", 0) if usage else 0
        c_tok = getattr(usage, "completion_tokens", 0) if usage else 0
        t_tok = getattr(usage, "total_tokens", 0) if usage else 0

        # Attempt to read billed cost from provider usage
        cost_usd: float | None = None
        if usage and hasattr(usage, "cost"):
            cost_usd = float(usage.cost)
        elif hasattr(resp, "cost"):
            cost_usd = float(resp.cost)
        else:
            # Conservative estimation if not directly in fields
            cost_usd = 0.0001

        self.budget_controller.record_call(
            cost_usd=cost_usd,
            model=self.model,
            generation_id=gen_id,
            tokens=t_tok,
        )

        receipt = ExecutionReceipt(
            content=content,
            model=self.model,
            provider=self.provider,
            control=control_config.kind.value,
            generation_id=gen_id,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            total_tokens=t_tok,
            cost_usd=cost_usd,
            finish_reason=finish_reason,
            latency_sec=latency,
            raw_response=resp.model_dump() if hasattr(resp, "model_dump") else {},
        )
        self.call_history.append(receipt)
        return receipt
