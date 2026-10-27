"""Structural transport port for prompt-cochain evaluation. AuthorityEffect: None."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from operations.domain.rop.result import Refusal, Result


class PromptCochainHost(Protocol):
    """Forward exact wire values and retain the complete railway outcome."""

    def evaluate_prompt_cochain(
        self,
        *,
        complex: Mapping[str, Any],
        cochain: Sequence[Any],
        primal_potential: Sequence[Any] | None = None,
        dual_witness: Sequence[Any] | None = None,
        triad_context: Mapping[str, Any] | None = None,
    ) -> Result[Mapping[str, Any], Refusal]: ...
