"""Council file inputs and DTO conversion; Rust assembles the profile. AuthorityEffect: None."""

from __future__ import annotations

from pathlib import Path

from omega_engine_operations.domain.rop.result import Err
from omega_engine_woland.stage.domain import (
    LicensedWorkflowPlanV1,
    NodeAssignmentV1,
    SceneGraphV1,
    SceneSpecV1,
    SceneTransitionV1,
    SeatRequirementV1,
    StopConditionV1,
    SwarmDefinitionV1,
    SwarmProfileV1,
)

from ..infrastructure.native import invoke


def _tuples(value):
    if isinstance(value, list):
        return tuple(_tuples(item) for item in value)
    if isinstance(value, dict):
        return {key: _tuples(item) for key, item in value.items()}
    return value


def load_woland_council_profile(
    governance_dir: str | Path | None = None,
    *,
    retinue_mode: str = "core",
) -> tuple[
    SwarmDefinitionV1, SceneGraphV1, SwarmProfileV1, LicensedWorkflowPlanV1, StopConditionV1
]:
    """Load the council. Default width is core; ``retinue_mode="full"`` keeps the full cast."""
    if governance_dir is None:
        current_path = Path(__file__).resolve()
        repo_root = current_path
        for parent in current_path.parents:
            if (parent / "omega_engine_governance").is_dir():
                repo_root = parent
                break
        woland_dir = repo_root / "omega_engine_woland" / "the_master_and_margarita"
        if woland_dir.is_dir():
            governance_dir = woland_dir
        else:
            governance_dir = (
                repo_root
                / "omega_engine_governance"
                / "anomalon_councils"
                / "the_master_and_margarita"
            )
    else:
        governance_dir = Path(governance_dir)

    root = Path(governance_dir)
    result = invoke(
        "council",
        retinue=(root / "wolands_retinue.yaml").read_text(encoding="utf-8"),
        scenes=(root / "scenes.yaml").read_text(encoding="utf-8"),
        retinue_mode=retinue_mode,
    )
    if isinstance(result, Err):
        error = result.error
        if error.code == "WOLAND_EVIDENCE_TYPE_ERROR":
            raise TypeError(error.message)
        failure = ValueError(error.message)
        failure.refusal_code = error.code
        raise failure
    definition, graph, profile, plan, stop = result.value
    definition, graph, profile, plan, stop = map(_tuples, (definition, graph, profile, plan, stop))
    definition["seat_requirements"] = tuple(
        SeatRequirementV1(**item) for item in definition["seat_requirements"]
    )
    plan["assignments"] = tuple(NodeAssignmentV1(**item) for item in plan["assignments"])
    graph["scenes"] = tuple(SceneSpecV1(**item) for item in graph["scenes"])
    graph["transitions"] = tuple(SceneTransitionV1(**item) for item in graph["transitions"])
    return (
        SwarmDefinitionV1(**definition),
        SceneGraphV1(**graph),
        SwarmProfileV1(**profile),
        LicensedWorkflowPlanV1(**plan),
        StopConditionV1(**stop),
    )
