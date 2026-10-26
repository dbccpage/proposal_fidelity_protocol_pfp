"""Compile explicit workflows through the existing native graph and typed plan ports."""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

from ..application.commands.compile_catalog import operation_content_digest
from ..application.queries.validate_workflows import ValidateWorkflowsHandler
from ..contracts.typed_capabilities_v1 import canonical_bytes
from ..contracts.typed_workflow_v1 import (
    TypedWorkflowWireV1,
    canonical_workflow_bytes,
    parse_typed_workflow,
)
from ..domain.entities.typed_workflow import (
    TypedWorkflowV1,
    WorkflowBindingV1,
    WorkflowInputV1,
    WorkflowNodeV1,
)
from .typed_contract_compiler import compile_typed_contracts


def example_workflow(repo_root: Path) -> TypedWorkflowV1:
    """Create an explicit new declaration; never repin an existing workflow."""
    bundle = compile_typed_contracts(repo_root)
    by_id = {str(doc.operations[0].operation_id): doc for doc in bundle.documents}
    nodes = []
    for node_id, operation_id in (
        ("audit", "woland-claim-audit"),
        ("falsifier", "woland-scope-falsifier"),
    ):
        doc = by_id[operation_id]
        nodes.append(
            WorkflowNodeV1(
                node_id,
                operation_id,
                str(doc.raw_digest),
                str(operation_content_digest(doc.operations[0])),
            )
        )
    return TypedWorkflowV1(
        "woland-claim-audit-workflow",
        "audit",
        tuple(nodes),
        (WorkflowBindingV1("falsifier", "audit", 0),),
        (WorkflowInputV1("falsifier", 0), WorkflowInputV1("audit", 1)),
    )


def _compile_receipt(
    root: Path,
    workflow_path: Path,
    allowed_effects: frozenset[str],
    allowed_tool_refs: frozenset[str],
) -> dict:
    workflow = parse_typed_workflow(workflow_path.read_bytes()).to_domain()
    from ..application.typed_workflow_compiler import compile_typed_workflow
    from ..application.woland_candidate_plan import port_contract

    bundle = compile_typed_contracts(root)
    selected_ids = {node.operation_id for node in workflow.nodes}
    compiled = compile_typed_workflow(
        tuple(
            doc
            for doc in bundle.all_documents
            if str(doc.operations[0].operation_id) in selected_ids
        ),
        workflow,
        validate_graph=ValidateWorkflowsHandler().handle,
        allowed_effects=allowed_effects,
        allowed_tool_refs=allowed_tool_refs,
    )
    return {
        "schema_version": "oewas.typed-workflow-check.v1",
        "authority_effect": "None",
        "admission": compiled.plan.admission,
        "runtime_activation": "HOLD",
        "workflow_digest": compiled.workflow_digest,
        "plan_digest": compiled.plan.plan_digest,
        "contracts_digest": bundle.contracts_digest,
        "occurrence_order": compiled.occurrence_order,
        "inputs": [port_contract(port) for port in compiled.plan.inputs],
        "output": port_contract(compiled.plan.output),
        "native_graph_report": asdict(compiled.native_report),
        "native_source_binding": "not_attested_by_this_command",
        "evidence_grade": "FINITE_TYPED_INSTRUCTION_GRAPH",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--allow-effect", action="append", default=[])
    parser.add_argument("--allow-tool", action="append", default=[])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit-example", action="store_true")
    mode.add_argument("--show-schema", action="store_true")
    mode.add_argument("--workflow", type=Path)
    args = parser.parse_args(argv)
    try:
        root = args.repo_root.absolute()
        if args.emit_example:
            raw = canonical_workflow_bytes(example_workflow(root))
        elif args.show_schema:
            raw = canonical_bytes(TypedWorkflowWireV1.model_json_schema())
        else:
            raw = canonical_bytes(
                _compile_receipt(
                    root,
                    args.workflow,
                    frozenset(args.allow_effect),
                    frozenset(args.allow_tool),
                )
            )
        print(raw.decode("ascii"), end="")
    except (ValueError, TypeError, OSError, KeyError) as exc:
        print(f"TYPED_WORKFLOW_REFUSED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
