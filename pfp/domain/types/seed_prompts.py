"""PFP Seed Prompts, AST Rewrites, and Oracle Ground Truth Expectations (seed.yaml & rewrite_*.yaml).

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import ConfigDict, Field, model_validator

from omega_engine_pfp.domain.value_objects.numerics import DifficultyRung
from omega_engine_pfp.domain.value_objects.identifiers import PilotId
from omega_engine_pfp.domain.value_objects.identifiers import RequestId
from .base import AuthorityEffect, CheckerId, PfpDomainModel


class CodebookSlotModel(PfpDomainModel):
    """Sidecar codebook slot for observational separation or parameter bindings."""
    role: str
    source_text_span: str
    binding_value: Any | None = None
    carrier_type: str | None = None
    model_config = ConfigDict(extra="allow")


class RewriteMetadataModel(PfpDomainModel):
    """Metadata detailing the AST/wire rewrite applied to the seed stimulus."""
    rewrite_id: str
    name: str
    governing_specification: str
    governing_strategy: str
    target_stratum: str
    explanation: str
    codebook_slots: dict[str, CodebookSlotModel] = Field(default_factory=dict)
    model_config = ConfigDict(extra="allow")


class InputTypingModel(PfpDomainModel):
    """Formal syntax and carrier typing contract for prompt stimulus."""
    lexical_alphabet: str
    syntactic_category: str
    semantic_carrier: str
    dialect_tier: str
    boundary_format: str
    model_config = ConfigDict(extra="allow")


class ExpectedOutcome(PfpDomainModel):
    answer: Any
    status: str = "ACCEPTED"


class SeedPrompt(PfpDomainModel):
    schema_: Literal["pfp.seed-prompt.v1"] = Field(default="pfp.seed-prompt.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    pilot_id: str
    task_family: str
    difficulty_rung: int = Field(ge=1, le=5)
    request_id: str
    rewrite_metadata: RewriteMetadataModel | None = None
    input_typing: InputTypingModel | None = None
    seed_prompt: str
    expected_outcome: ExpectedOutcome

    @model_validator(mode="after")
    def validate_value_objects(self) -> SeedPrompt:
        PilotId(self.pilot_id)
        RequestId(self.request_id)
        DifficultyRung(self.difficulty_rung)
        return self

    @property
    def pilot_id_vo(self) -> PilotId:
        return PilotId(self.pilot_id)

    @property
    def request_id_vo(self) -> RequestId:
        return RequestId(self.request_id)

    @property
    def difficulty_rung_vo(self) -> DifficultyRung:
        return DifficultyRung(self.difficulty_rung)

    @property
    def schema_version(self) -> str:
        return self.schema_

