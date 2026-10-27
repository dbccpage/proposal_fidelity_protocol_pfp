"""Actual instruction bytes must bind plan/workflow digests independently of pins.

Compiled aggregates can be supplied by callers. Their declared raw pins are
metadata at this seam; fresh source compilation separately owns raw-file custody.
No native attestation or execution authority is asserted by the graph fixture.
"""

from dataclasses import replace
from pathlib import Path

import pytest

from operations.domain.rop.result import Ok
from workflows_agents_skills.application.commands.compile_catalog import (
    operation_content_digest,
)
from workflows_agents_skills.application.dtos.success_dtos import (
    WorkflowValidationResultDTO,
)
from workflows_agents_skills.application.typed_workflow_compiler import (
    compile_typed_workflow,
)
from workflows_agents_skills.application.adversary_candidate_plan import (
    PlanNodeV01,
    compile_candidate_plan,
)
from workflows_agents_skills.domain.entities.typed_workflow import (
    TypedWorkflowV1,
    WorkflowBindingV1,
    WorkflowInputV1,
    WorkflowNodeV1,
)
from workflows_agents_skills.infrastructure.typed_contract_compiler import (
    compile_typed_contracts,
)

ROOT = next(
    path for path in Path(__file__).resolve().parents if (path / "pyproject.toml").is_file()
)
EFFECTS = frozenset({"read_subject", "emit_finding"})
TREE = PlanNodeV01("adversary-claim-audit", ((0, PlanNodeV01("adversary-scope-falsifier")),))


def _documents(bodies=("Check claim A.", "Check claim B."), *, effectful=False):
    originals = compile_typed_contracts(ROOT).documents
    documents = []
    for document in originals:
        operation = document.operations[0]
        index = 0 if str(operation.operation_id) == "adversary-claim-audit" else 1
        documents.append(
            replace(
                document,
                operands=(replace(document.operands[0], instruction_body=bodies[index]),),
                operations=(replace(operation, effects=operation.effects if effectful else ()),),
            )
        )
    return tuple(documents)


def _workflow(documents):
    by_id = {str(doc.operations[0].operation_id): doc for doc in documents}
    nodes = []
    for node_id, operation_id in (
        ("audit", "adversary-claim-audit"),
        ("falsifier", "adversary-scope-falsifier"),
    ):
        document = by_id[operation_id]
        nodes.append(
            WorkflowNodeV1(
                node_id,
                operation_id,
                str(document.raw_digest),
                str(operation_content_digest(document.operations[0])),
            )
        )
    return TypedWorkflowV1(
        "body-binding",
        "audit",
        tuple(nodes),
        (WorkflowBindingV1("falsifier", "audit", 0),),
        (WorkflowInputV1("falsifier", 0), WorkflowInputV1("audit", 1)),
    )


def _graph_fixture(query):
    return Ok(
        WorkflowValidationResultDTO(
            True,
            len(query.nodes),
            len(query.edges),
            topological_order=("falsifier", "audit"),
            execution_stages=(("falsifier",), ("audit",)),
        )
    )


def _compile(documents, workflow, *, effectful=False):
    effects = EFFECTS if effectful else frozenset()
    candidate = compile_candidate_plan(documents, TREE, allowed_effects=effects)
    compiled = compile_typed_workflow(
        documents,
        workflow,
        validate_graph=_graph_fixture,
        allowed_effects=effects,
    )
    assert compiled.plan == candidate
    assert compiled.plan.admission == "Unadmitted"
    return compiled


@pytest.mark.parametrize("effectful", [False, True])
@pytest.mark.parametrize("changed_index", [0, 1])
def test_equal_length_instruction_transplant_changes_plan_and_workflow_digest(
    effectful,
    changed_index,
):
    original_bodies = ("Check claim A.", "Check claim B.")
    bodies = list(original_bodies)
    bodies[changed_index] = "Check claim C."
    before_documents = _documents(original_bodies, effectful=effectful)
    changed_documents = _documents(tuple(bodies), effectful=effectful)
    workflow = _workflow(before_documents)
    before = _compile(before_documents, workflow, effectful=effectful)
    changed = _compile(changed_documents, workflow, effectful=effectful)

    assert _workflow(changed_documents) == workflow  # All source/operation pins unchanged.
    assert before.plan.source_digests == changed.plan.source_digests
    assert before.plan.instruction_bytes == changed.plan.instruction_bytes
    assert before.plan.ordered_operand_bodies == tuple(reversed(original_bodies))
    assert changed.plan.ordered_operand_bodies == tuple(reversed(bodies))
    assert changed.plan.plan_digest != before.plan.plan_digest
    assert changed.workflow_digest != before.workflow_digest
    assert _compile(before_documents, workflow, effectful=effectful) == before


@pytest.mark.parametrize("effectful", [False, True])
def test_swapped_equal_length_instruction_bodies_do_not_keep_a_digest(effectful):
    original = ("Check claim A.", "Check claim B.")
    before_documents = _documents(original, effectful=effectful)
    swapped_documents = _documents(tuple(reversed(original)), effectful=effectful)
    workflow = _workflow(before_documents)
    before = _compile(before_documents, workflow, effectful=effectful)
    swapped = _compile(swapped_documents, workflow, effectful=effectful)

    assert _workflow(swapped_documents) == workflow
    assert before.plan.source_digests == swapped.plan.source_digests
    assert before.plan.instruction_bytes == swapped.plan.instruction_bytes
    assert sorted(before.plan.ordered_operand_bodies) == sorted(swapped.plan.ordered_operand_bodies)
    assert before.plan.ordered_operand_bodies != swapped.plan.ordered_operand_bodies
    assert before.plan.plan_digest != swapped.plan.plan_digest
    assert before.workflow_digest != swapped.workflow_digest
    assert _compile(before_documents, workflow, effectful=effectful) == before


def test_body_boundaries_are_self_delimiting_and_document_order_is_not_body_order():
    before_documents = _documents(("c", "ab"))
    changed_documents = _documents(("bc", "a"))
    workflow = _workflow(before_documents)
    before = _compile(before_documents, workflow)
    changed = _compile(changed_documents, workflow)

    assert before.plan.ordered_operand_bodies == ("ab", "c")
    assert changed.plan.ordered_operand_bodies == ("a", "bc")
    assert (
        "".join(before.plan.ordered_operand_bodies)
        == "".join(changed.plan.ordered_operand_bodies)
        == "abc"
    )
    assert before.plan.instruction_bytes == changed.plan.instruction_bytes == 3
    assert before.plan.plan_digest != changed.plan.plan_digest
    assert before.workflow_digest != changed.workflow_digest
    assert _compile(tuple(reversed(before_documents)), workflow) == before
