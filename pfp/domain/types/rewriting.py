"""PFP Prompt Rewriting and Wire Topologies: mss-boundary-v1, Partitions, Symbol Codebook.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import Field, model_validator

from .base import AuthorityEffect, PfpBaseModel


class PfpSpanRole(str, Enum):
    TASK = "task"
    CONSTRAINT = "constraint"
    CONTEXT = "context"
    OUTPUT = "output"
    UNRESOLVED = "unresolved"


class PfpByteSpan(PfpBaseModel):
    start_byte: int = Field(ge=0)
    end_byte: int = Field(ge=0)
    role: PfpSpanRole

    @model_validator(mode="after")
    def _validate_interval(self) -> PfpByteSpan:
        if self.end_byte <= self.start_byte:
            raise ValueError(f"end_byte ({self.end_byte}) must be strictly greater than start_byte ({self.start_byte})")
        return self


class PfpSpanPartition(PfpBaseModel):
    prompt_byte_length: int = Field(ge=1)
    spans: list[PfpByteSpan] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_cover(self) -> PfpSpanPartition:
        cursor = 0
        for span in self.spans:
            if span.start_byte != cursor:
                raise ValueError(f"Gap or overlap at byte {cursor}: next span starts at {span.start_byte}")
            cursor = span.end_byte
        if cursor != self.prompt_byte_length:
            raise ValueError(f"Spans end at byte {cursor}, but prompt_byte_length is {self.prompt_byte_length}")
        return self


class PfpBoundaryWire(PfpBaseModel):
    profile: Literal["mss-boundary-v1"] = "mss-boundary-v1"
    term: str = Field(min_length=1)


class PfpSymbolMapping(PfpBaseModel):
    symbol_token: str = Field(pattern=r"^s[0-9]+$")
    start_byte: int = Field(ge=0)
    end_byte: int = Field(ge=0)
    text: str


class PfpRewritingContract(PfpBaseModel):
    schema_id: Literal["omega.pfp.rewriting.types.v1"] = "omega.pfp.rewriting.types.v1"
    title: str
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    source: str
    span_roles: list[str] = Field(default_factory=list)
    partition_rules: list[str] = Field(default_factory=list)
    wire_profile: dict[str, Any]
    receipt_guarantees_checked_by_model: list[str] = Field(default_factory=list)
    example: dict[str, Any]


# Aliases
SpanRole = PfpSpanRole
ByteSpan = PfpByteSpan
SpanPartition = PfpSpanPartition
BoundaryWire = PfpBoundaryWire
SymbolMapping = PfpSymbolMapping
RewritingContract = PfpRewritingContract
