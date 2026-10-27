"""Accounted PFP model completion; the legacy machine-block seat path is retired."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from operations.domain.rop.result import Err
from pfp.domain.contracts.pfp_runtime import PfpPrompt, PfpTaskPrompt
from pfp.infrastructure.estimated_gateway import DurableRunGateway
from pfp.infrastructure.seat_transport.transport import SYMBOL_GAME_PROTOCOL_V2
from pfp.use_cases.pfp_prompt import task_input_sha256, task_turn_response_schema
from pfp.use_cases.pfp_proposal import CheckPfpTaskTurnUseCase
from adversary.domain.providers.types import (
    CandidateRequest,
    DecodingParamsV1,
    Provider,
    ProviderConfigError,
)
from adversary.infrastructure.providers.wire import decode_reply

DEFAULT_ROUTED_MODEL = "openai/gpt-4o-mini"


class LiveOpenRouterSymbolGameTransport:
    """Use an operator-composed durable gateway; never acquire credentials here."""

    protocol_id = SYMBOL_GAME_PROTOCOL_V2

    def __init__(self, *, gateway=None, model: str | None = None,
                 api_key: str | None = None, max_tokens: int | None = None,
                 timeout: float = 45.0) -> None:
        if not isinstance(gateway, DurableRunGateway):
            raise ValueError("ACCOUNTED_PFP_GATEWAY_REQUIRED")
        if api_key is not None:
            raise ValueError("CREDENTIALS_BELONG_TO_ACCOUNTED_GATEWAY")
        self.gateway = gateway
        self.model = model or getattr(gateway, "model", gateway.gateway.default_model)
        actual_limit = getattr(gateway, "max_output_tokens", None)
        if actual_limit is None:
            actual_limit = gateway.gateway.policy.max_output_tokens
        if max_tokens is not None and max_tokens != actual_limit:
            raise ValueError("OUTPUT_LIMIT_BINDING_MISMATCH")
        self.max_tokens = actual_limit
        self.timeout = timeout

    def __call__(self, request):
        raise ValueError("LEGACY_SEAT_TRANSPORT_RETIRED: use the plan-consuming PFP executor")

    def complete(self, system_prompt: str, user_prompt: str, *, model: str | None = None):
        """Return the actual completion without wrapping or repairing its envelope."""
        public = decode_reply(user_prompt.encode("utf-8"))
        if not isinstance(public, dict) or any(type(public.get(key)) is not str or not public[key]
                for key in ("task_id", "attempt_id", "input_sha256")):
            raise ValueError("PFP_TASK_INPUT_REQUIRED")
        task = PfpTaskPrompt(public["task_id"], public.get("objective"),
            public.get("input"), public.get("answer_schema"))
        schema = task_turn_response_schema(task, public["attempt_id"])
        if task_input_sha256(task) != public["input_sha256"]:
            raise ValueError("PFP_TASK_INPUT_BINDING_MISMATCH")
        request = CandidateRequest(system_prompt, user_prompt,
            decoding=DecodingParamsV1(thinking=None, allow_fallbacks=False))
        action_id = "critique:" + sha256((public["task_id"] + "\0" + public["attempt_id"]).encode()).hexdigest()
        bound = self.gateway.for_action(action_id)
        result = bound.complete_result(request, provider=Provider.OPENROUTER, model=model or self.model)
        if isinstance(result, Err) and result.error.code == "PFP_ACTION_ALREADY_CLAIMED":
            result = bound.recover_result(request, provider=Provider.OPENROUTER, model=model or self.model)
        if isinstance(result, Err):
            raise ProviderConfigError(result.error.code)
        outcome = result.value
        decoded = decode_reply(outcome.reply_bytes)
        # The Providers parser validates this wire. Reading content here preserves
        # whitespace as supplied, rather than its compatibility parser's strip().
        text = decoded["choices"][0]["message"]["content"]
        response = outcome.candidate
        accountable = outcome.state in {"CompletedSettled", "CompletedPendingSettlement"}
        checked = CheckPfpTaskTurnUseCase().execute(task,
            PfpPrompt(system_prompt, user_prompt, schema), text.encode("utf-8", errors="surrogatepass"))
        return ModelCompletionOutcomeV1(content=text, input_tokens=response.input_tokens,
            output_tokens=response.output_tokens, cost_usd=response.cost_usd if accountable else None,
            model=response.model, raw_reply_bytes=outcome.reply_bytes,
            accounting_state=outcome.state, reported_cost_usd=response.cost_usd, pfp=checked)


@dataclass(frozen=True)
class ModelCompletionOutcomeV1:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    model: str = DEFAULT_ROUTED_MODEL
    raw_reply_bytes: bytes = b""
    accounting_state: str = "unaccounted"
    reported_cost_usd: float | None = None
    pfp: dict | None = None


def default_pfp_model_port(model: str | None = None, api_key: str | None = None, *, gateway=None):
    return LiveOpenRouterSymbolGameTransport(model=model, api_key=api_key, gateway=gateway)


def default_pfp_seat_transport(model: str = DEFAULT_ROUTED_MODEL, api_key: str | None = None, **options):
    raise ValueError("LEGACY_SEAT_TRANSPORT_RETIRED: use the plan-consuming PFP executor")


__all__ = ["DEFAULT_ROUTED_MODEL", "LiveOpenRouterSymbolGameTransport", "ModelCompletionOutcomeV1",
    "default_pfp_model_port", "default_pfp_seat_transport"]
