"""Python Facade: OeopApiV3 returning railway-oriented Result[SuccessDTO, ApiErrorDTO]."""

from __future__ import annotations

from typing import List, Optional

from omega_engine_operations.domain.rop.result import Result
from ..application.commands.compile_catalog import CompileCatalogHandler
from ..application.commands.compile_licensed_term import CompileLicensedTermHandler
from ..application.commands.compile_projection import CompileProjectionHandler
from ..application.commands.verify_catalog import VerifyCatalogHandler
from ..application.dtos.api_error_dto import ApiErrorDTO
from ..application.dtos.command_dtos import (
    CompileCatalogCommand,
    CompileLicensedTermCommand,
    CompileProjectionCommand,
    VerifyCatalogCommand,
)
from ..application.dtos.query_dtos import (
    GetCatalogQuery,
    ValidateWorkflowsQuery,
    WorkflowEdgeDTO,
    WorkflowNodeDTO,
)
from ..application.dtos.success_dtos import (
    CompileCatalogResultDTO,
    LicensedTermResultDTO,
    ProjectionResultDTO,
    VerifyCatalogResultDTO,
    WorkflowValidationResultDTO,
)
from ..application.queries.get_catalog import GetCatalogHandler
from ..application.queries.validate_workflows import ValidateWorkflowsHandler
from ..domain.entities.catalog_v3 import EstateCatalogV3
from ..domain.value_objects.identifier import (
    CausationId,
    CorrelationId,
    EstateRef,
    IdempotencyKey,
)


class OeopApiV3:
    def __init__(
        self,
        compile_catalog_handler: CompileCatalogHandler,
        verify_catalog_handler: VerifyCatalogHandler,
        compile_projection_handler: CompileProjectionHandler,
        compile_licensed_term_handler: CompileLicensedTermHandler,
        validate_workflows_handler: ValidateWorkflowsHandler,
        get_catalog_handler: GetCatalogHandler,
    ) -> None:
        self._compile_catalog = compile_catalog_handler
        self._verify_catalog = verify_catalog_handler
        self._compile_projection = compile_projection_handler
        self._compile_licensed_term = compile_licensed_term_handler
        self._validate_workflows = validate_workflows_handler
        self._get_catalog = get_catalog_handler

    def compile_catalog(
        self,
        estate_ref: str = "canonical",
        correlation_id: str = "req-001",
        causation_id: str = "init",
        idempotency_key: Optional[str] = None,
        expected_version: Optional[int] = None,
    ) -> Result[CompileCatalogResultDTO, ApiErrorDTO]:
        cmd = CompileCatalogCommand(
            estate_ref=EstateRef(estate_ref),
            correlation_id=CorrelationId(correlation_id),
            causation_id=CausationId(causation_id),
            idempotency_key=IdempotencyKey(idempotency_key) if idempotency_key else None,
            expected_version=expected_version,
        )
        return self._compile_catalog.handle(cmd)

    def verify_catalog(
        self,
        catalog_id: str,
        correlation_id: str = "req-001",
        causation_id: str = "init",
    ) -> Result[VerifyCatalogResultDTO, ApiErrorDTO]:
        cmd = VerifyCatalogCommand(
            catalog_id=catalog_id,
            correlation_id=CorrelationId(correlation_id),
            causation_id=CausationId(causation_id),
        )
        return self._verify_catalog.handle(cmd)

    def compile_projection(
        self,
        catalog_id: str,
        target_format: str = "operad_v1",
        correlation_id: str = "req-001",
        causation_id: str = "init",
    ) -> Result[ProjectionResultDTO, ApiErrorDTO]:
        cmd = CompileProjectionCommand(
            catalog_id=catalog_id,
            target_format=target_format,
            correlation_id=CorrelationId(correlation_id),
            causation_id=CausationId(causation_id),
        )
        return self._compile_projection.handle(cmd)

    def compile_licensed_term(
        self,
        agent_id: str,
        term_expr: str,
        correlation_id: str = "req-001",
        causation_id: str = "init",
    ) -> Result[LicensedTermResultDTO, ApiErrorDTO]:
        cmd = CompileLicensedTermCommand(
            agent_id=agent_id,
            term_expr=term_expr,
            correlation_id=CorrelationId(correlation_id),
            causation_id=CausationId(causation_id),
        )
        return self._compile_licensed_term.handle(cmd)

    def validate_workflows(
        self,
        nodes: List[dict],
        edges: List[dict],
    ) -> Result[WorkflowValidationResultDTO, ApiErrorDTO]:
        node_dtos = tuple(
            WorkflowNodeDTO(
                node_id=n.get("node_id", ""),
                operation_id=n.get("operation_id", ""),
                inputs=tuple(n.get("inputs", [])),
                outputs=tuple(n.get("outputs", [])),
                input_colours=tuple(sorted(
                    (str(name), str(colour))
                    for name, colour in n.get("input_colours", {}).items()
                )) if isinstance(n.get("input_colours", {}), dict) else (),
                output_colours=tuple(sorted(
                    (str(name), str(colour))
                    for name, colour in n.get("output_colours", {}).items()
                )) if isinstance(n.get("output_colours", {}), dict) else (),
            )
            for n in nodes
        )
        edge_dtos = tuple(
            WorkflowEdgeDTO(
                source_node_id=e.get("source_node_id", ""),
                source_output=e.get("source_output", ""),
                target_node_id=e.get("target_node_id", ""),
                target_input=e.get("target_input", ""),
            )
            for e in edges
        )
        query = ValidateWorkflowsQuery(nodes=node_dtos, edges=edge_dtos)
        return self._validate_workflows.handle(query)

    def get_catalog(self, catalog_id: str) -> Result[EstateCatalogV3, ApiErrorDTO]:
        query = GetCatalogQuery(catalog_id=catalog_id)
        return self._get_catalog.handle(query)
