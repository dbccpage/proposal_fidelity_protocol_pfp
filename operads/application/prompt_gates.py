"""Select OEEIS-admitted guidance before evaluating pure OEWAS prompt gates."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from omega_engine_epistemic_immune_system.use_cases.admitted_antibody_query import (
    admitted_antibodies,
)
from omega_engine_operads.domain.prompt_hierarchy.evaluator import (
    evaluate_prompt_gates as evaluate_bound_prompt_gates,
)
from omega_engine_operads.domain.prompt_hierarchy.models import (
    PromptGateReceipt,
    PromptTreeNode,
)


def evaluate_prompt_gates(
    node: PromptTreeNode,
    payload: Mapping[str, Any],
    *,
    catalog: Mapping[str, Any] | None = None,
    host_danger_signals: Sequence[str] = (),
    custom_detectors: Mapping[str, Callable[[Any], bool]] | None = None,
) -> PromptGateReceipt:
    """Candidates remain inert; OEEIS owns admission and OEWAS owns evaluation."""
    admitted_ids = (
        tuple(antibody.antibody_id for antibody in admitted_antibodies(catalog).admitted)
        if catalog
        else ()
    )
    return evaluate_bound_prompt_gates(
        node,
        payload,
        admitted_antibody_ids=admitted_ids,
        host_danger_signals=host_danger_signals,
        custom_detectors=custom_detectors,
    )
