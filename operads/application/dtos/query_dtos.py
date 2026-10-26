"""Query DTOs for OEWAS V3 Application Handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True, slots=True)
class GetCatalogQuery:
    catalog_id: str


@dataclass(frozen=True, slots=True)
class WorkflowNodeDTO:
    node_id: str
    operation_id: str
    inputs: Tuple[str, ...]
    outputs: Tuple[str, ...]
    input_colours: Tuple[Tuple[str, str], ...] = ()
    output_colours: Tuple[Tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class WorkflowEdgeDTO:
    source_node_id: str
    source_output: str
    target_node_id: str
    target_input: str


@dataclass(frozen=True, slots=True)
class ValidateWorkflowsQuery:
    nodes: Tuple[WorkflowNodeDTO, ...]
    edges: Tuple[WorkflowEdgeDTO, ...]
    typed: dict | None = None
