"""Load six source-bound operations into the existing typed and native compilers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from ..application.commands.compile_catalog import operation_content_digest
from ..contracts.ddc_code_repair_v1 import (
    EXECUTOR_METHODS,
    STAGES,
    CodeRepairRequestV1,
    RepairOperationWireV1,
    RepairStateV1,
    RepairTerminalV1,
    canonical,
)
from ..domain.entities.operation_v3 import OperationV3, PortSpecV3
from ..domain.entities.skill_document_v3 import SkillDocumentV3
from ..domain.entities.typed_workflow import (
    TypedWorkflowV1,
    WorkflowBindingV1,
    WorkflowInputV1,
    WorkflowNodeV1,
)
from ..domain.value_objects.byte_span import SourceByteSpan
from ..domain.value_objects.content_digest import ContentDigest
from ..domain.value_objects.identifier import (
    ColourId,
    DocumentId,
    OperandId,
    OperationId,
    SchemaRef,
    SkillId,
)
from ..domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
    DeclarationFacet,
    ExecutorBindingFacet,
    SchemaBindingFacet,
    SkillLifecycleV3,
    ValidationFacet,
)
from ..domain.value_objects.operands import InstructionOperand
from ..skill_operad.skill_compiler.op_inventory import (
    SCHEMA_VERSION,
    HostBinding,
    OpInventory,
    OpSpec,
    SkillDecomposition,
    Wire,
)
from .typed_contract_compiler import _read

ROOT = "omega_engine_operads/catalog/contracts/v1"
EFFECTS = frozenset({"read_source", "write_workspace", "run_check", "emit_evidence"})


@dataclass(frozen=True)
class CodeRepairFamily:
    documents: tuple[SkillDocumentV3, ...]
    workflow: TypedWorkflowV1
    inventory: OpInventory
    wire: Wire


def load_code_repair_family(root: Path, *, executor_digest: ContentDigest) -> CodeRepairFamily:
    if type(executor_digest) is not ContentDigest or executor_digest.hex_digest == "0" * 64:
        raise ValueError("CODE_REPAIR_EXECUTOR_UNBOUND")
    schemas = {
        "request": CodeRepairRequestV1.model_json_schema(),
        "state": RepairStateV1.model_json_schema(),
        "terminal": RepairTerminalV1.model_json_schema(),
    }
    schema_digest = ContentDigest.sha256(hashlib.sha256(canonical(schemas)).hexdigest())
    validator_digest = ContentDigest.sha256(hashlib.sha256(
        (root / "omega_engine_operads/contracts/ddc_code_repair_v1.py").read_bytes()
    ).hexdigest())

    def port(name):
        return PortSpecV3(
            name, ColourId("Receipt" if name == "terminal" else "State"),
            SchemaRef(f"schema:oeop:ddc-code-repair:{name}:v1"),
            ContentDigest.sha256(hashlib.sha256(canonical(schemas[name])).hexdigest()),
            f"oeop.ddc-code-repair.{name}.v1", validator_digest,
        )

    life = SkillLifecycleV3(
        DeclarationFacet.DECLARED, SchemaBindingFacet.BOUND, ExecutorBindingFacet.BOUND,
        ValidationFacet.VALIDATED, AdmissionFacet.UNADMITTED, schema_digest, executor_digest,
    )
    documents, native_ops, nodes = [], [], []
    wire: Wire | str = "State"
    for stage in STAGES:
        path = f"{ROOT}/ddc_code_repair_{stage.lower()}.json"
        raw = _read(root, path)
        declaration = RepairOperationWireV1.model_validate_json(raw)
        op_id = f"ddc-code-repair-{stage.lower()}"
        expected = ("request" if stage == "C" else "state", "terminal" if stage == "T" else "state")
        if (declaration.stage != stage or declaration.operation_id != op_id
                or (declaration.input, declaration.output) != expected):
            raise ValueError("CODE_REPAIR_DECLARATION_MISMATCH")
        operand_id = OperandId(op_id + "-instruction")
        operation = OperationV3(
            OperationId(op_id), (port(declaration.input),), port(declaration.output),
            (operand_id,), life, "unknown", effects=declaration.effects,
            description=declaration.instruction,
        )
        token = json.dumps(declaration.instruction).encode("ascii")
        start = raw.index(token)
        line, column = raw[:start].count(b"\n") + 1, start - raw.rfind(b"\n", 0, start) - 1
        span = SourceByteSpan(start, start + len(token), line, column, line, column + len(token))
        raw_digest = ContentDigest.sha256(hashlib.sha256(raw).hexdigest())
        document = SkillDocumentV3(
            DocumentId(op_id), SkillId(op_id), path, raw_digest, raw_digest,
            operands=(InstructionOperand(operand_id, "instruction", declaration.instruction, span),),
            operations=(operation,),
        )
        documents.append(document)
        nodes.append(WorkflowNodeV1(stage.lower(), op_id, str(raw_digest), str(operation_content_digest(operation))))
        native_ops.append(OpSpec(
            op_id=op_id, summary=declaration.instruction, inputs=("State",),
            output="Receipt" if stage == "T" else "State",
            binding=HostBinding(target=(
                "omega_engine_woland/infrastructure/ddc_code_repair.py::CodeRepairRuntime."
                + dict(EXECUTOR_METHODS)[stage]
            )),
        ))
        wire = Wire(op=op_id, args=(wire,))
    workflow = TypedWorkflowV1(
        "ddc-code-repair-v1", "t", tuple(nodes),
        tuple(WorkflowBindingV1(a.lower(), b.lower(), 0) for a, b in zip(STAGES, STAGES[1:])),
        (WorkflowInputV1("c", 0),),
    )
    inventory = OpInventory(
        schema_version=SCHEMA_VERSION,
        skills=(SkillDecomposition(skill_id="ddc-code-repair", ops=tuple(native_ops), wiring=wire),),
    )
    return CodeRepairFamily(tuple(documents), workflow, inventory, wire)
