"""Thin workflow graph DTO adapter to the native runtime."""

from __future__ import annotations

from dataclasses import asdict

from operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from operations.domain.rop.result import Err, Ok, Result

from ..dtos.api_error_dto import ApiErrorDTO
from ..dtos.query_dtos import ValidateWorkflowsQuery
from ..dtos.success_dtos import WorkflowValidationResultDTO


class ValidateWorkflowsHandler:
    def handle(
        self, query: ValidateWorkflowsQuery
    ) -> Result[WorkflowValidationResultDTO, ApiErrorDTO]:
        response = RustSymbolGameHost().invoke_runtime("workflow_graph", asdict(query))
        if isinstance(response, Err):
            return Err(
                ApiErrorDTO(
                    code=response.error.code, message=response.error.message, status_code=503
                )
            )
        envelope = response.value
        if not envelope["success"]:
            return Err(
                ApiErrorDTO(
                    code="WORKFLOW_GRAPH_DISPATCH_FAILED",
                    message=str(envelope["error"]),
                    status_code=500,
                )
            )
        reply = envelope["result"]
        if reply["refusal"] is not None:
            return Err(
                ApiErrorDTO(code=reply["refusal"]["code"], message=reply["refusal"]["message"])
            )
        wire = dict(reply["outcome"])
        if (
            query.typed is not None
            and wire.get("is_valid") is True
            and type(wire.get("typed_interface")) is not dict
        ):
            return Err(
                ApiErrorDTO(code="GRAPH_RESULT_MALFORMED", message="typed native interface absent")
            )
        for key in ("cycles", "execution_stages"):
            wire[key] = tuple(tuple(row) for row in wire[key])
        for key in (
            "colour_mismatches",
            "orphaned_edges",
            "topological_order",
            "duplicate_node_ids",
        ):
            wire[key] = tuple(wire[key])
        return Ok(WorkflowValidationResultDTO(**wire))
