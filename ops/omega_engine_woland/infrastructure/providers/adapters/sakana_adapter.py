"""sakana_adapter.py — OpenRouter & Sakana AI provider adapter for `sakana/fugu-ultra-v2`.

AuthorityEffect: None.

Provides a model-agnostic completion backend connecting to OpenRouter for the
Sakana AI model `sakana/fugu-ultra-v2` (console: https://console.sakana.ai/).
Live OpenRouter requires an injected accounted PFP gateway. Direct Sakana live
execution is unsupported; explicit dry runs need no credentials or transport.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Sequence, runtime_checkable

# Allow standalone execution when invoked directly outside package context
_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from omega_engine_woland.infrastructure.providers.openai_compat import OPENROUTER_BASE_URL  # noqa: E402

try:
    from omega_engine_woland.infrastructure.providers.adapters.model_backends import (
        Backend,  # noqa: E402
    )
except ImportError:
    @runtime_checkable
    class Backend(Protocol):  # type: ignore[no-redef]
        name: str

        def complete(self, prompt: str) -> str: ...

DEFAULT_SAKANA_MODEL = "sakana/fugu-ultra-v2"
DEFAULT_SAKANA_MAX_TOKENS = 65536
SAKANA_DIRECT_BASE_URL = "https://api.sakana.ai/v1"
SAKANA_CONSOLE_URL = "https://console.sakana.ai/"

__all__ = [
    "DEFAULT_SAKANA_MODEL",
    "DEFAULT_SAKANA_MAX_TOKENS",
    "OPENROUTER_BASE_URL",
    "SAKANA_CONSOLE_URL",
    "SAKANA_DIRECT_BASE_URL",
    "ConfigurationRefusal",
    "SakanaOpenRouterAdapter",
    "SakanaReceipt",
    "ask_sakana",
]


class ConfigurationRefusal(RuntimeError):
    """Raised when required API credentials or provider configurations are missing."""


@dataclass(frozen=True)
class SakanaReceipt:
    """Detailed receipt for a single model completion."""

    content: str
    model: str
    generation_id: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float | None
    latency_ms: float
    raw_usage: dict[str, object] = field(default_factory=dict)


class SakanaOpenRouterAdapter(Backend):
    """Adapter for `sakana/fugu-ultra-v2` via an accounted OpenRouter PFP gateway.

    Direct live execution is retired; its explicit dry configuration remains.
    Implements the `Backend` protocol (`name`, `complete(prompt)`).
    """

    def __init__(
        self,
        model: str = DEFAULT_SAKANA_MODEL,
        api_key: str | None = None,
        base_url: str = OPENROUTER_BASE_URL,
        direct_sakana: bool = False,
        timeout: float = 600.0,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        dry_run: bool = False,
        *,
        gateway=None,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.dry_run = dry_run
        self.direct_sakana = direct_sakana

        if direct_sakana:
            self.base_url = SAKANA_DIRECT_BASE_URL.rstrip("/")
        else:
            self.base_url = base_url.rstrip("/")

        if not self.dry_run and direct_sakana:
            raise ConfigurationRefusal("DIRECT_SAKANA_LIVE_UNSUPPORTED: use an accounted OpenRouter PFP gateway")
        if not self.dry_run and self.base_url != OPENROUTER_BASE_URL:
            raise ConfigurationRefusal("CUSTOM_SAKANA_ENDPOINT_UNSUPPORTED: use an accounted OpenRouter PFP gateway")
        self.api_key = "dry-run-key" if self.dry_run else api_key

        target_slug = "direct-sakana" if direct_sakana else "openrouter"
        self.name = f"{target_slug}:{self.model}"
        self.call_history: list[SakanaReceipt] = []
        self.last_turn: dict | None = None
        self.turn_history: list[dict] = []
        self.last_receipt: SakanaReceipt | None = None
        self._backend = None
        if not self.dry_run:
            from omega_engine_pfp.infrastructure.pilot_matrix import _output_bound
            from omega_engine_woland.infrastructure.providers.adapters.model_backends import (
                OpenRouterBackend,
            )
            self._backend = OpenRouterBackend(model=model,
                max_tokens=max_tokens if max_tokens is not None else DEFAULT_SAKANA_MAX_TOKENS,
                api_key=api_key, gateway=gateway, temperature=temperature)
            if max_tokens is None and gateway is not None:
                self._backend.max_tokens = _output_bound(gateway)

    def complete(self, prompt: str) -> str:
        """Complete a single text prompt and return assistant response content."""
        receipt = self.complete_with_receipt(prompt)
        return receipt.content

    def complete_chat(self, messages: Sequence[dict[str, str]]) -> str:
        """Complete a chat conversation messages list and return response content."""
        receipt = self.complete_with_receipt(messages)
        return receipt.content

    def complete_with_receipt(
        self,
        prompt_or_messages: str | Sequence[dict[str, str]],
        *,
        prefer_openai_sdk: bool = True,
    ) -> SakanaReceipt:
        """Send completion request and return receipt with token and cost metadata."""
        if isinstance(prompt_or_messages, str):
            messages = [{"role": "user", "content": prompt_or_messages}]
        else:
            messages = list(prompt_or_messages)

        start_time = time.monotonic()

        if self.dry_run:
            latency_ms = (time.monotonic() - start_time) * 1000.0
            mock_content = f"[DRY-RUN:{self.model}] Simulated response to: {messages[-1]['content'][:50]}"
            receipt = SakanaReceipt(
                content=mock_content,
                model=self.model,
                generation_id=f"dry-run-{len(self.call_history) + 1}",
                prompt_tokens=len(messages[-1]["content"]) // 4,
                completion_tokens=len(mock_content) // 4,
                total_tokens=(len(messages[-1]["content"]) + len(mock_content)) // 4,
                cost_usd=0.0,
                latency_ms=latency_ms,
                raw_usage={"dry_run": True},
            )
            self.call_history.append(receipt)
            self.last_receipt = receipt
            return receipt

        # Kept as a call-site compatibility option; both values use the one
        # bounded byte transport, with no SDK retries or secondary sender.
        before = len(self._backend.call_history)
        try:
            self._backend.complete_with_receipt(messages)
        finally:
            self.last_turn = self._backend.last_turn
            self.turn_history = self._backend.turn_history
            for response in self._backend.call_history[before:]:
                receipt = SakanaReceipt(content=response.content, model=response.model,
                    generation_id=response.generation_id, prompt_tokens=response.prompt_tokens,
                    completion_tokens=response.completion_tokens, total_tokens=response.total_tokens,
                    cost_usd=response.cost_usd, latency_ms=(time.monotonic() - start_time) * 1000,
                    raw_usage=dict(response.raw_usage))
                self.call_history.append(receipt)
                self.last_receipt = receipt
        return self.last_receipt


    @property
    def total_tokens(self) -> int:
        """Summed token count across all completions executed in this session."""
        return sum(r.total_tokens for r in self.call_history)

    @property
    def total_cost_usd(self) -> float | None:
        """Summed reported USD cost, or None if any call lacked cost reporting."""
        if self._backend is not None:
            return self._backend.total_cost_usd
        if any(r.cost_usd is None for r in self.call_history):
            return None
        return sum(r.cost_usd for r in self.call_history if r.cost_usd is not None)


def ask_sakana(
    prompt: str,
    *,
    model: str = DEFAULT_SAKANA_MODEL,
    api_key: str | None = None,
    direct_sakana: bool = False,
    max_tokens: int = 2048,
    temperature: float = 0.7,
    dry_run: bool = False,
    gateway=None,
) -> str:
    """Convenience helper using an injected accounted gateway or explicit dry mode."""
    adapter = SakanaOpenRouterAdapter(
        model=model,
        api_key=api_key,
        direct_sakana=direct_sakana,
        max_tokens=max_tokens,
        temperature=temperature,
        dry_run=dry_run,
        gateway=gateway,
    )
    return adapter.complete(prompt)



def main() -> int:
    """CLI entrypoint for interactive or one-shot testing of the Sakana adapter."""
    parser = argparse.ArgumentParser(
        description="Adapter for Sakana AI models (default: sakana/fugu-ultra-v2) via OpenRouter"
    )
    parser.add_argument("prompt", nargs="?", default=None, help="Prompt text to send")
    parser.add_argument(
        "--model",
        default=DEFAULT_SAKANA_MODEL,
        help=f"Model identifier (default: {DEFAULT_SAKANA_MODEL})",
    )
    parser.add_argument("--api-key", default=None,
        help="Legacy compatibility only; key alone cannot enable live chat. Use Python gateway API or Woland teamwork.")
    parser.add_argument(
        "--direct-sakana",
        action="store_true",
        help="Retired for live execution; allowed only with --dry-run",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate completion offline without dispatching network calls",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=2048,
        help="Maximum generation tokens (default: 2048)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Print structured receipt JSON instead of just content",
    )

    args = parser.parse_args()

    prompt = args.prompt
    if not prompt:
        if sys.stdin.isatty():
            prompt = "Explain in one sentence what makes the Fugu architecture unique."
        else:
            prompt = sys.stdin.read().strip()

    try:
        adapter = SakanaOpenRouterAdapter(
            model=args.model,
            api_key=args.api_key,
            direct_sakana=args.direct_sakana,
            max_tokens=args.max_tokens,
            dry_run=args.dry_run,
        )
        receipt = adapter.complete_with_receipt(prompt)
    except ConfigurationRefusal as exc:
        sys.stderr.write(f"Refusal: {exc}\n")
        return 1
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2

    if args.json_output:
        print(
            json.dumps(
                {
                    "content": receipt.content,
                    "model": receipt.model,
                    "generation_id": receipt.generation_id,
                    "prompt_tokens": receipt.prompt_tokens,
                    "completion_tokens": receipt.completion_tokens,
                    "total_tokens": receipt.total_tokens,
                    "cost_usd": receipt.cost_usd,
                    "latency_ms": round(receipt.latency_ms, 2),
                },
                indent=2,
            )
        )
    else:
        print(receipt.content)

    return 0


if __name__ == "__main__":
    sys.exit(main())
