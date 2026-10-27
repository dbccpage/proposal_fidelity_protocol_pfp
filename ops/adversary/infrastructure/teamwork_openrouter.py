"""OpenRouter provider template for the remote teamwork executor.

The run-wide ceiling is at most $0.05. Estimated admission is conservative
accounting, not a vendor bill. A requested hard ceiling retains the
gateway's pre-dispatch refusal when the transport cannot enforce it.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from pfp.infrastructure.estimated_gateway import create_accounted_openrouter_gateway
from adversary.domain.providers.types import DecodingParamsV1, Provider

from .teamwork_remote import (
    RemoteProviderTemplate,
    RemoteTeamworkExecutor,
    build_remote_executor,
    compact_profile,
    strict_schema,
)


OPENROUTER_PRESET_MODEL_MAP = {
    "anthropic/claude-3.7-sonnet:thinking": "anthropic/claude-opus-5.5",
    "anthropic/claude-3.7-sonnet": "anthropic/claude-sonnet-5.5",
    "anthropic/claude-3.5-sonnet": "anthropic/claude-sonnet-5.5",
    "anthropic/claude-3.5-haiku": "anthropic/claude-haiku-5.5",
    "openai/o3-mini": "openai/gpt-5.4-mini",
    "openai/gpt-4o": "openai/gpt-4o",
    "openai/gpt-4o-mini": "openai/gpt-4o-mini",
    "deepseek/deepseek-r1": "deepseek/deepseek-v3.2",
    "google/gemini-2.5-flash": "google/gemini-2.5-flash",
    "google/gemini-2.5-flash-lite": "google/gemini-2.5-flash",
}


@dataclass(frozen=True)
class OpenRouterTemplate(RemoteProviderTemplate):
    name: str = "openrouter"
    provider: Provider = Provider.OPENROUTER
    budget_schemas: frozenset = frozenset({"pfp.fuzzy-run.v1", "pfp.hard-run.v1"})
    ceiling_microusd: int = 50_000
    ceiling_label: str = "$0.05"

    def resolve_model(self, model: str, *, preset: str | None = None) -> str:
        return OPENROUTER_PRESET_MODEL_MAP.get(model, model) if preset is not None else model

    def decoding(self, action, turn, *, effort=None):
        if effort is not None:
            raise ValueError("EFFORT_UNSUPPORTED: the OpenRouter template has no effort control")
        compact = compact_profile(action)
        if compact and getattr(action, "assigned_model", ""):
            return DecodingParamsV1(
                allow_fallbacks=False,
                require_parameters=False,
                response_format=strict_schema(turn),
            )
        return DecodingParamsV1(
            temperature=0.0 if compact else None,
            thinking="disabled" if compact else None,
            allow_fallbacks=False,
            response_format=strict_schema(turn) if compact else None,
        )

    def gateway(self, model, max_output_tokens, **options):
        if options.pop("pricing_snapshot", None) is not None:
            raise ValueError("PRICING_SNAPSHOT_UNSUPPORTED: OpenRouter uses its builtin price table")
        return create_accounted_openrouter_gateway(model, max_output_tokens, **options)


@dataclass
class OpenRouterTeamworkExecutor(RemoteTeamworkExecutor):
    template: ClassVar[RemoteProviderTemplate] = OpenRouterTemplate()


def create_openrouter_executor(model: str, max_output_tokens: int, **options) -> OpenRouterTeamworkExecutor:
    """Require a run-wide policy of at most $0.05 before constructing transport."""
    return build_remote_executor(OpenRouterTeamworkExecutor, model, max_output_tokens, **options)
