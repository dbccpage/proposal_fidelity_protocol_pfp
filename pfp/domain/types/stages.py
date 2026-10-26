"""PFP Stages and Execution Controllers (11 Numbered Pipeline Stages).

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import Field

from .base import AuthorityEffect, PfpBaseModel


class PfpStageName(str, Enum):
    ADMIT = "admit"
    IDEATION = "ideation"
    AUDIT = "audit"
    L2_EXTRACTION = "l2_extraction"
    EVALUATION = "evaluation"
    ADVERSARIAL = "adversarial"
    CHALLENGE_REPLAY = "challenge_replay"
    SELECTION = "selection"
    RECEIPT = "receipt"
    HAND_OFF = "hand_off"
    EVIDENCE_PLAN = "evidence_plan"


class PfpStageExecutor(str, Enum):
    MODEL = "model"
    HOST = "host"


class PfpStageInputContract(PfpBaseModel):
    preserve_original_seed: bool
    retain_stage_2_candidates: bool
    candidate_source_stage: int
    independent_checker_required: bool


class PfpStageFile(PfpBaseModel):
    stage: int = Field(ge=1, le=11)
    name: PfpStageName
    executor: PfpStageExecutor
    requires: list[int] = Field(default_factory=list)
    seat: str | None = None
    version: str
    derived_under_policy: Literal["SPK-001"] = "SPK-001"
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    source_template: str
    system_prompt: str
    user_prompt: str
    response_schema: dict[str, Any] | None = None
    input_contract: PfpStageInputContract | None = None
    obligation_rules: dict[str, str] | None = None


class PfpStageReference(PfpBaseModel):
    stage: int = Field(ge=1, le=11)
    name: PfpStageName
    executor: PfpStageExecutor
    requires: list[int] = Field(default_factory=list)
    seat: str | None = None


class PfpStageController(PfpBaseModel):
    policy_id: Literal["SPK-001"] = "SPK-001"
    version: str
    public_stage_count: Literal[11] = 11
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    system_prompt: str
    worked_example: str
    stages: list[PfpStageReference] = Field(min_length=11, max_length=11)


# Aliases
StageName = PfpStageName
StageExecutor = PfpStageExecutor
StageInputContract = PfpStageInputContract
StageFile = PfpStageFile
StageReference = PfpStageReference
StageController = PfpStageController
