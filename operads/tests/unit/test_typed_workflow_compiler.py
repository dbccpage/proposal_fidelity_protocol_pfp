"""Public bridge controls; the injected graph oracle is not native evidence."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from omega_engine_operations.domain.rop.result import Err, Ok
from omega_engine_operads.application.commands.compile_catalog import (
    operation_content_digest,
)
from omega_engine_operads.application.dtos.api_error_dto import ApiErrorDTO
from omega_engine_operads.application.dtos.success_dtos import (
    WorkflowValidationResultDTO,
)
from omega_engine_operads.application.typed_workflow_compiler import (
    WorkflowCompileRefusal,
    compile_typed_workflow,
)
from omega_engine_operads.contracts.typed_capabilities_v1 import canonical_bytes
from omega_engine_operads.contracts.typed_workflow_v1 import TypedWorkflowWireV1
from omega_engine_operads.domain.entities.typed_workflow import (
    TypedWorkflowV1,
    WorkflowBindingV1,
    WorkflowInputV1,
    WorkflowNodeV1,
)
from omega_engine_operads.domain.value_objects.content_digest import ContentDigest
from omega_engine_operads.domain.value_objects.lifecycle_facets import (
    ValidationFacet,
)
from omega_engine_operads.infrastructure.typed_contract_compiler import (
    compile_typed_contracts,
)

ROOT = next(
    path for path in Path(__file__).resolve().parents if (path / "pyproject.toml").is_file()
)
EFFECTS = frozenset({"read_subject", "emit_finding"})


def _node(node_id, document):
    return WorkflowNodeV1(
        node_id,
        str(document.operations[0].operation_id),
        str(document.raw_digest),
        str(operation_content_digest(document.operations[0])),
    )


def _example():
    docs = compile_typed_contracts(ROOT).documents
    workflow = TypedWorkflowV1(
        "woland-review",
        "audit",
        tuple(_node(n, doc) for n, doc in zip(("audit", "guard"), docs, strict=True)),
        (WorkflowBindingV1("guard", "audit", 0),),
        (WorkflowInputV1("guard", 0), WorkflowInputV1("audit", 1)),
    )
    return docs, workflow


def _graph(query):
    """Independent small Kahn/colour oracle; does not invoke the native host."""
    remaining = {node.node_id for node in query.nodes}
    by_id = {node.node_id: node for node in query.nodes}
    order, stages, mismatches = [], [], []
    for edge in query.edges:
        source = dict(by_id[edge.source_node_id].output_colours)[edge.source_output]
        target = dict(by_id[edge.target_node_id].input_colours)[edge.target_input]
        if source != target:
            mismatches.append(f"{edge.source_node_id}->{edge.target_node_id}")
    while remaining:
        stage = tuple(
            sorted(
                n
                for n in remaining
                if not any(
                    e.target_node_id == n and e.source_node_id in remaining for e in query.edges
                )
            )
        )
        if not stage:
            return Ok(
                WorkflowValidationResultDTO(
                    False,
                    len(query.nodes),
                    len(query.edges),
                    cycles=(tuple(sorted(remaining)),),
                )
            )
        stages.append(stage)
        order.extend(stage)
        remaining.difference_update(stage)
    return Ok(
        WorkflowValidationResultDTO(
            not mismatches,
            len(query.nodes),
            len(query.edges),
            colour_mismatches=tuple(mismatches),
            topological_order=tuple(order),
            execution_stages=tuple(stages),
        )
    )


def _compile(docs, workflow, **kwargs):
    return compile_typed_workflow(
        docs,
        workflow,
        validate_graph=kwargs.pop("validate_graph", _graph),
        allowed_effects=kwargs.pop("allowed_effects", EFFECTS),
        **kwargs,
    )


def _refuses(code, docs, workflow, **kwargs):
    with pytest.raises(WorkflowCompileRefusal) as raised:
        _compile(docs, workflow, **kwargs)
    assert raised.value.code == code


def test_real_typed_pair_compiles_ordered_unadmitted_candidate():
    docs, workflow = _example()
    observed = []

    def graph_port(query):
        observed.append(query)
        return _graph(query)

    result = _compile(docs, workflow, validate_graph=graph_port)
    assert result.plan.operation_count == 2
    assert result.occurrence_order == ("guard", "audit")
    assert result.plan.operation_ids == ("woland-scope-falsifier", "woland-claim-audit")
    assert tuple(str(port.colour_id) for port in result.plan.inputs) == ("Contract", "Contract")
    assert str(result.plan.output.colour_id) == "Receipt"
    assert result.plan.admission == "Unadmitted"
    assert result.workflow_digest.startswith("sha256:") and len(result.workflow_digest) == 71
    assert observed[0].edges[0].source_output == "out"
    assert observed[0].edges[0].target_input == "in:0"
    assert observed[0].nodes[0].input_colours == (("in:0", "Audit"), ("in:1", "Contract"))
    assert result.native_report == _graph(observed[0]).value
    assert result.plan.ordered_operand_bodies == (
        docs[1].operands[0].instruction_body,
        docs[0].operands[0].instruction_body,
    )


@pytest.mark.parametrize(
    "pin,code",
    [
        ("source_digest", "SOURCE_DIGEST_MISMATCH"),
        ("operation_digest", "OPERATION_DIGEST_MISMATCH"),
    ],
)
def test_stale_pins_refuse_before_calling_native(pin, code):
    docs, workflow = _example()
    node = replace(workflow.nodes[1], **{pin: "sha256:" + "f" * 64})
    called = []
    _refuses(
        code,
        docs,
        replace(workflow, nodes=(workflow.nodes[0], node)),
        validate_graph=lambda query: called.append(query),
    )
    assert called == []


@pytest.mark.parametrize(
    "kind,code",
    [
        ("duplicate", "DUPLICATE_NODE_ID"),
        ("missing-root", "ROOT_NODE_MISSING"),
        ("unknown-operation", "OPERATION_MISSING"),
        ("unknown-source", "BINDING_NODE_MISSING"),
        ("unknown-target", "BINDING_NODE_MISSING"),
        ("bad-slot", "SLOT_OUT_OF_BOUNDS"),
        ("duplicate-slot", "DUPLICATE_SLOT_BINDING"),
    ],
)
def test_invalid_graph_declarations_refuse(kind, code):
    docs, workflow = _example()
    if kind == "duplicate":
        workflow = replace(workflow, nodes=workflow.nodes + (workflow.nodes[0],))
    elif kind == "missing-root":
        workflow = replace(workflow, root_node_id="missing")
    elif kind == "unknown-operation":
        workflow = replace(
            workflow, nodes=(replace(workflow.nodes[0], operation_id="missing"), workflow.nodes[1])
        )
    elif kind == "unknown-source":
        workflow = replace(workflow, bindings=(WorkflowBindingV1("missing", "audit", 0),))
    elif kind == "unknown-target":
        workflow = replace(workflow, bindings=(WorkflowBindingV1("guard", "missing", 0),))
    elif kind == "bad-slot":
        workflow = replace(workflow, bindings=(WorkflowBindingV1("guard", "audit", 127),))
    else:
        workflow = replace(workflow, bindings=workflow.bindings + workflow.bindings)
    _refuses(code, docs, workflow)


@pytest.mark.parametrize(
    "entries",
    [
        (WorkflowInputV1("audit", 1), WorkflowInputV1("guard", 0)),
        (WorkflowInputV1("guard", 0),),
        (WorkflowInputV1("guard", 0), WorkflowInputV1("audit", 1), WorkflowInputV1("guard", 0)),
        (WorkflowInputV1("guard", 0), WorkflowInputV1("audit", 0)),
    ],
)
def test_equal_colour_entry_reordering_missing_extra_and_bound_slots_refuse(entries):
    docs, workflow = _example()
    _refuses("ENTRY_BOUNDARY_MISMATCH", docs, replace(workflow, inputs=entries))


def _repeated(count=2):
    """Synthetic bound unary endomorphism, derived from real compiled ports."""
    docs, _ = _example()
    guard = docs[1]
    op = guard.operations[0]
    guard = replace(guard, operations=(replace(op, inputs=(op.output,)),))
    docs = (docs[0], guard)
    nodes = (_node("audit", docs[0]),) + tuple(_node(f"guard-{i}", guard) for i in range(count))
    bindings = (WorkflowBindingV1("guard-0", "audit", 0),) + tuple(
        WorkflowBindingV1(f"guard-{i}", f"guard-{i - 1}", 0) for i in range(1, count)
    )
    workflow = TypedWorkflowV1(
        "finite-repeat",
        "audit",
        nodes,
        bindings,
        (WorkflowInputV1(f"guard-{count - 1}", 0), WorkflowInputV1("audit", 1)),
    )
    return docs, workflow


def test_finite_repeated_operation_has_fresh_occurrences_and_bound_digest():
    docs, workflow = _repeated()
    result = _compile(docs, workflow)
    assert result.occurrence_order == ("guard-1", "guard-0", "audit")
    assert result.plan.operation_count == 3
    assert result.plan.operation_ids == (
        "woland-scope-falsifier",
        "woland-scope-falsifier",
        "woland-claim-audit",
    )
    assert result.plan.ordered_operand_bodies[0] == result.plan.ordered_operand_bodies[1]
    renamed = replace(workflow, workflow_id="finite-repeat-other")
    assert _compile(docs, renamed).workflow_digest != result.workflow_digest
    assert _compile(docs, renamed).plan.plan_digest == result.plan.plan_digest


def test_shared_output_refuses_instead_of_duplicating_a_logical_occurrence():
    docs, workflow = _repeated()
    # The same guard-1 output would feed both guard-0 and the root.
    root = docs[0].operations[0]
    docs = (
        replace(docs[0], operations=(replace(root, inputs=(root.inputs[0], root.inputs[0])),)),
        docs[1],
    )
    workflow = replace(
        workflow,
        nodes=(_node("audit", docs[0]), *workflow.nodes[1:]),
        bindings=workflow.bindings + (WorkflowBindingV1("guard-1", "audit", 1),),
    )
    _refuses("SHARED_OUTPUT_UNSUPPORTED", docs, workflow)


def test_unreachable_declared_node_refuses():
    docs, workflow = _repeated()
    extra = _node("orphan", docs[1])
    _refuses("UNREACHABLE_NODE", docs, replace(workflow, nodes=workflow.nodes + (extra,)))


def test_native_cycle_and_colour_refusals_are_not_lowered():
    docs, workflow = _repeated()
    cycle = replace(
        workflow,
        bindings=(
            WorkflowBindingV1("guard-0", "guard-1", 0),
            WorkflowBindingV1("guard-1", "guard-0", 0),
        ),
    )
    _refuses("GRAPH_INVALID", docs, cycle)
    docs, workflow = _example()
    wrong_colour = replace(workflow, bindings=(WorkflowBindingV1("guard", "audit", 1),))
    _refuses("GRAPH_INVALID", docs, wrong_colour)


@pytest.mark.parametrize(
    "field,value",
    [
        ("is_valid", 1),
        ("node_count", True),
        ("node_count", 3),
        ("edge_count", 0),
        ("topological_order", ["guard", "audit"]),
        ("topological_order", ("audit",)),
        ("topological_order", ("guard", "guard")),
        ("execution_stages", (("guard", "audit"),)),
        ("execution_stages", (("audit",), ("guard",))),
        ("execution_stages", (("guard",), (), ("audit",))),
        ("execution_stages", [["guard"], ["audit"]]),
        ("cycles", ((),)),
        ("colour_mismatches", (False,)),
        ("orphaned_edges", ("x" * 2049,)),
    ],
)
def test_malformed_positive_native_reports_fail_closed(field, value):
    docs, workflow = _example()
    report = WorkflowValidationResultDTO(
        True, 2, 1, topological_order=("guard", "audit"), execution_stages=(("guard",), ("audit",))
    )
    _refuses(
        "GRAPH_RESULT_MALFORMED",
        docs,
        workflow,
        validate_graph=lambda query: Ok(replace(report, **{field: value})),
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("is_valid", False),
        ("cycles", (("guard", "audit"),)),
        ("colour_mismatches", ("mismatch",)),
        ("orphaned_edges", ("orphan",)),
        ("duplicate_node_ids", ("guard",)),
    ],
)
def test_well_shaped_native_negative_report_never_promotes(field, value):
    docs, workflow = _example()
    report = WorkflowValidationResultDTO(
        True, 2, 1, topological_order=("guard", "audit"), execution_stages=(("guard",), ("audit",))
    )
    _refuses(
        "GRAPH_INVALID",
        docs,
        workflow,
        validate_graph=lambda query: Ok(replace(report, **{field: value})),
    )


@pytest.mark.parametrize(
    "reply", [None, True, {}, Ok({}), Err("synthetic error"), Err(ApiErrorDTO("lowercase", "bad"))]
)
def test_malformed_result_envelopes_refuse(reply):
    docs, workflow = _example()
    _refuses("GRAPH_RESULT_MALFORMED", docs, workflow, validate_graph=lambda query: reply)


def test_native_unavailable_and_typed_refusal_preserve_failure():
    docs, workflow = _example()

    def unavailable(query):
        raise OSError("host unavailable")

    _refuses("GRAPH_VALIDATOR_UNAVAILABLE", docs, workflow, validate_graph=unavailable)
    _refuses("GRAPH_VALIDATOR_UNAVAILABLE", docs, workflow, validate_graph=None)
    _refuses(
        "HOST_INPUT_BINDING_MISMATCH",
        docs,
        workflow,
        validate_graph=lambda query: Err(ApiErrorDTO("HOST_INPUT_BINDING_MISMATCH", "wrong input")),
    )


def test_forged_positive_report_cannot_bless_a_cycle():
    docs, workflow = _repeated()
    workflow = replace(
        workflow,
        bindings=(
            WorkflowBindingV1("guard-0", "guard-1", 0),
            WorkflowBindingV1("guard-1", "guard-0", 0),
        ),
    )
    report = WorkflowValidationResultDTO(
        True,
        3,
        2,
        topological_order=("guard-1", "guard-0", "audit"),
        execution_stages=(("guard-1",), ("guard-0",), ("audit",)),
    )
    _refuses("GRAPH_RESULT_MALFORMED", docs, workflow, validate_graph=lambda query: Ok(report))


@pytest.mark.parametrize(
    "field", ["schema_ref", "schema_digest", "validator_ref", "validator_digest"]
)
def test_same_colour_foreign_contract_is_rejected_by_existing_candidate_compiler(field):
    docs, workflow = _example()
    op = docs[1].operations[0]
    values = {
        "schema_ref": type(op.output.schema_ref)("schema:foreign:v1"),
        "schema_digest": ContentDigest.sha256("a" * 64),
        "validator_ref": "foreign.validator",
        "validator_digest": ContentDigest.sha256("b" * 64),
    }
    foreign = replace(op.output, **{field: values[field]})
    docs = (docs[0], replace(docs[1], operations=(replace(op, output=foreign),)))
    workflow = replace(workflow, nodes=(workflow.nodes[0], _node("guard", docs[1])))
    _refuses("BOUNDARY_MISMATCH", docs, workflow)


def test_capability_and_lifecycle_checks_remain_in_candidate_compiler():
    docs, workflow = _example()
    _refuses("EFFECT_NOT_LICENSED", docs, workflow, allowed_effects=frozenset())


def test_candidate_refusal_message_keeps_one_code_prefix():
    docs, workflow = _example()
    with pytest.raises(WorkflowCompileRefusal) as raised:
        _compile(docs, workflow, allowed_effects=frozenset())
    message = str(raised.value)
    assert message.startswith("EFFECT_NOT_LICENSED: ")
    assert message.count("EFFECT_NOT_LICENSED") == 1
    op = docs[1].operations[0]
    lifecycle = replace(op.lifecycle, validation=ValidationFacet.UNCHECKED)
    changed = replace(docs[1], operations=(replace(op, lifecycle=lifecycle),))
    workflow = replace(workflow, nodes=(workflow.nodes[0], _node("guard", changed)))
    _refuses("OPERATION_UNBOUND", (docs[0], changed), workflow)


def test_declaration_order_is_normalized_but_source_and_occurrence_pins_bind_digest():
    docs, workflow = _repeated()
    first = _compile(docs, workflow)
    reordered = replace(
        workflow, nodes=tuple(reversed(workflow.nodes)), bindings=tuple(reversed(workflow.bindings))
    )
    assert _compile(docs, reordered).workflow_digest == first.workflow_digest
    renamed = replace(
        workflow,
        root_node_id="audit-other",
        nodes=(replace(workflow.nodes[0], node_id="audit-other"), *workflow.nodes[1:]),
        bindings=tuple(
            replace(b, target_node_id="audit-other") if b.target_node_id == "audit" else b
            for b in workflow.bindings
        ),
        inputs=tuple(
            replace(p, node_id="audit-other") if p.node_id == "audit" else p
            for p in workflow.inputs
        ),
    )
    assert _compile(docs, renamed).workflow_digest != first.workflow_digest
    changed = replace(docs[1], raw_digest=ContentDigest.sha256("c" * 64))
    repinned = replace(
        workflow, nodes=(workflow.nodes[0], _node("guard-0", changed), _node("guard-1", changed))
    )
    assert _compile((docs[0], changed), repinned).workflow_digest != first.workflow_digest


def test_workflow_digest_matches_explicit_profile_and_plan_binding_oracle():
    docs, workflow = _example()
    result = _compile(docs, workflow)
    normalized = replace(workflow, nodes=tuple(sorted(workflow.nodes, key=lambda n: n.node_id)))
    payload = {
        "schema_version": "oewas.compiled-workflow.v1",
        "workflow": TypedWorkflowWireV1.from_domain(normalized).model_dump(mode="json"),
        "plan_digest": result.plan.plan_digest,
    }
    assert (
        result.workflow_digest == "sha256:" + hashlib.sha256(canonical_bytes(payload)).hexdigest()
    )


def test_native_callback_cannot_mutate_caller_inputs_into_compiled_snapshot():
    docs, workflow = _example()
    expected = _compile(docs, workflow)

    def mutating_port(query):
        docs[1].raw_digest = ContentDigest.sha256("d" * 64)
        docs[1].operations = ()
        object.__setattr__(workflow.nodes[1], "source_digest", "sha256:" + "e" * 64)
        return _graph(query)

    observed = _compile(docs, workflow, validate_graph=mutating_port)
    assert observed == expected
    assert docs[1].operations == ()  # mutation happened, but not to the compiled snapshot


@pytest.mark.parametrize(
    "target,field,value",
    [
        ("workflow", "nodes", []),
        ("workflow", "inputs", []),
        ("node", "node_id", "UPPER"),
        ("node", "source_digest", 123),
        ("binding", "target_slot", True),
        ("input", "slot", -1),
    ],
)
def test_tampered_frozen_carriers_revalidate_exact_types(target, field, value):
    docs, workflow = _example()
    carrier = {
        "workflow": workflow,
        "node": workflow.nodes[1],
        "binding": workflow.bindings[0],
        "input": workflow.inputs[0],
    }[target]
    object.__setattr__(carrier, field, value)
    _refuses("WORKFLOW_SHAPE_INVALID", docs, workflow)


@pytest.mark.parametrize("documents", [None, (), [], (object(),)])
def test_malformed_sources_refuse_typed(documents):
    _, workflow = _example()
    _refuses("SOURCE_SHAPE_INVALID", documents, workflow)


def test_existing_candidate_depth_budget_still_bounds_finite_repetition():
    docs, workflow = _repeated(16)
    _refuses("COMPOSITION_BUDGET_EXCEEDED", docs, workflow)


def test_equal_length_compiled_operand_change_binds_plan_and_workflow_digests():
    docs, workflow = _example()
    original = _compile(docs, workflow)
    operand = docs[1].operands[0]
    body = ("Y" if operand.instruction_body.startswith("X") else "X") + operand.instruction_body[1:]
    assert len(body.encode("utf-8")) == len(operand.instruction_body.encode("utf-8"))
    changed = replace(docs[1], operands=(replace(operand, instruction_body=body),))
    observed = _compile((docs[0], changed), workflow)
    assert observed.plan.ordered_operand_bodies != original.plan.ordered_operand_bodies
    assert observed.plan.plan_digest != original.plan.plan_digest
    assert observed.workflow_digest != original.workflow_digest
    assert observed.plan.admission == "Unadmitted"
