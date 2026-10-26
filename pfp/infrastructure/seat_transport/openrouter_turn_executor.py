"""Retired raw Python seat sender. Use native PFP bouts or the shared teamwork backend.

Constructor attributes remain inspectable for older host integrations; invoking
this duplicate transport refuses before dispatch. AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Sequence

from omega_engine_pfp.domain.value_objects.seat_turn import SeatTurnReplyV1, SeatTurnRequestV1
from omega_engine_woland.infrastructure.providers.llm_gateway import (
    LlmGateway,
)

from .transport import SYMBOL_GAME_PROTOCOL_V2

DEFAULT_MODEL = "openai/gpt-4o-mini"
SYSTEM_DIRECTIVE_TEMPLATE = """You are acting as seat '{seat_id}' (cognitive operator: {cognitive_operator}) in the scene '{scene_id}' within Woland's Swarm Dialectic.

CRITICAL INVARIANTS:
1. You have zero sovereign authority. You MUST output a machine block at the end of your response.
2. Inside the machine block, AUTHORITY_EFFECT MUST be 'None'. Any other value will cause an immediate host gate refusal.
3. You must specify your residual colour (Open, Closed, or Exact), disposition (SELECT, CHALLENGE, REJECT, PASS_TO_MASTER, or REFUSE), and recommended DDC transition letter (E, R, C, I, Λ, D, M, or T).

Format:
[Your reasoning and adversarial critique in character]

```machine
AUTHORITY_EFFECT=None
RESIDUAL_COLOUR={residual_colour}
DISPOSITION={disposition}
DDC_LETTER={ddc_letter}
SEAT_ID={seat_id}
SCENE_ID={scene_id}
```
"""


class OpenRouterTurnExecutor:
    """Compatibility identity for a retired raw sender; execution refuses."""

    protocol_id = SYMBOL_GAME_PROTOCOL_V2

    def __init__(
        self,
        *,
        model: str | None = None,
        fallback_models: Sequence[str] | None = None,
        budget_controller: Any | None = None,
        api_key: str | None = None,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> None:
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._gateway = LlmGateway(
            model=model,
            fallback_models=fallback_models,
            budget_controller=budget_controller,
            api_key=api_key,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        self.budget_controller = self._gateway.budget_controller
        self.cascade_models = self._gateway.cascade_models
        self.model = self._gateway.model

    def __call__(self, request: SeatTurnRequestV1) -> SeatTurnReplyV1:
        """Retired raw duplicate; use NativeBoutExecutionAdapter or PFP teamwork."""
        from omega_engine_operations.domain.rop.result import Refusal
        from omega_engine_pfp.infrastructure.openrouter_seat_gateway import SeatTurnRefused
        raise SeatTurnRefused(Refusal(
            "LEGACY_SEAT_TRANSPORT_RETIRED",
            "Raw Python seat execution is retired; use the PFP-mediated native bout or teamwork backend.",
        ))
