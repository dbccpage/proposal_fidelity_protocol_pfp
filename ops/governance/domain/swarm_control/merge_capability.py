"""Merge-method capability discovery (SWARM-L10). No silent method substitution."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

ALLOWED_METHODS = frozenset({"merge", "squash", "rebase"})


@dataclass(frozen=True)
class MergeCapability:
    repository: str
    allowed_methods: tuple[str, ...]
    residual: str | None = None
    observation_binding: Mapping[str, Any] = field(default_factory=dict)

    def supports(self, method: str) -> bool:
        return method in self.allowed_methods and self.residual is None

    def request(self, method: str) -> str | None:
        """Return None if allowed, else MERGE_METHOD_UNAVAILABLE residual."""
        if self.residual is not None:
            return self.residual
        if method not in ALLOWED_METHODS:
            return f"MERGE_METHOD_UNKNOWN:{method}"
        if method not in self.allowed_methods:
            return f"MERGE_METHOD_UNAVAILABLE:{method}"
        return None


def discover_merge_methods(
    repository: str,
    *,
    settings_fetch: Callable[[str], Mapping[str, Any]] | None = None,
    observation: Mapping[str, Any] | None = None,
) -> MergeCapability:
    binding = dict(observation or {})
    binding.setdefault("repository", repository)

    if settings_fetch is None:
        return MergeCapability(
            repository=repository,
            allowed_methods=(),
            residual="MERGE_CAPABILITY_UNAVAILABLE:no_adapter",
            observation_binding=binding,
        )

    try:
        settings = dict(settings_fetch(repository))
    except Exception as exc:  # noqa: BLE001
        return MergeCapability(
            repository=repository,
            allowed_methods=(),
            residual=f"MERGE_CAPABILITY_UNAVAILABLE:{type(exc).__name__}",
            observation_binding=binding,
        )

    flags = {
        "merge": bool(settings.get("allow_merge_commit", False)),
        "squash": bool(settings.get("allow_squash_merge", False)),
        "rebase": bool(settings.get("allow_rebase_merge", False)),
    }
    allowed = tuple(m for m, ok in flags.items() if ok)
    return MergeCapability(
        repository=repository,
        allowed_methods=allowed,
        residual=None,
        observation_binding=binding,
    )
