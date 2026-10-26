"""Public typed workflow command: canonical example, native check, typed refusal."""

from __future__ import annotations

import json
from pathlib import Path


def test_cli_emits_example_bound_to_current_typed_contracts(capsys) -> None:
    from omega_engine_operads.contracts.typed_workflow_v1 import (
        parse_typed_workflow,
    )
    from omega_engine_operads.infrastructure.typed_workflow_compiler import main

    root = Path(__file__).resolve().parents[3]
    assert main(["--repo-root", str(root), "--emit-example"]) == 0
    output = capsys.readouterr().out
    workflow = parse_typed_workflow(output.encode("utf-8")).to_domain()
    assert workflow.root_node_id == "audit"
    assert tuple(node.operation_id for node in workflow.nodes) == (
        "woland-claim-audit",
        "woland-scope-falsifier",
    )
    assert workflow.bindings[0].target_slot == 0
    assert workflow.inputs[0].node_id == "falsifier"
    assert tuple((port.node_id, port.slot) for port in workflow.inputs) == (
        ("falsifier", 0),
        ("audit", 1),
    )


def test_cli_emits_versioned_schema(capsys) -> None:
    from omega_engine_operads.infrastructure.typed_workflow_compiler import main

    assert main(["--repo-root", ".", "--show-schema"]) == 0
    schema = json.loads(capsys.readouterr().out)
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == "oewas.typed-workflow.v1"


def test_cli_malformed_workflow_refuses_before_native_dispatch(tmp_path, capsys) -> None:
    from omega_engine_operads.infrastructure.typed_workflow_compiler import main

    workflow = tmp_path / "bad.json"
    workflow.write_bytes(b'{"nodes":[],"nodes":[]}')
    assert main(["--repo-root", ".", "--workflow", str(workflow)]) == 1
    assert "TYPED_WORKFLOW_REFUSED" in capsys.readouterr().err
