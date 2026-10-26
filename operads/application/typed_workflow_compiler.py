"""Lower a finite, pinned occurrence graph to the existing candidate compiler.

The injected graph port checks topology; candidate compilation checks full port
contracts and capability ceilings. Every result remains Unadmitted.
AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Callable
from dataclasses import dataclass, replace

from omega_engine_operations.domain.rop.result import Err, Ok

from ..contracts.typed_capabilities_v1 import canonical_bytes, digest_bytes
from ..contracts.typed_workflow_v1 import TypedWorkflowWireV1
from ..domain.entities.operation_v3 import OperationV3
from ..domain.entities.skill_document_v3 import SkillDocumentV3
from ..domain.entities.typed_workflow import (
    TypedWorkflowV1,
    WorkflowBindingV1,
    WorkflowInputV1,
    WorkflowNodeV1,
)
from .commands.compile_catalog import operation_content_bytes, operation_content_digest
from .dtos.api_error_dto import ApiErrorDTO
from .dtos.query_dtos import ValidateWorkflowsQuery, WorkflowEdgeDTO, WorkflowNodeDTO
from .dtos.success_dtos import WorkflowValidationResultDTO
from .woland_candidate_plan import (
    CandidateInstructionPlanV01,
    PlanNodeV01,
    PlanRefusal,
    compile_candidate_plan,
    port_contract,
)

_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,127}\Z")


class WorkflowCompileRefusal(PlanRefusal):
    """A bounded workflow could not become an unadmitted candidate."""


@dataclass(frozen=True, slots=True)
class CompiledWorkflowV1:
    plan: CandidateInstructionPlanV01
    workflow_digest: str
    occurrence_order: tuple[str, ...]
    native_report: WorkflowValidationResultDTO


def _workflow_snapshot(workflow: TypedWorkflowV1) -> TypedWorkflowV1:
    if type(workflow) is not TypedWorkflowV1:
        raise WorkflowCompileRefusal("WORKFLOW_SHAPE_INVALID", "exact workflow required")
    # Re-run both outer and nested invariants: frozen carriers can be tampered
    # with through object.__setattr__; JSON round trips alone normalize lists.
    TypedWorkflowV1(
        workflow.workflow_id,
        workflow.root_node_id,
        workflow.nodes,
        workflow.bindings,
        workflow.inputs,
    )
    return TypedWorkflowV1(
        workflow.workflow_id,
        workflow.root_node_id,
        tuple(
            WorkflowNodeV1(n.node_id, n.operation_id, n.source_digest, n.operation_digest)
            for n in workflow.nodes
        ),
        tuple(
            WorkflowBindingV1(b.source_node_id, b.target_node_id, b.target_slot)
            for b in workflow.bindings
        ),
        tuple(WorkflowInputV1(p.node_id, p.slot) for p in workflow.inputs),
    )


def _source_operations(documents: tuple[SkillDocumentV3, ...]) -> dict:
    if type(documents) is not tuple or not 1 <= len(documents) <= 64:
        raise WorkflowCompileRefusal("SOURCE_SHAPE_INVALID", "1..64 exact source documents")
    operations = {}
    for doc in documents:
        if (
            type(doc) is not SkillDocumentV3
            or type(doc.operations) is not tuple
            or len(doc.operations) != 1
            or type(doc.operations[0]) is not OperationV3
        ):
            raise WorkflowCompileRefusal("SOURCE_SHAPE_INVALID", "one exact operation per source")
        op = doc.operations[0]
        if type(op.inputs) is not tuple or len(op.inputs) > 128:
            raise WorkflowCompileRefusal("OPERATION_ARITY_UNSUPPORTED", "at most 128 input slots")
        op_id = str(op.operation_id)
        if op_id in operations:
            raise WorkflowCompileRefusal("DUPLICATE_SOURCE_ID", op_id)
        operations[op_id] = (doc, op)
    return operations


def _pinned_nodes(workflow: TypedWorkflowV1, operations: dict) -> dict[str, OperationV3]:
    nodes = {}
    for node in workflow.nodes:
        if node.node_id in nodes:
            raise WorkflowCompileRefusal("DUPLICATE_NODE_ID", node.node_id)
        if node.operation_id not in operations:
            raise WorkflowCompileRefusal("OPERATION_MISSING", node.operation_id)
        doc, op = operations[node.operation_id]
        if node.source_digest != str(doc.raw_digest):
            raise WorkflowCompileRefusal("SOURCE_DIGEST_MISMATCH", node.node_id)
        if node.operation_digest != str(operation_content_digest(op)):
            raise WorkflowCompileRefusal("OPERATION_DIGEST_MISMATCH", node.node_id)
        nodes[node.node_id] = op
    if workflow.root_node_id not in nodes:
        raise WorkflowCompileRefusal("ROOT_NODE_MISSING", workflow.root_node_id)
    return nodes


def _bindings(workflow: TypedWorkflowV1, nodes: dict) -> dict[tuple[str, int], str]:
    bindings = {}
    consumed = set()
    for edge in workflow.bindings:
        if edge.source_node_id not in nodes or edge.target_node_id not in nodes:
            raise WorkflowCompileRefusal("BINDING_NODE_MISSING", "both endpoints must be declared")
        if edge.target_slot >= len(nodes[edge.target_node_id].inputs):
            raise WorkflowCompileRefusal("SLOT_OUT_OF_BOUNDS", edge.target_node_id)
        target = (edge.target_node_id, edge.target_slot)
        if target in bindings:
            raise WorkflowCompileRefusal("DUPLICATE_SLOT_BINDING", str(target))
        if edge.source_node_id in consumed:
            raise WorkflowCompileRefusal("SHARED_OUTPUT_UNSUPPORTED", edge.source_node_id)
        bindings[target] = edge.source_node_id
        consumed.add(edge.source_node_id)
    return bindings


def _graph_query(
    workflow: TypedWorkflowV1, nodes: dict, operations: dict
) -> ValidateWorkflowsQuery:
    return ValidateWorkflowsQuery(
        nodes=tuple(
            WorkflowNodeDTO(
                node.node_id,
                node.operation_id,
                tuple(f"in:{i}" for i in range(len(nodes[node.node_id].inputs))),
                ("out",),
                tuple(
                    (f"in:{i}", str(port.colour_id))
                    for i, port in enumerate(nodes[node.node_id].inputs)
                ),
                (("out", str(nodes[node.node_id].output.colour_id)),),
            )
            for node in workflow.nodes
        ),
        edges=tuple(
            WorkflowEdgeDTO(
                edge.source_node_id,
                "out",
                edge.target_node_id,
                f"in:{edge.target_slot}",
            )
            for edge in workflow.bindings
        ),
        typed={
            "schema_version": "oewas.typed-graph.v1",
            "root_node_id": workflow.root_node_id,
            "pins": [
                {
                    "node_id": node.node_id,
                    "source_digest": node.source_digest,
                    "operation_digest": node.operation_digest,
                }
                for node in workflow.nodes
            ],
            "declarations": [
                {
                    "source_digest": str(doc.raw_digest),
                    "operation_json": operation_content_bytes(op).decode("ascii"),
                }
                for doc, op in operations.values()
            ],
            "inputs": [{"node_id": p.node_id, "slot": p.slot} for p in workflow.inputs],
        },
    )


def _strings(value: object, maximum: int = 256) -> bool:
    return (
        type(value) is tuple
        and len(value) <= maximum
        and all(type(item) is str and 0 < len(item) <= 2048 for item in value)
    )


def _report_shape(report: object, workflow: TypedWorkflowV1) -> None:
    if type(report) is not WorkflowValidationResultDTO:
        raise WorkflowCompileRefusal("GRAPH_RESULT_MALFORMED", "exact graph report required")
    if (
        type(report.is_valid) is not bool
        or type(report.node_count) is not int
        or type(report.edge_count) is not int
        or report.node_count != len(workflow.nodes)
        or report.edge_count != len(workflow.bindings)
    ):
        raise WorkflowCompileRefusal("GRAPH_RESULT_MALFORMED", "flag and exact input counts")
    flat = (
        report.colour_mismatches,
        report.orphaned_edges,
        report.duplicate_node_ids,
        report.topological_order,
    )
    if not all(_strings(value) for value in flat):
        raise WorkflowCompileRefusal("GRAPH_RESULT_MALFORMED", "bounded string tuples required")
    for rows in (report.cycles, report.execution_stages):
        if (
            type(rows) is not tuple
            or len(rows) > 128
            or not all(_strings(row, 129) and row for row in rows)
        ):
            raise WorkflowCompileRefusal("GRAPH_RESULT_MALFORMED", "bounded nonempty report rows")


def _report_order(report: WorkflowValidationResultDTO, workflow: TypedWorkflowV1) -> None:
    expected = {node.node_id for node in workflow.nodes}
    order = report.topological_order
    flattened = tuple(node for stage in report.execution_stages for node in stage)
    if len(order) != len(expected) or set(order) != expected or flattened != order:
        raise WorkflowCompileRefusal(
            "GRAPH_RESULT_MALFORMED", "order/stages must cover every node once"
        )
    stage_index = {node: i for i, stage in enumerate(report.execution_stages) for node in stage}
    if any(
        stage_index[e.source_node_id] >= stage_index[e.target_node_id] for e in workflow.bindings
    ):
        raise WorkflowCompileRefusal("GRAPH_RESULT_MALFORMED", "every edge must advance a stage")


def _native_report(
    validate_graph: Callable, workflow: TypedWorkflowV1, nodes: dict, operations: dict
):
    if not callable(validate_graph):
        raise WorkflowCompileRefusal("GRAPH_VALIDATOR_UNAVAILABLE", "callable graph port required")
    try:
        reply = validate_graph(_graph_query(workflow, nodes, operations))
    except Exception as exc:
        raise WorkflowCompileRefusal("GRAPH_VALIDATOR_UNAVAILABLE", type(exc).__name__) from exc
    if type(reply) is Err:
        error = reply.error
        if (
            type(error) is not ApiErrorDTO
            or type(error.code) is not str
            or _CODE.fullmatch(error.code) is None
            or type(error.message) is not str
            or len(error.message) > 2048
        ):
            raise WorkflowCompileRefusal("GRAPH_RESULT_MALFORMED", "typed graph refusal required")
        raise WorkflowCompileRefusal(error.code, error.message)
    if type(reply) is not Ok:
        raise WorkflowCompileRefusal("GRAPH_RESULT_MALFORMED", "ROP graph result required")
    report = reply.value
    _report_shape(report, workflow)
    if (
        not report.is_valid
        or report.cycles
        or report.colour_mismatches
        or report.orphaned_edges
        or report.duplicate_node_ids
    ):
        raise WorkflowCompileRefusal(
            "GRAPH_INVALID", "native graph report refused topology or colours"
        )
    _report_order(report, workflow)
    return replace(report)


def _lower_tree(workflow: TypedWorkflowV1, nodes: dict, bindings: dict):
    reached = set()
    occurrence_order = []
    open_inputs = []

    def visit(node_id: str) -> PlanNodeV01:
        reached.add(node_id)
        children = []
        for slot in range(len(nodes[node_id].inputs)):
            source = bindings.get((node_id, slot))
            if source is None:
                open_inputs.append(WorkflowInputV1(node_id, slot))
            else:
                children.append((slot, visit(source)))
        occurrence_order.append(node_id)
        return PlanNodeV01(str(nodes[node_id].operation_id), tuple(children))

    root = visit(workflow.root_node_id)
    if reached != set(nodes):
        raise WorkflowCompileRefusal("UNREACHABLE_NODE", ",".join(sorted(set(nodes) - reached)))
    if tuple(open_inputs) != workflow.inputs:
        raise WorkflowCompileRefusal(
            "ENTRY_BOUNDARY_MISMATCH", "ordered open node/slot references differ"
        )
    return root, tuple(occurrence_order)


def _workflow_digest(workflow: TypedWorkflowV1, plan: CandidateInstructionPlanV01) -> str:
    normalized = replace(
        workflow,
        nodes=tuple(sorted(workflow.nodes, key=lambda node: node.node_id)),
        bindings=tuple(
            sorted(
                workflow.bindings,
                key=lambda edge: (edge.target_node_id, edge.target_slot, edge.source_node_id),
            )
        ),
    )
    return digest_bytes(
        canonical_bytes(
            {
                "schema_version": "oewas.compiled-workflow.v1",
                "workflow": TypedWorkflowWireV1.from_domain(normalized).model_dump(mode="json"),
                "plan_digest": plan.plan_digest,
            }
        )
    )


def compile_typed_workflow(
    documents: tuple[SkillDocumentV3, ...],
    workflow: TypedWorkflowV1,
    *,
    validate_graph: Callable,
    allowed_effects: frozenset[str] = frozenset(),
    allowed_tool_refs: frozenset[str] = frozenset(),
) -> CompiledWorkflowV1:
    """Compile only a finite single-consumer graph, never admit or execute it.

    Documents are compiled aggregates supplied by the caller; their declaration
    pins are checked here. Raw file custody belongs to the existing compiler.
    The graph port is injected and must be wired to the native handler by the
    composition root. No fallback graph validator exists in this module.
    """
    try:
        workflow = _workflow_snapshot(workflow)
        operations = _source_operations(documents)
        documents = copy.deepcopy(documents)
        operations = _source_operations(documents)
        nodes = _pinned_nodes(workflow, operations)
        bindings = _bindings(workflow, nodes)
        report = _native_report(validate_graph, workflow, nodes, operations)
        root, order = _lower_tree(workflow, nodes, bindings)
        plan = compile_candidate_plan(
            documents, root, allowed_effects=allowed_effects, allowed_tool_refs=allowed_tool_refs
        )
        if report.typed_interface is not None and report.typed_interface != {
            "inputs": [list(port_contract(port)) for port in plan.inputs],
            "output": list(port_contract(plan.output)),
            "occurrence_order": list(order),
        }:
            raise WorkflowCompileRefusal(
                "GRAPH_RESULT_MALFORMED", "native ordered full interface differs"
            )
        return CompiledWorkflowV1(plan, _workflow_digest(workflow, plan), order, report)
    except WorkflowCompileRefusal:
        raise
    except PlanRefusal as exc:
        text = str(exc)
        prefix = f"{exc.code}: "
        detail = text[len(prefix) :] if text.startswith(prefix) else text
        raise WorkflowCompileRefusal(exc.code, detail) from exc
    except (ValueError, TypeError, AttributeError, RecursionError) as exc:
        raise WorkflowCompileRefusal("WORKFLOW_SHAPE_INVALID", type(exc).__name__) from exc
