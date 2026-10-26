"""Real native topology + existing exact typed compiler, with no provider calls.

Requires an installed omega_symbol_game host or OMEGA_SYMBOL_GAME_HOST. A missing
native prerequisite is an observed refusal/failure, never a skipped positive arm.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from omega_engine_operads.application.commands.compile_catalog import (
    operation_content_digest,
)
from omega_engine_operads.application.queries.validate_workflows import (
    ValidateWorkflowsHandler,
)
from omega_engine_operads.application.typed_workflow_compiler import (
    WorkflowCompileRefusal,
    compile_typed_workflow,
)
from omega_engine_operads.application.woland_candidate_plan import PlanRefusal
from omega_engine_operads.contracts.typed_workflow_v1 import (
    canonical_workflow_bytes,
)
from omega_engine_operads.domain.entities.typed_workflow import WorkflowBindingV1
from omega_engine_operads.domain.value_objects.content_digest import ContentDigest
from omega_engine_operads.domain.value_objects.identifier import SchemaRef
from omega_engine_operads.infrastructure.typed_contract_compiler import (
    compile_typed_contracts,
)
from omega_engine_operads.infrastructure.typed_workflow_compiler import (
    example_workflow,
    main,
)

ROOT = Path(__file__).resolve().parents[3]
EFFECTS = frozenset({"read_subject", "emit_finding"})


def test_current_skill_and_antiskill_compile_through_real_native_graph() -> None:
    bundle = compile_typed_contracts(ROOT)
    result = compile_typed_workflow(
        bundle.documents,
        example_workflow(ROOT),
        validate_graph=ValidateWorkflowsHandler().handle,
        allowed_effects=EFFECTS,
    )
    assert result.native_report.is_valid is True
    assert result.native_report.execution_stages == (("falsifier",), ("audit",))
    assert result.occurrence_order == ("falsifier", "audit")
    assert result.plan.admission == "Unadmitted"
    assert tuple(str(port.colour_id) for port in result.plan.inputs) == ("Contract", "Contract")
    assert str(result.plan.output.colour_id) == "Receipt"


def test_native_graph_returns_the_literal_full_typed_interface():
    from omega_engine_operads.application.woland_candidate_plan import port_contract

    result = compile_typed_workflow(
        compile_typed_contracts(ROOT).documents,
        example_workflow(ROOT),
        validate_graph=ValidateWorkflowsHandler().handle,
        allowed_effects=EFFECTS,
    )
    interface = result.native_report.typed_interface
    assert tuple(tuple(p) for p in interface["inputs"]) == tuple(
        port_contract(p) for p in result.plan.inputs
    )
    assert tuple(interface["output"]) == port_contract(result.plan.output)
    assert tuple(interface["occurrence_order"]) == result.occurrence_order


def _direct_typed_payload():
    port = {
        "name": "entry",
        "colour_id": "Code",
        "schema_ref": "schema:code:v1",
        "schema_digest": "sha256:" + "b" * 64,
        "validator_ref": "validator:code:v1",
        "validator_digest": "sha256:" + "c" * 64,
    }
    operation = {
        "operation_id": "OP_LEGACY",
        "inputs": [port],
        "output": port,
        "authority_effect": "None",
        "authority_ceiling": "None",
        "description": "bounded",
        "effects": [],
        "tool_refs": [],
        "operand_refs": [],
        "lifecycle": {},
        "residual_status": "Open",
        "invocation_grade": "entry",
    }
    raw = json.dumps(operation, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return {
        "nodes": [
            {
                "node_id": "identity",
                "operation_id": "OP_LEGACY",
                "inputs": ["in:0"],
                "outputs": ["out"],
            }
        ],
        "edges": [],
        "typed": {
            "schema_version": "oewas.typed-graph.v1",
            "root_node_id": "identity",
            "pins": [
                {
                    "node_id": "identity",
                    "source_digest": "sha256:" + "a" * 64,
                    "operation_digest": "sha256:" + hashlib.sha256(raw.encode()).hexdigest(),
                }
            ],
            "declarations": [{"source_digest": "sha256:" + "a" * 64, "operation_json": raw}],
            "inputs": [{"node_id": "identity", "slot": 0}],
        },
    }


def _direct_graph(payload):
    from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost

    crossed = RustSymbolGameHost().invoke_runtime("workflow_graph", payload)
    assert crossed.is_ok, crossed
    envelope = crossed.unwrap()
    assert envelope["success"], envelope
    return envelope["result"]


def test_direct_native_typed_port_consumes_pins_and_full_interface():
    reply = _direct_graph(_direct_typed_payload())
    assert reply["refusal"] is None, reply
    assert reply["outcome"]["typed_interface"]["inputs"][0] == [
        "Code",
        "schema:code:v1",
        "sha256:" + "b" * 64,
        "validator:code:v1",
        "sha256:" + "c" * 64,
    ]


@pytest.mark.parametrize("include_null", [False, True])
def test_actual_handler_refuses_missing_or_null_typed_native_reply(monkeypatch, include_null):
    from omega_engine_operations.domain.rop.result import Ok
    from omega_engine_operads.application.dtos.query_dtos import (
        ValidateWorkflowsQuery,
    )
    from omega_engine_operads.application.queries import validate_workflows as owner

    wire = {
        "is_valid": True,
        "node_count": 0,
        "edge_count": 0,
        "cycles": [],
        "execution_stages": [],
        "colour_mismatches": [],
        "orphaned_edges": [],
        "topological_order": [],
        "duplicate_node_ids": [],
    }
    if include_null:
        wire["typed_interface"] = None
    monkeypatch.setattr(
        owner.RustSymbolGameHost,
        "invoke_runtime",
        lambda self, action, payload: Ok(
            {"success": True, "result": {"refusal": None, "outcome": wire}}
        ),
    )
    result = ValidateWorkflowsHandler().handle(ValidateWorkflowsQuery((), (), typed={}))
    assert result.is_err and result.unwrap_err().code == "GRAPH_RESULT_MALFORMED"
    if not include_null:
        assert ValidateWorkflowsHandler().handle(ValidateWorkflowsQuery((), ())).is_ok


@pytest.mark.parametrize(
    "field,code",
    [
        ("source_digest", "SOURCE_DIGEST_MISMATCH"),
        ("operation_digest", "OPERATION_DIGEST_MISMATCH"),
    ],
)
def test_direct_native_stale_pin_refuses(field, code):
    payload = _direct_typed_payload()
    payload["typed"]["pins"][0][field] = "sha256:" + "f" * 64
    assert _direct_graph(payload)["refusal"]["code"] == code


def _add_occurrence(payload, node_id, operation_id, inputs, output):
    operation = json.loads(payload["typed"]["declarations"][0]["operation_json"])
    operation.update(operation_id=operation_id, inputs=inputs, output=output)
    raw = json.dumps(operation, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    payload["nodes"].append(
        {
            "node_id": node_id,
            "operation_id": operation_id,
            "inputs": [f"in:{i}" for i in range(len(inputs))],
            "outputs": ["out"],
        }
    )
    payload["typed"]["pins"].append(
        {
            "node_id": node_id,
            "source_digest": "sha256:" + "a" * 64,
            "operation_digest": "sha256:" + hashlib.sha256(raw.encode()).hexdigest(),
        }
    )
    payload["typed"]["declarations"].append(
        {"source_digest": "sha256:" + "a" * 64, "operation_json": raw}
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_ref", "schema:foreign:v1"),
        ("schema_digest", "sha256:" + "d" * 64),
        ("validator_ref", "validator:foreign:v1"),
        ("validator_digest", "sha256:" + "e" * 64),
    ],
)
def test_direct_native_same_colour_foreign_full_port_refuses(field, value):
    payload = _direct_typed_payload()
    port = json.loads(payload["typed"]["declarations"][0]["operation_json"])["output"]
    _add_occurrence(payload, "producer", "OP_PRODUCER", [], {**port, field: value})
    payload["edges"] = [
        {
            "source_node_id": "producer",
            "source_output": "out",
            "target_node_id": "identity",
            "target_input": "in:0",
        }
    ]
    payload["typed"]["inputs"] = []
    assert _direct_graph(payload)["refusal"]["code"] == "BOUNDARY_MISMATCH"


def test_direct_native_nonzero_original_slot_and_nullary_identity_contract():
    payload = _direct_typed_payload()
    port = json.loads(payload["typed"]["declarations"][0]["operation_json"])["output"]
    left, middle, right = (
        {**port, "name": name, "schema_ref": "schema:" + name + ":v1"}
        for name in ("left", "middle", "right")
    )
    _add_occurrence(payload, "root", "OP_ROOT", [left, middle, right], port)
    _add_occurrence(payload, "constant", "OP_NULLARY", [], middle)
    payload["nodes"] = [node for node in payload["nodes"] if node["node_id"] != "identity"]
    payload["typed"]["pins"] = [p for p in payload["typed"]["pins"] if p["node_id"] != "identity"]
    payload["typed"]["root_node_id"] = "root"
    payload["typed"]["inputs"] = [{"node_id": "root", "slot": 0}, {"node_id": "root", "slot": 2}]
    payload["edges"] = [
        {
            "source_node_id": "constant",
            "source_output": "out",
            "target_node_id": "root",
            "target_input": "in:1",
        }
    ]
    reply = _direct_graph(payload)
    assert reply["refusal"] is None, reply
    interface = reply["outcome"]["typed_interface"]
    assert [p[1] for p in interface["inputs"]] == ["schema:left:v1", "schema:right:v1"]
    assert interface["occurrence_order"] == ["constant", "root"]
    wrong = copy.deepcopy(payload)
    wrong["typed"]["inputs"].reverse()
    assert _direct_graph(wrong)["refusal"]["code"] == "ENTRY_BOUNDARY_MISMATCH"
    unary = _direct_graph(_direct_typed_payload())["outcome"]["typed_interface"]
    assert unary["inputs"][0] == unary["output"]


def test_cycle_in_explicit_occurrence_graph_is_refused_by_real_native_port() -> None:
    workflow = example_workflow(ROOT)
    cycle = replace(
        workflow,
        bindings=workflow.bindings
        + (
            WorkflowBindingV1(
                "audit",
                "falsifier",
                0,
            ),
        ),
        inputs=(),
    )
    observed = []

    def capture_native(query):
        result = ValidateWorkflowsHandler().handle(query)
        assert result.is_ok
        observed.append(result.unwrap())
        return result

    with pytest.raises(WorkflowCompileRefusal) as refusal:
        compile_typed_workflow(
            compile_typed_contracts(ROOT).documents,
            cycle,
            validate_graph=capture_native,
            allowed_effects=EFFECTS,
        )
    assert refusal.value.code == "GRAPH_INVALID"
    assert len(observed) == 1
    assert observed[0].cycles
    assert observed[0].topological_order == ()


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_ref", SchemaRef("schema:foreign:v1")),
        ("schema_digest", ContentDigest.sha256("d" * 64)),
        ("validator_ref", "validator:foreign:v1"),
        ("validator_digest", ContentDigest.sha256("e" * 64)),
    ],
)
def test_same_colour_foreign_contract_cannot_pass_after_native_topology(
    field: str,
    value: object,
) -> None:
    documents = list(compile_typed_contracts(ROOT).documents)
    index = next(
        i
        for i, doc in enumerate(documents)
        if str(doc.operations[0].operation_id) == "woland-claim-audit"
    )
    doc = documents[index]
    operation = doc.operations[0]
    changed = replace(
        operation,
        inputs=(replace(operation.inputs[0], **{field: value}), *operation.inputs[1:]),
    )
    documents[index] = replace(doc, operations=(changed,))
    workflow = example_workflow(ROOT)
    nodes = tuple(
        replace(node, operation_digest=str(operation_content_digest(changed)))
        if node.node_id == "audit"
        else node
        for node in workflow.nodes
    )
    with pytest.raises(PlanRefusal) as refusal:
        compile_typed_workflow(
            tuple(documents),
            replace(workflow, nodes=nodes),
            validate_graph=ValidateWorkflowsHandler().handle,
            allowed_effects=EFFECTS,
        )
    assert refusal.value.code == "BOUNDARY_MISMATCH"


def test_cli_checks_real_workflow_and_keeps_authority_ceiling(tmp_path, capsys) -> None:
    path = tmp_path / "workflow.json"
    path.write_bytes(canonical_workflow_bytes(example_workflow(ROOT)))
    assert (
        main(
            [
                "--repo-root",
                str(ROOT),
                "--workflow",
                str(path),
                "--allow-effect",
                "read_subject",
                "--allow-effect",
                "emit_finding",
            ]
        )
        == 0
    )
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["authority_effect"] == "None"
    assert receipt["admission"] == "Unadmitted"
    assert receipt["runtime_activation"] == "HOLD"
    assert receipt["native_graph_report"]["is_valid"] is True


def test_cli_missing_native_host_is_a_refusal(tmp_path, capsys, monkeypatch) -> None:
    path = tmp_path / "workflow.json"
    path.write_bytes(canonical_workflow_bytes(example_workflow(ROOT)))
    monkeypatch.setenv("OMEGA_SYMBOL_GAME_HOST", str(tmp_path / "absent.exe"))
    assert main(["--repo-root", str(ROOT), "--workflow", str(path)]) == 1
    assert "TYPED_WORKFLOW_REFUSED" in capsys.readouterr().err
