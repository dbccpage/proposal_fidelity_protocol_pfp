"""PFP-mediated dialogue adapters; the injected provider gateway owns accounting.

Current-IDE callables receive the prepared user/system text in the legacy
cue/context slots. OpenRouter callers supply an existing accounted gateway.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional
from uuid import uuid4

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_pfp.infrastructure.task_turn import prepare_task_turn
from omega_engine_woland.domain.providers.types import CandidateRequest, Provider
from omega_engine_woland.domain.residual_algebra.dialogue_personas import PERSONA_PROMPTS
from omega_engine_woland.infrastructure.providers.gateway import (
    enclosing_accounted_gateway as _enclosing_accounted_gateway,
)

_ANSWER_SCHEMA = {"type": "string", "minLength": 1, "pattern": r"\S"}


def _dialogue_request(speaker: str, cue: str, context: str) -> CandidateRequest:
    persona = PERSONA_PROMPTS.get(
        speaker,
        f"You are {speaker}, an authentic character in a Bulgakovian mathematical-engineering drama.",
    )
    return CandidateRequest(
        system=persona + "\nDeliver a single in-character utterance (1-3 sentences) "
        "reacting to the cue, with guillemets («...»).",
        user=json.dumps({"speaker": speaker, "cue": cue, "context": context}, ensure_ascii=False),
    )


def _reply_refusal(checked: dict) -> Err:
    return Err(Refusal(
        "DIALOGUE_PFP_REPLY_INVALID", str(checked.get("reason") or checked["failure_class"]),
        __name__, (("pfp_result", json.dumps(checked, ensure_ascii=True)),),
    ))


@dataclass(frozen=True)
class CallableDialogueProvider:
    """Current-IDE `(speaker, prepared_user, prepared_system) -> raw JSON` adapter.

    The callable performs the actual IDE turn. Its exact reply and check remain
    accessible in ``last_pfp_result``; schema validity grants no task authority.
    """

    fn: Callable[[str, str, str], str]
    last_pfp_result: dict | None = field(default=None, init=False, repr=False, compare=False)

    def generate(self, speaker: str, cue: str, context: str = "") -> Result[str, Refusal]:
        object.__setattr__(self, "last_pfp_result", None)
        try:
            request = _dialogue_request(speaker, cue, context)
            prepared = prepare_task_turn(system=request.system, user=request.user,
                task_id="woland-dialogue", attempt_id=uuid4().hex, answer_schema=_ANSWER_SCHEMA)
            result = self.fn(speaker, prepared.prompt.user, prepared.prompt.system)
        except Exception as exc:
            return Err(Refusal("DIALOGUE_PROVIDER_FAILED", f"{type(exc).__name__}: {exc}", __name__))
        if not isinstance(result, str) or not result.strip():
            if isinstance(result, str):
                object.__setattr__(self, "last_pfp_result", prepared.check_completion(result))
            return Err(Refusal("DIALOGUE_REPLY_EMPTY", "Dialogue provider returned no text.", __name__))
        checked = prepared.check_completion(result)
        object.__setattr__(self, "last_pfp_result", checked)
        if not checked["schema_valid"] or checked["failure_class"] != "NONE":
            return _reply_refusal(checked)
        return Ok(checked["answer"].strip())


@dataclass(frozen=True)
class OpenRouterDialogueProvider:
    """Dialogue over an existing accounted gateway, using the shared PFP turn.

    ``api_key`` and the positional constructor remain accepted. Credentials and
    transport policy belong to ``gateway``; an API key alone cannot authorize a
    call. Pass the same budgeted provider gateway, EstimatedBudgetGateway or
    DurableRunGateway used by the enclosing Woland run. An estimated allowance
    retains its existing weaker financial guarantee.
    """

    api_key: str = ""
    model: str = "google/gemini-2.5-flash"
    timeout_seconds: float = 10.0
    gateway: Any | None = field(default=None, kw_only=True, repr=False, compare=False)
    last_pfp_result: dict | None = field(default=None, init=False, repr=False, compare=False)

    @classmethod
    def from_environment(cls, environ: Optional[Mapping[str, str]] = None, *, gateway=None
    ) -> "OpenRouterDialogueProvider | None":
        env = os.environ if environ is None else environ
        api_key = env.get("OPENROUTER_API_KEY")
        return cls(api_key=api_key, gateway=gateway) if api_key else None

    def generate(self, speaker: str, cue: str, context: str = "") -> Result[str, Refusal]:
        object.__setattr__(self, "last_pfp_result", None)
        if self.gateway is None:
            return Err(Refusal("DIALOGUE_GATEWAY_REQUIRED",
                "Bind the enclosing run's accounted gateway; an API key alone is insufficient.", __name__))
        from omega_engine_pfp.infrastructure.task_turn import complete_task_turn

        if not _enclosing_accounted_gateway(self.gateway):
            return Err(
                Refusal(
                    "DIALOGUE_ACCOUNTED_GATEWAY_REQUIRED",
                    "Use the enclosing run's existing budgeted or accounted gateway.",
                    __name__,
                )
            )
        try:
            candidate, _, checked = complete_task_turn(self.gateway,
                _dialogue_request(speaker, cue, context), task_id="woland-dialogue",
                attempt_id=uuid4().hex, provider=Provider.OPENROUTER, model=self.model,
                answer_schema=_ANSWER_SCHEMA)
            object.__setattr__(self, "last_pfp_result", checked)
            return Ok(candidate.content.strip())
        except Exception as exc:
            checked = getattr(exc, "checked", None)
            object.__setattr__(self, "last_pfp_result", checked)
            if checked is not None:
                return _reply_refusal(checked)
            return Err(Refusal("DIALOGUE_PROVIDER_FAILED", f"{type(exc).__name__}: {exc}", __name__))


@dataclass(frozen=True)
class GeminiDialogueProvider:
    """Retained constructor for the retired unaccounted native Gemini route."""

    api_key: str
    model: str = "gemini-2.5-pro"
    timeout_seconds: float = 10.0

    @classmethod
    def from_environment(cls, environ: Optional[Mapping[str, str]] = None
    ) -> "GeminiDialogueProvider | None":
        env = os.environ if environ is None else environ
        api_key = env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY")
        return cls(api_key=api_key) if api_key else None

    def generate(self, speaker: str, cue: str, context: str = "") -> Result[str, Refusal]:
        return Err(Refusal("DIALOGUE_NATIVE_GEMINI_RETIRED",
            "Use current-IDE dialogue or the OpenRouter adapter with an accounted gateway. "
            "No provider fallback was attempted.", __name__))


def resolve_dialogue_provider_from_environment(
    environ: Optional[Mapping[str, str]] = None, *, gateway=None,
) -> OpenRouterDialogueProvider | GeminiDialogueProvider | None:
    """Prefer OpenRouter; legacy Gemini selection produces an explicit refusal."""
    openrouter = OpenRouterDialogueProvider.from_environment(environ, gateway=gateway)
    return openrouter if openrouter is not None else GeminiDialogueProvider.from_environment(environ)
