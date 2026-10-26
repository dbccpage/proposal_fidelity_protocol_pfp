"""Pilot dimension and coordinate definitions. AuthorityEffect: None."""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable
from pydantic import Field
from omega_engine_pfp.domain.types.base import PfpBaseModel


class DimensionDefinition(PfpBaseModel):
    """Specification of an orthogonal coordinate dimension in the Cartesian product."""

    dimension_id: str
    display_name: str
    type: str
    cardinality_baseline: int
    levels: list[Any]
    note: str = ""


class CartesianCoordinate(PfpBaseModel):
    """A single concrete point in the PFP Cartesian Product space."""

    task_family: str
    difficulty_rung: int = Field(ge=1)
    prompt_representation: str
    operational_mode: str
    stage_pipeline: str = Field(default="single_pass")
    rewrite_strategy: str = Field(default="none")
    gate_profile: str = Field(default="canonical_exact_rational")
    inoculation_status: str = Field(default="none")
    model_tier: str = Field(default="class_8b")
    decoding_control: str = Field(default="deterministic_t0")
    execution_channel: str = Field(default="offline_fixture")

    def coordinate_vector(self) -> tuple[str, int, str, str, str, str, str, str, str, str, str]:
        return (
            self.task_family,
            self.difficulty_rung,
            self.prompt_representation,
            self.operational_mode,
            self.stage_pipeline,
            self.rewrite_strategy,
            self.gate_profile,
            self.inoculation_status,
            self.model_tier,
            self.decoding_control,
            self.execution_channel,
        )


class SamplingSlice(PfpBaseModel):
    """Definition of an empirical sampling projection over the Cartesian space."""

    slice_id: str
    name: str
    pilot_count: int
    pilot_range: str = ""
    focus: str = ""
    constraints: dict[str, Any] = Field(default_factory=dict)
