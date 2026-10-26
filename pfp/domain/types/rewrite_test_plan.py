"""PFP Rewrite Test Plan Data Types (testplan.yaml).

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import AuthorityEffect, PfpDomainModel


class TestPlanTemplateRef(PfpDomainModel):
    path: str
    shared_by_all_tests: bool = True


class TestPlanSeedRef(PfpDomainModel):
    path: str
    seed_prompt: str
    instantiated_template: str | None = None
    prompt_id: str | None = None
    signature: str | None = None


class TestPlanExpectedOutcome(PfpDomainModel):
    answer: Any | None = None
    status: str = "ACCEPTED"


class TestPlanCounts(PfpDomainModel):
    unique_cases: int
    rewrite_files: int = 0
    tests: int


class RewriteTestCase(PfpDomainModel):
    case_id: str
    rewrite_id: str | None = None
    signature: str | None = None
    grammar: Any | None = None
    name: str | None = None
    governing_strategy: str | None = None
    governing_specification: str | None = None
    dialect_tier: str | None = None
    boundary_format: str | None = None
    semantic_carrier: Any | None = None
    seed_prompt: str | None = None
    rewritten_seed_prompt: str | None = None
    artifact: str | None = None
    instantiated_template: str | None = None
    prompt_id: str | None = None
    tests: list[str] = Field(default_factory=list)


class RewriteTestItem(PfpDomainModel):
    test_id: str
    kind: str | None = None
    rewrite_id: str | None = None
    signature: str | None = None
    grammar: Any | None = None
    seed_prompt: str | None = None
    prompt_template: str | None = None
    rewritten_seed_prompt: str | None = None
    artifact: str | None = None
    request_id: str | None = None
    prompt_id: str | None = None
    parent_prompt_id: str | None = None
    user_prompt_equals_rewritten_seed: bool | None = None
    case_id: str | None = None


class RewriteTestPlan(PfpDomainModel):
    schema_: Literal["pfp.rewrite-test-plan.v1"] = Field(default="pfp.rewrite-test-plan.v1", alias="schema")
    authority_effect: AuthorityEffect | str | None = AuthorityEffect.NONE
    pilot_id: str
    spec: str = "spec.yaml"
    responses: str = "results"
    description: str | None = None
    prompt_template: TestPlanTemplateRef
    seed: TestPlanSeedRef
    expected_outcome: TestPlanExpectedOutcome
    counts: TestPlanCounts
    cases: list[RewriteTestCase] = Field(default_factory=list)
    tests: list[RewriteTestItem] = Field(default_factory=list)
