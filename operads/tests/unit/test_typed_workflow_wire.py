"""The explicit workflow wire is strict, bounded and lossless at the domain seam."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest


def _payload() -> dict:
    return {
        "schema_version": "oewas.typed-workflow.v1",
        "canonicalization_profile": "oewas.sorted-ascii-json.v1",
        "authority_effect": "None",
        "workflow_id": "audit-workflow",
        "root_node_id": "audit",
        "nodes": [
            {
                "node_id": "audit",
                "operation_id": "adversary-claim-audit",
                "source_digest": "sha256:" + "a" * 64,
                "operation_digest": "sha256:" + "b" * 64,
            }
        ],
        "bindings": [],
        "inputs": [{"node_id": "audit", "slot": 0}],
    }


def _parse(payload: dict):
    from operads.contracts.typed_workflow_v1 import (
        parse_typed_workflow,
    )

    return parse_typed_workflow(json.dumps(payload).encode("utf-8"))


def test_wire_roundtrip_retains_pins_and_ordered_open_ports() -> None:
    from operads.contracts.typed_workflow_v1 import (
        TypedWorkflowWireV1,
        canonical_workflow_bytes,
        parse_typed_workflow,
    )

    wire = _parse(_payload())
    domain = wire.to_domain()
    assert domain.workflow_id == "audit-workflow"
    assert domain.inputs[0].node_id == "audit"
    assert domain.nodes[0].source_digest == "sha256:" + "a" * 64
    assert TypedWorkflowWireV1.from_domain(domain) == wire
    raw = canonical_workflow_bytes(domain)
    assert raw.endswith(b"\n")
    assert parse_typed_workflow(raw).to_domain() == domain


@pytest.mark.parametrize(
    "operation_id", ["OP_LEGACY:route.1", "legacy.operation_name", "legacy/operation"]
)
def test_legacy_operation_ids_remain_distinct_from_occurrence_ids(operation_id):
    payload = _payload()
    payload["nodes"][0]["operation_id"] = operation_id
    assert _parse(payload).to_domain().nodes[0].operation_id == operation_id
    payload["nodes"][0]["node_id"] = operation_id
    with pytest.raises(ValueError):
        _parse(payload)


@pytest.mark.parametrize("operation_id", [" ", " leading", "trailing ", "x" * 513])
def test_operation_ids_do_not_silently_trim_or_exceed_the_existing_carrier(operation_id):
    payload = _payload()
    payload["nodes"][0]["operation_id"] = operation_id
    with pytest.raises(ValueError):
        _parse(payload)


@pytest.mark.parametrize(
    "field,value",
    [
        ("authority_effect", "EXECUTE"),
        ("schema_version", "future"),
        ("canonicalization_profile", "RFC8785"),
        ("workflow_id", "../escape"),
        ("root_node_id", 3),
        ("unknown", True),
        ("nodes", []),
    ],
)
def test_wire_refuses_wrong_versions_authority_and_shape(field: str, value: object) -> None:
    data = _payload()
    data[field] = value
    with pytest.raises(ValueError):
        _parse(data)


@pytest.mark.parametrize("slot", [True, -1, 128, "0", 0.0])
def test_slots_are_bounded_exact_integers(slot: object) -> None:
    data = _payload()
    data["inputs"][0]["slot"] = slot
    with pytest.raises(ValueError):
        _parse(data)


@pytest.mark.parametrize("pin", ["a" * 64, "sha256:" + "A" * 64, "sha256:abc"])
def test_source_pins_have_one_exact_profile(pin: str) -> None:
    data = _payload()
    data["nodes"][0]["source_digest"] = pin
    with pytest.raises(ValueError):
        _parse(data)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"nodes":[],"nodes":[]}',
        b'{"x":NaN}',
        b"\xff",
        b"{}" * 70000,
    ],
    ids=["duplicate", "nonfinite", "invalid-utf8", "oversized"],
)
def test_parser_rejects_ambiguous_nonfinite_invalid_or_oversized_bytes(raw: bytes) -> None:
    from operads.contracts.typed_workflow_v1 import (
        parse_typed_workflow,
    )

    with pytest.raises(ValueError):
        parse_typed_workflow(raw)


def test_domain_cannot_bypass_exact_types_and_collection_bounds() -> None:
    domain = _parse(_payload()).to_domain()
    with pytest.raises(ValueError):
        replace(domain, nodes=list(domain.nodes))
    with pytest.raises(ValueError):
        replace(domain.inputs[0], slot=True)
    with pytest.raises(ValueError):
        replace(domain, nodes=domain.nodes * 129)
    with pytest.raises(ValueError):
        replace(domain, inputs=(object(),))
    assert hash(domain) == hash(_parse(_payload()).to_domain())
    assert domain != object()


def test_deeply_nested_bounded_json_has_a_normal_validation_refusal() -> None:
    from operads.contracts.typed_workflow_v1 import (
        parse_typed_workflow,
    )

    raw = b"[" * 20000 + b"0" + b"]" * 20000
    with pytest.raises(ValueError):
        parse_typed_workflow(raw)


@pytest.mark.parametrize(
    "key,value",
    [
        ("authority_effect", "None"),
        ("node_id", "audit"),
    ],
)
def test_duplicate_key_in_otherwise_valid_workflow_is_refused(key: str, value: str) -> None:
    from operads.contracts.typed_workflow_v1 import (
        parse_typed_workflow,
    )

    raw = json.dumps(_payload())
    entry = json.dumps(key) + ": " + json.dumps(value)
    raw = raw.replace(entry, entry + ", " + entry, 1)
    with pytest.raises(ValueError, match="duplicate JSON key"):
        parse_typed_workflow(raw.encode("utf-8"))
