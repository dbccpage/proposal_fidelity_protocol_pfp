"""Versioned explicit workflow wire over the existing typed capability profile."""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, Literal

from pydantic import Field, model_validator

from ..domain.anti_skills.json_wire import loads_strict_json
from ..domain.entities.typed_workflow import (
    TypedWorkflowV1,
    WorkflowBindingV1,
    WorkflowInputV1,
    WorkflowNodeV1,
)
from .typed_capabilities_v1 import Identifier, StrictWire, canonical_bytes

Digest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
Slot = Annotated[int, Field(ge=0, lt=128)]


class WorkflowNodeWireV1(StrictWire):
    node_id: Identifier
    operation_id: Annotated[str, Field(min_length=1, max_length=512)]
    source_digest: Digest
    operation_digest: Digest

    @model_validator(mode="after")
    def declared_operation_identifier(self):
        self.to_domain()
        return self

    def to_domain(self) -> WorkflowNodeV1:
        return WorkflowNodeV1(**self.model_dump())


class WorkflowBindingWireV1(StrictWire):
    source_node_id: Identifier
    target_node_id: Identifier
    target_slot: Slot

    def to_domain(self) -> WorkflowBindingV1:
        return WorkflowBindingV1(**self.model_dump())


class WorkflowInputWireV1(StrictWire):
    node_id: Identifier
    slot: Slot

    def to_domain(self) -> WorkflowInputV1:
        return WorkflowInputV1(**self.model_dump())


class TypedWorkflowWireV1(StrictWire):
    schema_version: Literal["oewas.typed-workflow.v1"]
    canonicalization_profile: Literal["oewas.sorted-ascii-json.v1"]
    authority_effect: Literal["None"]
    workflow_id: Identifier
    root_node_id: Identifier
    nodes: Annotated[tuple[WorkflowNodeWireV1, ...], Field(min_length=1, max_length=128)]
    bindings: Annotated[tuple[WorkflowBindingWireV1, ...], Field(max_length=127)]
    inputs: Annotated[tuple[WorkflowInputWireV1, ...], Field(max_length=1024)]

    def to_domain(self) -> TypedWorkflowV1:
        return TypedWorkflowV1(
            self.workflow_id,
            self.root_node_id,
            tuple(node.to_domain() for node in self.nodes),
            tuple(binding.to_domain() for binding in self.bindings),
            tuple(port.to_domain() for port in self.inputs),
        )

    @classmethod
    def from_domain(cls, workflow: TypedWorkflowV1) -> TypedWorkflowWireV1:
        if type(workflow) is not TypedWorkflowV1:
            raise ValueError("expected exact TypedWorkflowV1")
        data = {
            "schema_version": "oewas.typed-workflow.v1",
            "canonicalization_profile": "oewas.sorted-ascii-json.v1",
            "authority_effect": "None",
            **asdict(workflow),
        }
        return cls.model_validate_json(canonical_bytes(data))


def parse_typed_workflow(raw: bytes) -> TypedWorkflowWireV1:
    if type(raw) is not bytes or not 1 <= len(raw) <= 131072:
        raise ValueError("workflow JSON must be 1..131072 exact bytes")
    try:
        value = loads_strict_json(raw.decode("utf-8"))
        return TypedWorkflowWireV1.model_validate_json(canonical_bytes(value))
    except RecursionError as exc:
        raise ValueError("workflow JSON nesting exceeds the parser limit") from exc


def canonical_workflow_bytes(workflow: TypedWorkflowV1) -> bytes:
    return canonical_bytes(TypedWorkflowWireV1.from_domain(workflow).model_dump(mode="json"))
