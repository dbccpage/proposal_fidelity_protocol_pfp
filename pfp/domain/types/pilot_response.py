"""PFP Pilot Response, Sanitization Reports & Evaluation Receipts (response.yaml).

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from pfp.domain.value_objects.identifiers import PilotId
from pfp.domain.value_objects.identifiers import RequestId
from .base import (
    AuthorityEffect,
    EvaluationStatus,
    ExecutionMode,
    PfpDomainModel,
    TrialStatus,
)


class ResponseSummaryPayload(PfpDomainModel):
    narrowest_defensible_thesis: str
    evidence_scope: str
    next_concrete_test: str


class ProcessIntegrityPayload(PfpDomainModel):
    seed_allows_theory_refutation: bool
    detected_prompt_biases: list[str] = Field(default_factory=list)
    should_continue: bool


class ResponseSectionPayload(PfpDomainModel):
    name: str | None = None
    title: str | None = None
    rows: list[Any] = Field(default_factory=list)
    body: str | None = None
    content: str | None = None
    status: str | None = None
    notes: list[str] | str | None = None
    subsections: list[dict[str, Any]] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")


class PromptResponsePayload(PfpDomainModel):
    derived_under_policy: Literal["SPK-001"] | str = "SPK-001"
    summary: ResponseSummaryPayload
    process_integrity: ProcessIntegrityPayload
    sections: list[ResponseSectionPayload | str] = Field(default_factory=list)
    answer: Any | None = None


class SanitizationReport(PfpDomainModel):
    fence_stripped: bool
    is_valid_json: bool
    structure_leakage_debt_chars: int = Field(ge=0)


class EvaluationReport(PfpDomainModel):
    checker_id: str
    expected: Any
    received: Any
    status: EvaluationStatus
    reason: str | None = None


class TokenUsageDetails(PfpDomainModel):
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: int = 0
    total_tokens: int


class CostDetails(PfpDomainModel):
    total_cost_usd: float
    total_cost_microusd: int | None = None
    cost_details: dict[str, Any] = Field(default_factory=dict)


class ExecutionReceipt(PfpDomainModel):
    provider: str | None = None
    dispatch_kind: str | None = None
    upstream_model: str | None = None
    upstream_provider: str | None = None
    dispatch_id: str | None = None
    system_fingerprint: str | None = None
    duration_seconds: float | None = None
    tokens_per_second: float | None = None
    cost_microusd: int = Field(ge=0, default=0)
    evidence: str | None = None
    timestamp_utc: str | None = None
    provider_calls: int | None = None
    usage: TokenUsageDetails | None = None
    cost: CostDetails | None = None


class InputMetadata(PfpDomainModel):
    source_file: str
    source_file_bytes: int | None = None
    source_file_kb: float | None = None
    payload_bytes: int | None = None
    payload_kb: float
    messages_count: int | None = None


class PilotResponse(PfpDomainModel):
    schema_: Literal["pfp.pilot-response.v1"] = Field(default="pfp.pilot-response.v1", alias="schema")
    authority_effect: AuthorityEffect | str | None = AuthorityEffect.NONE
    test_id: str | None = None
    test_kind: str | None = None
    pilot_id: str
    case_id: str | None = None
    request_id: str
    execution_mode: ExecutionMode | str | None = None
    model_id: str | None = None
    trial_status: TrialStatus | str
    input_metadata: InputMetadata | None = None
    raw_reply: str | None = None
    reasoning_content: str | None = None
    parsed_response: PromptResponsePayload | dict[str, Any] | list[Any] | int | float | str | None = None
    parsed_json: dict[str, Any] | list[Any] | int | float | str | None = None
    extracted_answer: Any | None = None
    sanitization: SanitizationReport
    evaluation: EvaluationReport
    receipt: ExecutionReceipt

    @field_validator("execution_mode", mode="before")
    @classmethod
    def coerce_execution_mode(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return ExecutionMode(v)
            except ValueError:
                return v
        return v

    @field_validator("trial_status", mode="before")
    @classmethod
    def coerce_trial_status(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return TrialStatus(v)
            except ValueError:
                return v
        return v

    @model_validator(mode="after")
    def validate_value_objects(self) -> PilotResponse:
        PilotId(self.pilot_id)
        RequestId(self.request_id)
        return self

    @property
    def pilot_id_vo(self) -> PilotId:
        return PilotId(self.pilot_id)

    @property
    def request_id_vo(self) -> RequestId:
        return RequestId(self.request_id)

    @property
    def schema_version(self) -> str:
        return self.schema_

