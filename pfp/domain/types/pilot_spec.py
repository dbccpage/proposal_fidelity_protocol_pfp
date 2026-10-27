"""PFP Pilot Specification Data Types (spec.yaml).

AuthorityEffect: None.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal

from pydantic import Field, model_validator

from pfp.domain.value_objects.numerics import BoundedTemperature
from pfp.domain.value_objects.identifiers import CheckerIdVO
from pfp.domain.value_objects.numerics import DifficultyRung
from pfp.domain.value_objects.numerics import MicroUsdSpend
from pfp.domain.value_objects.identifiers import PilotId
from pfp.domain.value_objects.identifiers import PromptId
from pfp.domain.value_objects.identifiers import RequestId
from pfp.domain.value_objects.taxonomy import TaskFamilyVO
from .base import (
    ArmTemplate,
    AuthorityEffect,
    CheckerId,
    CohomologyDefectClass,
    FloatingPointRisk,
    MagmaAssociativityType,
    MissingPremise,
    ModelClass,
    PfpDomainModel,
    RepresentationRewrite,
    StructureDeltaMetric,
    TaskFamily,
    TaskModeFidelity,
    VariableIdentifierPermutation,
)


class PilotCoordinates(PfpDomainModel):
    task_family: TaskFamily | str
    difficulty_rung: int = Field(ge=1, le=5)
    representation_rewrite: RepresentationRewrite | str
    rewrite_count: int = Field(ge=0)
    legend_present: bool
    mode: str
    stage_count: int = Field(ge=1)
    pass_count: int = Field(ge=1)
    single_shot: bool
    antibody_active: bool
    antibody_ids: list[str] = Field(default_factory=list)
    model_class: ModelClass | str
    model_id: str
    temperature: float = Field(ge=0.0, le=2.0)
    target_spend_usd: float = Field(ge=0.0)

    @property
    def difficulty_rung_vo(self) -> DifficultyRung:
        return DifficultyRung(self.difficulty_rung)

    @property
    def temperature_vo(self) -> BoundedTemperature:
        return BoundedTemperature(self.temperature)

    @property
    def target_spend_vo(self) -> MicroUsdSpend:
        return MicroUsdSpend.from_usd(self.target_spend_usd)


class PilotIngress(PfpDomainModel):
    task_mode_fidelity: TaskModeFidelity | str
    variable_identifier_permutation: VariableIdentifierPermutation | str
    floating_point_approximation_risk: FloatingPointRisk | str
    arm_template: ArmTemplate | str
    missing_premise: MissingPremise | str
    cohomology_defect_class: CohomologyDefectClass | str
    magma_associativity_type: MagmaAssociativityType | str


class PilotHostGate(PfpDomainModel):
    checker_id: CheckerId | str
    response_schema: str
    residual_logging: bool
    structure_delta_metric: StructureDeltaMetric | str
    expected_outcome: str

    @property
    def checker_id_vo(self) -> CheckerIdVO:
        val = self.checker_id.value if hasattr(self.checker_id, "value") else str(self.checker_id)
        return CheckerIdVO(val)


class PilotTestPlanReference(PfpDomainModel):
    path: str
    cases: int | None = None
    tests: int | None = None
    seed: str | None = None
    prompt_template: str | None = None
    p_star: str | None = None
    seed_rewrite_first: str | None = None
    seed_rewrite_last: str | None = None
    p_star_rewrite_first: str | None = None
    p_star_rewrite_last: str | None = None
    mode_id: int | None = None
    packet: str | None = None
    variations: int | None = None


class PilotResponsesReference(PfpDomainModel):
    directory: str


class PilotSpec(PfpDomainModel):
    schema_: Literal["pfp.pilot-spec.v1"] = Field(default="pfp.pilot-spec.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    pilot_id: str
    prompt_id: str
    parent_prompt_id: str | None = None
    generation_id: int = 0
    phase: str
    split: str
    coordinates: PilotCoordinates
    ingress: PilotIngress
    host_gate: PilotHostGate
    test_plan: PilotTestPlanReference | None = None
    responses: PilotResponsesReference | None = None
    models: list[str] | None = None

    @model_validator(mode="after")
    def validate_value_objects(self) -> PilotSpec:
        PilotId(self.pilot_id)
        PromptId(self.prompt_id)
        if self.parent_prompt_id:
            PromptId(self.parent_prompt_id)
        return self

    @property
    def pilot_id_vo(self) -> PilotId:
        return PilotId(self.pilot_id)

    @property
    def prompt_id_vo(self) -> PromptId:
        return PromptId(self.prompt_id)

    @property
    def schema_version(self) -> str:
        return self.schema_

    def to_aggregate(self, seed: Any, response: Any = None) -> Any:
        """Bind source documents and retain response claims for fresh raw-reply evaluation."""
        from ..aggregates.pilot_aggregate import PilotAggregate

        if seed.pilot_id != self.pilot_id:
            raise ValueError("INV_PILOT_01 violation: seed/spec pilot binding mismatch")
        checker_str = str(self.host_gate.checker_id.value if hasattr(self.host_gate.checker_id, "value") else self.host_gate.checker_id)
        family_str = str(self.coordinates.task_family.value if hasattr(self.coordinates.task_family, "value") else self.coordinates.task_family)

        req_id = seed.request_id_vo if hasattr(seed, "request_id_vo") else RequestId(seed.request_id)

        return PilotAggregate(
            pilot_id=self.pilot_id_vo,
            prompt_id=self.prompt_id_vo,
            request_id=req_id,
            difficulty_rung=self.coordinates.difficulty_rung_vo,
            checker_id=CheckerIdVO(checker_str),
            task_family=TaskFamilyVO(family_str),
            target_spend=self.coordinates.target_spend_vo,
            temperature=self.coordinates.temperature_vo,
            seed_prompt=seed.seed_prompt,
            expected_answer=deepcopy(seed.expected_outcome.answer),
            expected_outcome=seed.expected_outcome.status,
            response=deepcopy(response),
        )

