"""Per-provider model allowlist. Fail-closed. AuthorityEffect: None."""

from __future__ import annotations

from collections.abc import Iterable

from omega_engine_woland.domain.providers.types import ModelNotAllowed, Provider


class ModelAllowlist:
    def __init__(self, entries: dict[Provider, set[str]] | None = None) -> None:
        self._entries: dict[Provider, set[str]] = {
            p: set(models) for p, models in (entries or {}).items()
        }

    @classmethod
    def empty(cls) -> ModelAllowlist:
        return cls({})

    @classmethod
    def builtin(cls) -> ModelAllowlist:
        return (
            cls.empty()
            .allow(Provider.FIXTURE, "fixture-model")
            .allow(Provider.ANTHROPIC, "claude-sonnet-4-20250514")
            .allow(Provider.OPENAI, "gpt-4o-mini")
            .allow(Provider.GROK, "grok-2-latest")
            .allow(Provider.GROQ, "llama-3.1-8b-instant")
            .allow(Provider.LOCAL, "qwen2.5:0.5b")
            .allow(Provider.OPENROUTER, "deepseek/deepseek-v4-flash")
            .allow(Provider.OPENROUTER, "google/gemini-2.5-flash")
            .allow(Provider.OPENROUTER, "openai/gpt-4o-mini")
            # Open-weight lane for challenges: at most 70B total parameters per the
            # model registry. Qwen2.5-72B and Qwen3-235B-A22B were removed as over it.
            .allow(Provider.OPENROUTER, "meta-llama/llama-3.3-70b-instruct")
            .allow(Provider.DEEPSEEK, "deepseek-v4-flash")
            # SCALE-003 S3: Gemini strong-judge / propose path
            .allow(Provider.GEMINI, "gemini-2.5-flash")
            # NVIDIA NIM API (free tier / .env integrated)
            .allow(Provider.NVIDIA, "meta/llama-3.3-70b-instruct")
            .allow(Provider.NVIDIA, "nvidia/llama-3.1-nemotron-70b-instruct")
            .allow(Provider.NVIDIA, "deepseek-ai/deepseek-r1")
        )

    def allow(self, provider: Provider, model: str) -> ModelAllowlist:
        entries = {p: set(m) for p, m in self._entries.items()}
        entries.setdefault(provider, set()).add(model)
        return ModelAllowlist(entries)

    def contains(self, provider: Provider, model: str) -> bool:
        return model in self._entries.get(provider, set())

    def check(self, provider: Provider, model: str) -> None:
        if not self.contains(provider, model):
            raise ModelNotAllowed(f"{provider.value}:{model}")

    def iter_pairs(self) -> Iterable[tuple[Provider, str]]:
        for provider in sorted(self._entries.keys(), key=lambda p: p.value):
            for model in sorted(self._entries[provider]):
                yield provider, model

    def models_for(self, provider: Provider) -> frozenset[str]:
        return frozenset(self._entries.get(provider, set()))
