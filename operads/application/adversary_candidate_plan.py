"""Fail-closed, non-symmetric OEWAS plan compilation for Adversary.

This compiler checks a *declared* ordered boundary and binds the exact source
documents. Its output is always a candidate: source text cannot self-admit and
this module does not impersonate an OEEIS admission or an executable plan.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from ..domain.entities.operation_v3 import OperationV3, PortSpecV3
from ..domain.entities.skill_document_v3 import SkillDocumentV3
from ..domain.planar_substitution import OPERAD_COLOURS
from ..domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
    DeclarationFacet,
    ExecutorBindingFacet,
    SchemaBindingFacet,
    ValidationFacet,
)
from .commands.compile_catalog import operation_content_digest

_SOURCE_PREFIX = "operads/catalog/operands/v1/"
_TYPED_SOURCE_PREFIX = "operads/catalog/contracts/v1/"
_SOURCE_NAME = re.compile(r"[a-z][a-z0-9_-]*\Z")
_CAPABILITY_NAME = re.compile(r"[a-z][a-z0-9_.:/-]{0,127}\Z")
_PROJECTED_SOURCE = re.compile(r"(?:operads|\.agents)/skills/[a-z0-9][a-z0-9_-]{0,127}/SKILL\.md\Z")
_PROJECTION_PATH = re.compile(r"operads/catalog/projections/v3/[a-z0-9][a-z0-9_-]{0,127}\.json\Z")
_MAX_SOURCES = 64
_MAX_TREE_NODES = 128
_MAX_TREE_DEPTH = 16
_MAX_INSTRUCTION_BYTES = 65536


class PlanRefusal(ValueError):
    """A typed reason why a source-only composition is not a candidate plan."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code


@dataclass(frozen=True, slots=True)
class PlanNodeV01:
    operation_id: str
    # Bindings name *original* input slots. Their order is not a permutation.
    children: tuple[tuple[int, PlanNodeV01], ...] = ()


@dataclass(frozen=True, slots=True)
class CandidateInstructionPlanV01:
    root_operation_id: str
    inputs: tuple[PortSpecV3, ...]
    output: PortSpecV3
    ordered_operand_bodies: tuple[str, ...]
    source_digests: tuple[tuple[str, str], ...]
    operation_ids: tuple[str, ...]
    effects: tuple[str, ...]
    tool_refs: tuple[str, ...]
    operation_count: int
    instruction_bytes: int
    plan_digest: str
    admission: str = "Unadmitted"
    canonical_payload: bytes = b""


def port_contract(port: PortSpecV3) -> tuple[str, str, str, str, str]:
    return (
        str(port.colour_id),
        str(port.schema_ref),
        str(port.schema_digest),
        port.validator_ref,
        str(port.validator_digest),
    )


def _bound_port(port: PortSpecV3) -> bool:
    return (
        bool(port.validator_ref)
        and str(port.colour_id) in OPERAD_COLOURS
        and str(port.schema_ref) != "schema:any:v1"
        and port.schema_digest.hex_digest != "0" * 64
        and port.validator_digest.hex_digest != "0" * 64
    )


def _check_operation(op: OperationV3) -> None:
    life = op.lifecycle
    if life.admission is AdmissionFacet.RETIRED:
        raise PlanRefusal("OPERATION_RETIRED", str(op.operation_id))
    if (
        life.declaration is not DeclarationFacet.DECLARED
        or life.schema_binding is not SchemaBindingFacet.BOUND
        or life.executor_binding is not ExecutorBindingFacet.BOUND
        or life.validation is not ValidationFacet.VALIDATED
        or life.schema_digest is None
        or life.executor_digest is None
        or life.schema_digest.hex_digest == "0" * 64
        or life.executor_digest.hex_digest == "0" * 64
    ):
        raise PlanRefusal("OPERATION_UNBOUND", str(op.operation_id))
    if any(not _bound_port(port) for port in (*op.inputs, op.output)):
        raise PlanRefusal("PORT_UNBOUND", str(op.operation_id))
    if op.authority_effect.value != "None" or op.authority_ceiling.value != "None":
        raise PlanRefusal("AUTHORITY_EFFECT_FORBIDDEN", str(op.operation_id))
    for name, values in (("EFFECT", op.effects), ("TOOL", op.tool_refs)):
        if (
            type(values) is not tuple
            or any(
                type(value) is not str or _CAPABILITY_NAME.fullmatch(value) is None
                for value in values
            )
            or len(values) != len(set(values))
        ):
            raise PlanRefusal(f"{name}_DECLARATION_INVALID", str(op.operation_id))


def compile_candidate_plan(
    documents: tuple[SkillDocumentV3, ...],
    root: PlanNodeV01,
    *,
    allowed_effects: frozenset[str] = frozenset(),
    allowed_tool_refs: frozenset[str] = frozenset(),
    max_nodes: int = _MAX_TREE_NODES,
    max_instruction_bytes: int = _MAX_INSTRUCTION_BYTES,
    projection: dict | None = None,
    projection_path: str | None = None,
) -> CandidateInstructionPlanV01:
    """Compile an explicit finite operation tree; never grant execution authority.

    Each short source file declares one instruction operand and one typed
    operation. Recursive slot substitution preserves input order. A duplicate,
    stale, unbound or mismatched source refuses instead of becoming prose.
    Actual ordered bodies bind the digest independently of declared source pins.
    Fresh source reading separately owns correspondence to original raw bytes.
    """
    if type(root) is not PlanNodeV01 or not documents:
        raise PlanRefusal("PLAN_INPUT_INVALID", "root and nonempty documents are required")
    for name, values in (("effects", allowed_effects), ("tools", allowed_tool_refs)):
        if type(values) is not frozenset or any(
            type(value) is not str or _CAPABILITY_NAME.fullmatch(value) is None for value in values
        ):
            raise PlanRefusal("PLAN_CEILING_INVALID", name)
    if (
        type(max_nodes) is not int
        or not 1 <= max_nodes <= _MAX_TREE_NODES
        or type(max_instruction_bytes) is not int
        or not 1 <= max_instruction_bytes <= _MAX_INSTRUCTION_BYTES
    ):
        raise PlanRefusal("PLAN_CEILING_INVALID", "node and text budgets")
    if len(documents) > _MAX_SOURCES:
        raise PlanRefusal("SOURCE_BUDGET_EXCEEDED", str(len(documents)))
    by_id: dict[str, tuple[SkillDocumentV3, OperationV3]] = {}
    operands: set[str] = set()
    paths: set[str] = set()
    for doc in documents:
        if type(doc) is not SkillDocumentV3 or len(doc.operations) != 1 or len(doc.operands) != 1:
            raise PlanRefusal("SOURCE_SHAPE_INVALID", "one operation and operand per source")
        op = doc.operations[0]
        operand = doc.operands[0]
        op_id = str(op.operation_id)
        operand_id = str(operand.operand_id)
        path = doc.source_relative_path
        relative = path.removeprefix(_SOURCE_PREFIX) if path.startswith(_SOURCE_PREFIX) else ""
        parts = relative.split("/")
        legacy_path = not (
            len(parts) != 2
            or _SOURCE_NAME.fullmatch(parts[0]) is None
            or not parts[1].endswith(".md")
            or _SOURCE_NAME.fullmatch(parts[1][:-3]) is None
        )
        typed_name = (
            path.removeprefix(_TYPED_SOURCE_PREFIX) if path.startswith(_TYPED_SOURCE_PREFIX) else ""
        )
        typed_path = typed_name.endswith(".json") and (
            _SOURCE_NAME.fullmatch(typed_name[:-5]) is not None
            or (
                typed_name.startswith("lessons/")
                and _SOURCE_NAME.fullmatch(typed_name[len("lessons/") : -5]) is not None
            )
        )
        projected_path = projection is not None and _PROJECTED_SOURCE.fullmatch(path) is not None
        if not (legacy_path or typed_path or projected_path):
            raise PlanRefusal("SOURCE_PATH_INVALID", path)
        if op_id in by_id or operand_id in operands or path in paths:
            raise PlanRefusal("DUPLICATE_SOURCE_ID", op_id)
        if op.operand_refs != (operand.operand_id,):
            raise PlanRefusal("OPERAND_REFERENCE_MISMATCH", op_id)
        if operand.dependencies:
            raise PlanRefusal("UNRESOLVED_OPERAND_DEPENDENCY", operand_id)
        if (
            not operand.instruction_body.strip()
            or len(operand.instruction_body.encode("utf-8")) > 4096
        ):
            raise PlanRefusal("OPERAND_BODY_INVALID", operand_id)
        _check_operation(op)
        by_id[op_id] = (doc, op)
        operands.add(operand_id)
        paths.add(path)

    used: set[str] = set()
    bodies: list[str] = []
    trace: list[dict] = []
    visited_nodes = 0
    instruction_bytes = 0
    effects: set[str] = set()
    tool_refs: set[str] = set()

    def visit(
        node: PlanNodeV01, active: frozenset[int]
    ) -> tuple[tuple[PortSpecV3, ...], PortSpecV3]:
        nonlocal visited_nodes, instruction_bytes
        if type(node) is not PlanNodeV01:
            raise PlanRefusal("PLAN_NODE_INVALID", "every child must be PlanNodeV01")
        if (
            type(node.operation_id) is not str
            or not node.operation_id
            or type(node.children) is not tuple
            or any(type(binding) is not tuple or len(binding) != 2 for binding in node.children)
        ):
            raise PlanRefusal("PLAN_NODE_INVALID", "operation and ordered bindings required")
        if id(node) in active:
            raise PlanRefusal("COMPOSITION_CYCLE", node.operation_id)
        visited_nodes += 1
        if visited_nodes > max_nodes or len(active) >= _MAX_TREE_DEPTH:
            raise PlanRefusal("COMPOSITION_BUDGET_EXCEEDED", node.operation_id)
        if node.operation_id not in by_id:
            raise PlanRefusal("OPERATION_MISSING", node.operation_id)
        doc, op = by_id[node.operation_id]
        if not set(op.effects) <= allowed_effects:
            raise PlanRefusal("EFFECT_NOT_LICENSED", node.operation_id)
        if not set(op.tool_refs) <= allowed_tool_refs:
            raise PlanRefusal("TOOL_NOT_LICENSED", node.operation_id)
        effects.update(op.effects)
        tool_refs.update(op.tool_refs)
        used.add(node.operation_id)
        slots = [slot for slot, _ in node.children]
        if any(type(slot) is not int or slot < 0 or slot >= len(op.inputs) for slot in slots):
            raise PlanRefusal("SLOT_OUT_OF_BOUNDS", node.operation_id)
        if len(slots) != len(set(slots)):
            raise PlanRefusal("DUPLICATE_SLOT_BINDING", node.operation_id)
        # Visit in planar left-to-right order. Substitute in reverse only to
        # preserve the original slot indices after earlier slots expand.
        boundary = list(op.inputs)
        children_trace: list[dict] = []
        resolved: list[tuple[int, tuple[PortSpecV3, ...]]] = []
        for slot, child in sorted(node.children, key=lambda row: row[0]):
            child_inputs, child_output = visit(child, active | {id(node)})
            if port_contract(child_output) != port_contract(op.inputs[slot]):
                raise PlanRefusal("BOUNDARY_MISMATCH", f"{node.operation_id}:{slot}")
            resolved.append((slot, child_inputs))
            children_trace.append({"slot": slot, "operation_id": child.operation_id})
        for slot, child_inputs in reversed(resolved):
            boundary[slot : slot + 1] = child_inputs
        body = doc.operands[0].instruction_body
        instruction_bytes += len(body.encode("utf-8"))
        if instruction_bytes > max_instruction_bytes:
            raise PlanRefusal("INSTRUCTION_BUDGET_EXCEEDED", node.operation_id)
        bodies.append(body)
        trace.append(
            {
                "operation_id": node.operation_id,
                "operation_digest": str(operation_content_digest(op)),
                "source_path": doc.source_relative_path,
                "source_digest": str(doc.raw_digest),
                "children": children_trace,
            }
        )
        return tuple(boundary), op.output

    inputs, output = visit(root, frozenset())
    if used != set(by_id):
        raise PlanRefusal("UNUSED_SOURCE", ",".join(sorted(set(by_id) - used)))
    sources = tuple(
        sorted((doc.source_relative_path, str(doc.raw_digest)) for doc, _ in by_id.values())
    )
    payload = {
        "schema": "oewas.adversary.candidate_plan.v0.1",
        "root": root.operation_id,
        "inputs": [port_contract(port) for port in inputs],
        "output": port_contract(output),
        "sources": sources,
        "trace": trace,
        "effects": sorted(effects),
        "tool_refs": sorted(tool_refs),
        "operation_count": visited_nodes,
        "instruction_bytes": instruction_bytes,
        "ordered_operand_bodies": bodies,
    }
    if projection is not None:
        if type(projection) is not dict or type(projection_path) is not str or _PROJECTION_PATH.fullmatch(projection_path) is None:
            raise PlanRefusal("PROJECTION_INVALID", "projection and its source path required")
        try:
            rows = projection["operation_records"]
            if type(rows) is not list or any(type(row) is not dict for row in rows):
                raise ValueError("operation records must be objects")
            records = {row["operation_id"]: row for row in rows}
            if len(records) != len(rows):
                raise ValueError("duplicate projected operation")
        except (KeyError, TypeError, ValueError) as error:
            raise PlanRefusal("PROJECTION_INVALID", str(error)) from error
        for op_id, (doc, op) in by_id.items():
            record = records.get(op_id)
            if record is None or record["admission"] == "Retired":
                raise PlanRefusal("OPERATION_RETIRED", op_id)
            if record["source_path"] != doc.source_relative_path or record["content_digest"] != str(operation_content_digest(op)):
                raise PlanRefusal("PROJECTION_INVALID", op_id)
        projection_raw = json.dumps(projection, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")
        sources = tuple(sorted((*sources, (projection_path, "sha256:" + hashlib.sha256(projection_raw).hexdigest()))))
        payload["sources"] = sources
        payload["projection"] = projection
        payload["projection_path"] = projection_path
    elif projection_path is not None:
        raise PlanRefusal("PROJECTION_INVALID", "projection omitted")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "ascii"
    )
    return CandidateInstructionPlanV01(
        root_operation_id=root.operation_id,
        inputs=inputs,
        output=output,
        ordered_operand_bodies=tuple(bodies),
        source_digests=sources,
        operation_ids=tuple(row["operation_id"] for row in trace),
        effects=tuple(sorted(effects)),
        tool_refs=tuple(sorted(tool_refs)),
        operation_count=visited_nodes,
        instruction_bytes=instruction_bytes,
        plan_digest="sha256:" + hashlib.sha256(encoded).hexdigest(),
        canonical_payload=encoded,
    )


def candidate_plan_material(plan: CandidateInstructionPlanV01) -> dict:
    """Return the exact existing digest payload for native signature verification."""
    if type(plan) is not CandidateInstructionPlanV01 or type(plan.canonical_payload) is not bytes:
        raise PlanRefusal("PLAN_MATERIAL_INVALID", "exact compiled candidate required")
    if (
        not plan.canonical_payload
        or "sha256:" + hashlib.sha256(plan.canonical_payload).hexdigest() != plan.plan_digest
    ):
        raise PlanRefusal("PLAN_MATERIAL_INVALID", "candidate payload digest mismatch")
    return json.loads(plan.canonical_payload)


__all__ = [
    "CandidateInstructionPlanV01",
    "PlanNodeV01",
    "PlanRefusal",
    "compile_candidate_plan",
    "port_contract",
    "candidate_plan_material",
]
