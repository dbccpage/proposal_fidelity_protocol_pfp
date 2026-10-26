"""PFP Pilot Granular Test Specification Data Types (test_spec.yaml).

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import AuthorityEffect, EvaluationStatus, PfpDomainModel


class ExpectedTestOutcome(PfpDomainModel):
    answer: Any | None = None
    status: str = "ACCEPTED"


class ActualTestOutcome(PfpDomainModel):
    extracted_answer: Any | None = None
    gate_status: EvaluationStatus | str = "NOT_RUN"
    reason: str | None = None
    status: str | None = None
    refusal_code: str | None = None
    transport_code: str | None = None
    parsed_json: Any | None = None
    witness_verified: bool | None = None


class TestMetrics(PfpDomainModel):
    __test__ = False
    duration_seconds: float | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    reasoning_tokens: int | None = None
    cost_usd: float | None = None
    provider_calls: int | None = None
    billing: str | None = None
    total_tokens: int | None = None


class TestSpec(PfpDomainModel):
    __test__ = False
    schema_: Literal["pfp.test-spec.v1"] = Field(default="pfp.test-spec.v1", alias="schema")
    authority_effect: AuthorityEffect | str | None = AuthorityEffect.NONE
    test_folder: str | None = None
    test_id: str
    pilot_id: str | None = None
    case_id: str
    test_index: int | None = None
    generation_id: int | None = None
    dialect_name: str | None = None
    input_source_file: str | None = None
    response_file: str | None = None
    model_id: str
    expected_outcome: ExpectedTestOutcome
    actual_outcome: ActualTestOutcome
    metrics: TestMetrics | None = None
    notes: str | None = None
