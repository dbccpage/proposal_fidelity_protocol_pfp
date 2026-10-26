"""PFP Pilot Comparison Results Data Types (comparison_results.yaml).

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import AuthorityEffect, PfpDomainModel


class TestKindAggregate(PfpDomainModel):
    count: int
    avg_time_sec: float
    total_time_sec: float
    avg_cost_usd: float
    total_cost_usd: float
    avg_prompt_tokens: float
    avg_completion_tokens: float
    avg_total_tokens: float
    avg_payload_kb: float
    accuracy_ratio: str
    accuracy_percent: float


class ComparisonRatios(PfpDomainModel):
    cost_ratio: float | None = None
    latency_ratio: float | None = None
    tokens_ratio: float | None = None
    payload_kb_ratio: float | None = None


class ComparisonAggregates(PfpDomainModel):
    plain_inputs: TestKindAggregate
    p_star_templated: TestKindAggregate
    overall: TestKindAggregate
    ratios_templated_vs_plain: ComparisonRatios


class TestComparisonEntry(PfpDomainModel):
    test_id: str
    test_kind: str
    case_id: str
    source_file: str
    response_file: str
    payload_kb: float
    source_kb: float | None = None
    duration_seconds: float
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: int = 0
    total_tokens: int
    cost_usd: float
    cost_microusd: int | None = None
    tokens_per_second: float | None = None
    extracted_answer: Any | None = None
    expected_answer: Any | None = None
    gate_status: str
    gate_reason: str | None = None
    answer_match: bool | None = None
    is_correct: bool | None = None


class PilotComparisonResults(PfpDomainModel):
    schema_: Literal["pfp.pilot-comparison-results.v1"] = Field(
        default="pfp.pilot-comparison-results.v1", alias="schema"
    )
    authority_effect: AuthorityEffect | str | None = AuthorityEffect.NONE
    pilot_id: str | None = None
    model_id: str | None = None
    checker_id: str | None = None
    timestamp_utc: str | None = None
    total_tests: int | None = None
    aggregates: ComparisonAggregates | None = None
    tests: list[TestComparisonEntry] = Field(default_factory=list)
    comparison_table: list[TestComparisonEntry] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.tests and self.comparison_table:
            object.__setattr__(self, "tests", list(self.comparison_table))
        elif not self.comparison_table and self.tests:
            object.__setattr__(self, "comparison_table", list(self.tests))
