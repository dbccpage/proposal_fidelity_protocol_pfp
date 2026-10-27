"""Registry of model deployments and their published parameter counts. AuthorityEffect: None.

Parameter ceilings are enforced from this table, never inferred from a model id:
an id such as ``qwen3-235b-a22b`` names active parameters, and ``8x22b`` names a
per-expert size. Each row records the publisher's nominal total size, which is
how challenges state their ceiling ("at most 70B"). Mixture-of-experts models
count total parameters, not active ones. A model whose size is undisclosed, or
whose weights are closed, cannot be admitted under a parameter ceiling.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any

from adversary.domain.providers.types import ModelNotAllowed, Provider

OPEN_WEIGHT_CEILING_PARAMETERS = 70_000_000_000
_ARCHITECTURES = ("dense", "moe", "undisclosed")
_B = 1_000_000_000


class ModelNotRegistered(ModelNotAllowed):
    """The deployment has no registry row, so its size is unknown."""

    def __init__(self, provider: Provider, model: str) -> None:
        self.code = "MODEL_NOT_REGISTERED"
        super().__init__(f"MODEL_NOT_REGISTERED:{provider.value}:{model}")


class ModelParameterCeilingRefused(ModelNotAllowed):
    """The deployment is registered but cannot be admitted under the ceiling."""

    def __init__(self, code: str, provider: Provider, model: str, detail: str) -> None:
        self.code = code
        super().__init__(f"{code}:{provider.value}:{model}:{detail}")


@dataclass(frozen=True)
class ModelSpecV1:
    """One model deployment with its published nominal total parameter count."""

    provider: Provider
    model_id: str
    total_parameters: int | None
    open_weights: bool
    architecture: str
    source: str

    def __post_init__(self) -> None:
        if type(self.provider) is not Provider:
            raise TypeError("provider must be exactly Provider")
        if type(self.model_id) is not str or not self.model_id:
            raise ValueError("model_id must be a non-empty exact string")
        if self.total_parameters is not None and (
            type(self.total_parameters) is not int or self.total_parameters <= 0
        ):
            raise ValueError("total_parameters must be a positive exact integer or None")
        if type(self.open_weights) is not bool:
            raise TypeError("open_weights must be exactly bool")
        if self.architecture not in _ARCHITECTURES:
            raise ValueError(f"architecture must be one of {_ARCHITECTURES}")
        if (self.architecture == "undisclosed") != (self.total_parameters is None):
            raise ValueError("an undisclosed architecture exactly when total_parameters is None")
        if type(self.source) is not str or not self.source:
            raise ValueError("source must be a non-empty exact string")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, ModelSpecV1):
            return False
        return (
            self.provider == other.provider
            and self.model_id == other.model_id
            and self.total_parameters == other.total_parameters
            and self.open_weights == other.open_weights
            and self.architecture == other.architecture
            and self.source == other.source
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.provider,
            self.model_id,
            self.total_parameters,
            self.open_weights,
            self.architecture,
            self.source,
        ))


def _spec(
    provider: Provider,
    model_id: str,
    total_parameters: int | None,
    *,
    open_weights: bool,
    architecture: str,
    source: str,
) -> ModelSpecV1:
    return ModelSpecV1(provider, model_id, total_parameters, open_weights, architecture, source)


class ModelRegistry:
    """Fail-closed lookup from (provider, model id) to a published size."""

    def __init__(self, specs: Iterable[ModelSpecV1] = ()) -> None:
        rows: dict[tuple[Provider, str], ModelSpecV1] = {}
        for spec in specs:
            if type(spec) is not ModelSpecV1:
                raise TypeError("registry rows must be exactly ModelSpecV1")
            key = (spec.provider, spec.model_id)
            if key in rows:
                raise ValueError(f"duplicate registry row {spec.provider.value}:{spec.model_id}")
            rows[key] = spec
        self._rows = rows

    @classmethod
    def builtin(cls) -> ModelRegistry:
        meta = "Meta model card"
        closed = "closed weights; parameter count undisclosed by the vendor"
        return cls((
            _spec(Provider.OPENROUTER, "meta-llama/llama-3.3-70b-instruct", 70 * _B, open_weights=True,
                  architecture="dense", source=f"{meta}: Llama 3.3 70B"),
            _spec(Provider.OPENROUTER, "meta-llama/llama-3.1-70b-instruct", 70 * _B, open_weights=True,
                  architecture="dense", source=f"{meta}: Llama 3.1 70B"),
            _spec(Provider.OPENROUTER, "meta-llama/llama-3.1-8b-instruct", 8 * _B, open_weights=True,
                  architecture="dense", source=f"{meta}: Llama 3.1 8B"),
            _spec(Provider.OPENROUTER, "meta-llama/llama-4-maverick-17b-128e-instruct", 400 * _B,
                  open_weights=True, architecture="moe",
                  source=f"{meta}: Llama 4 Maverick, 400B total, 17B active"),
            _spec(Provider.OPENROUTER, "qwen/qwen-2.5-7b-instruct", 7 * _B, open_weights=True,
                  architecture="dense", source="Qwen model card: Qwen2.5-7B-Instruct"),
            _spec(Provider.OPENROUTER, "qwen/qwen-2.5-coder-32b-instruct", 32 * _B, open_weights=True,
                  architecture="dense", source="Qwen model card: Qwen2.5-Coder-32B-Instruct"),
            _spec(Provider.OPENROUTER, "qwen/qwen-2.5-72b-instruct", 72 * _B, open_weights=True,
                  architecture="dense", source="Qwen model card: Qwen2.5-72B-Instruct"),
            _spec(Provider.OPENROUTER, "qwen/qwen3-30b-a3b", 30 * _B, open_weights=True,
                  architecture="moe", source="Qwen model card: Qwen3-30B-A3B, 30B total, 3B active"),
            _spec(Provider.OPENROUTER, "qwen/qwen3-235b-a22b", 235 * _B, open_weights=True,
                  architecture="moe", source="Qwen model card: Qwen3-235B-A22B, 235B total, 22B active"),
            _spec(Provider.OPENROUTER, "google/gemma-3-27b-it", 27 * _B, open_weights=True,
                  architecture="dense", source="Google model card: Gemma 3 27B"),
            _spec(Provider.OPENROUTER, "mistralai/mistral-small-24b-instruct-2501", 24 * _B,
                  open_weights=True, architecture="dense",
                  source="Mistral model card: Mistral Small 24B Instruct 2501"),
            _spec(Provider.OPENROUTER, "mistralai/mixtral-8x22b-instruct", 141 * _B, open_weights=True,
                  architecture="moe", source="Mistral model card: Mixtral 8x22B, 141B total, 39B active"),
            _spec(Provider.OPENROUTER, "deepseek/deepseek-r1-distill-llama-70b", 70 * _B,
                  open_weights=True, architecture="dense",
                  source="DeepSeek model card: DeepSeek-R1-Distill-Llama-70B"),
            _spec(Provider.OPENROUTER, "deepseek/deepseek-v4-flash", None, open_weights=False,
                  architecture="undisclosed", source="parameter count not recorded in this estate"),
            _spec(Provider.OPENROUTER, "google/gemini-2.5-flash", None, open_weights=False,
                  architecture="undisclosed", source=closed),
            _spec(Provider.OPENROUTER, "google/gemini-2.5-pro", None, open_weights=False,
                  architecture="undisclosed", source=closed),
            _spec(Provider.OPENROUTER, "openai/gpt-4o-mini", None, open_weights=False,
                  architecture="undisclosed", source=closed),
            _spec(Provider.NVIDIA, "meta/llama-3.3-70b-instruct", 70 * _B, open_weights=True,
                  architecture="dense", source=f"{meta}: Llama 3.3 70B"),
            _spec(Provider.NVIDIA, "nvidia/llama-3.1-nemotron-70b-instruct", 70 * _B, open_weights=True,
                  architecture="dense", source="NVIDIA model card: Llama-3.1-Nemotron-70B-Instruct"),
            _spec(Provider.NVIDIA, "deepseek-ai/deepseek-r1", 671 * _B, open_weights=True,
                  architecture="moe", source="DeepSeek model card: DeepSeek-R1, 671B total, 37B active"),
            _spec(Provider.GROQ, "llama-3.1-8b-instant", 8 * _B, open_weights=True,
                  architecture="dense", source=f"{meta}: Llama 3.1 8B"),
            _spec(Provider.LOCAL, "qwen2.5:0.5b", 500_000_000, open_weights=True,
                  architecture="dense", source="Qwen model card: Qwen2.5-0.5B-Instruct"),
            _spec(Provider.ANTHROPIC, "claude-sonnet-4-20250514", None, open_weights=False,
                  architecture="undisclosed", source=closed),
            _spec(Provider.OPENAI, "gpt-4o-mini", None, open_weights=False,
                  architecture="undisclosed", source=closed),
            _spec(Provider.GROK, "grok-2-latest", None, open_weights=False,
                  architecture="undisclosed", source="hosted deployment; parameter count not recorded in this estate"),
            _spec(Provider.DEEPSEEK, "deepseek-v4-flash", None, open_weights=False,
                  architecture="undisclosed", source="parameter count not recorded in this estate"),
            _spec(Provider.GEMINI, "gemini-2.5-flash", None, open_weights=False,
                  architecture="undisclosed", source=closed),
        ))

    @classmethod
    def from_dict(cls, data: list[dict[str, Any]]) -> ModelRegistry:
        specs: list[ModelSpecV1] = []
        for row in data:
            specs.append(
                ModelSpecV1(
                    provider=Provider(row["provider"]),
                    model_id=row["model_id"],
                    total_parameters=row["total_parameters"],
                    open_weights=row["open_weights"],
                    architecture=row["architecture"],
                    source=row["source"],
                )
            )
        return cls(specs)

    def __iter__(self) -> Iterator[ModelSpecV1]:
        return iter(sorted(self._rows.values(), key=lambda s: (s.provider.value, s.model_id)))

    def spec(self, provider: Provider, model: str) -> ModelSpecV1:
        spec = self._rows.get((provider, model))
        if spec is None:
            raise ModelNotRegistered(provider, model)
        return spec

    def admit_under_ceiling(
        self,
        provider: Provider,
        model: str,
        ceiling_parameters: int = OPEN_WEIGHT_CEILING_PARAMETERS,
    ) -> ModelSpecV1:
        """Return the spec when the model is open-weight and at most the ceiling; refuse otherwise."""
        if type(ceiling_parameters) is not int or ceiling_parameters <= 0:
            raise ValueError("ceiling_parameters must be a positive exact integer")
        spec = self.spec(provider, model)
        if spec.total_parameters is None:
            raise ModelParameterCeilingRefused("MODEL_SIZE_UNDISCLOSED", provider, model, spec.source)
        if spec.total_parameters > ceiling_parameters:
            raise ModelParameterCeilingRefused(
                "MODEL_OVER_PARAMETER_CEILING",
                provider,
                model,
                f"{spec.total_parameters} > {ceiling_parameters}",
            )
        if not spec.open_weights:
            raise ModelParameterCeilingRefused("MODEL_NOT_OPEN_WEIGHTS", provider, model, spec.source)
        return spec


__all__ = [
    "OPEN_WEIGHT_CEILING_PARAMETERS",
    "ModelNotRegistered",
    "ModelParameterCeilingRefused",
    "ModelRegistry",
    "ModelSpecV1",
]
