"""Pydantic wire models for FastAPI serialization and HTTP contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from governance.domain.ingress.limits import (
    MAX_ADMITTED_TEXT_BYTES,
    REFUSAL_TEXT_TOO_LARGE,
    check_text_bytes,
)


class CompileCatalogRequest(BaseModel):
    estate_ref: str = Field(default="canonical", description="Logical estate reference")
    correlation_id: str = Field(default="req-001", description="Correlation ID")
    causation_id: str = Field(default="init", description="Causation ID")
    idempotency_key: str | None = Field(default=None, description="Idempotency key")
    expected_version: int | None = Field(
        default=None, description="Expected catalog version"
    )


class VerifyCatalogRequest(BaseModel):
    correlation_id: str = Field(default="req-001", description="Correlation ID")
    causation_id: str = Field(default="init", description="Causation ID")


class CompileProjectionRequest(BaseModel):
    target_format: str = Field(
        default="operad_v1", description="Target compatibility format"
    )
    correlation_id: str = Field(default="req-001", description="Correlation ID")
    causation_id: str = Field(default="init", description="Causation ID")


class CompileLicensedTermRequest(BaseModel):
    agent_id: str = Field(description="Agent identifier")
    term_expr: str = Field(
        description=f"Mathematical term expression; at most {MAX_ADMITTED_TEXT_BYTES} UTF-8 bytes"
    )
    correlation_id: str = Field(default="req-001", description="Correlation ID")
    causation_id: str = Field(default="init", description="Causation ID")

    @field_validator("term_expr")
    @classmethod
    def bound_term_bytes(cls, value: str) -> str:
        check_text_bytes(
            value, limit=MAX_ADMITTED_TEXT_BYTES, refusal_code=REFUSAL_TEXT_TOO_LARGE
        )
        return value


class WorkflowNodeWire(BaseModel):
    node_id: str
    operation_id: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    input_colours: dict[str, str] = Field(default_factory=dict)
    output_colours: dict[str, str] = Field(default_factory=dict)


class WorkflowEdgeWire(BaseModel):
    source_node_id: str
    source_output: str
    target_node_id: str
    target_input: str


class ValidateWorkflowsRequest(BaseModel):
    nodes: list[WorkflowNodeWire] = Field(default_factory=list)
    edges: list[WorkflowEdgeWire] = Field(default_factory=list)
