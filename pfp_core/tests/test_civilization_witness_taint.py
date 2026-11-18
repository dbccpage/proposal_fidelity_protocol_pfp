"""PCIV taint travels only over witnessed inheritance edges.

Review findings (2026-11-17, PFP 2c5526f1 and the anomalon copy at 412505bf):

* ``Lineage.taint`` sent ``getattr(edge, "witness", "sha256:00")`` to the native host,
  but ``LineageEdgeV1`` stores ``witness_receipt``, so every edge carried the
  placeholder ``sha256:00`` and the host never saw the sealed witness.
* Both the native transport and the Python fallback propagated over every edge,
  so a ``RetrievedPrecedent`` reference edge tainted its reader.

Each test runs on the Python fallback and on the native ``pfp_immune`` host
(``PFP_IMMUNE_BIN`` or ``code/rust/target/debug/pfp_immune``).

AuthorityEffect: None.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from pciv.domain.causal_witness import SealedCausalWitness, seal_causal_witness
from pciv.use_cases.genealogy import RelationshipType
from pfp_core import civilization, immune_host

NATIVE = Path(__file__).resolve().parents[2] / "code" / "rust" / "target" / "debug" / "pfp_immune"


def _use_native(monkeypatch) -> None:
    if not immune_host.is_available():
        if not NATIVE.is_file():
            pytest.fail(f"native pfp_immune is not built at {NATIVE}")
        monkeypatch.setenv(immune_host.ENVIRONMENT, str(NATIVE))
    assert immune_host.is_available()


@pytest.fixture(params=["fallback", "native"])
def mode(request, monkeypatch):
    if request.param == "fallback":
        monkeypatch.setattr(immune_host, "is_available", lambda: False)
    else:
        _use_native(monkeypatch)
    return request.param


def _lineage() -> civilization.Lineage:
    lineage = civilization.Lineage()
    lineage.derive("parent", "child", "bounded repair")
    lineage.derive("child", "grandchild", "retry")
    lineage.graph.add_edge("parent", "precedent_reader", RelationshipType.RETRIEVED_PRECEDENT)
    lineage.graph.add_edge("child", "second_reader", RelationshipType.RETRIEVED_PRECEDENT)
    return lineage


def test_native_transport_carries_the_actual_sealed_witness(monkeypatch):
    lineage = civilization.Lineage()
    lineage.derive("parent", "child", "bounded repair")
    observed = {}
    monkeypatch.setattr(immune_host, "is_available", lambda: True)
    monkeypatch.setattr(
        immune_host, "taint",
        lambda edges, seeds: observed.update(edges=edges) or {"tainted_nodes": ["parent", "child"]},
    )
    lineage.taint({"parent"})
    witness = lineage.graph.edges[0].witness_receipt
    assert observed["edges"] == [{
        "parent": "parent", "child": "child",
        "witness": witness.receipt_sha256, "witness_body": witness.canonical_body,
        "relationship": "DirectMutation",
    }]


def test_reference_edges_carry_no_taint(mode):
    assert _lineage().taint({"parent"}) == {"parent", "child", "grandchild"}


def test_reader_of_a_tainted_precedent_is_not_tainted(mode):
    assert _lineage().taint({"child"}) == {"child", "grandchild"}


def _tamper(lineage: civilization.Lineage, index: int, witness) -> None:
    edges = lineage.graph._edges
    edges[index] = dataclasses.replace(edges[index], witness_receipt=witness)


def _forged(body: str) -> SealedCausalWitness:
    """A witness whose digest no longer matches its body, built past the constructor check."""
    witness = seal_causal_witness({"parent_id": "parent", "child_id": "child", "change": "x"})
    object.__setattr__(witness, "canonical_body", body)
    return witness


@pytest.mark.parametrize(
    "witness",
    [
        pytest.param(None, id="missing"),
        pytest.param({"receipt_sha256": "sha256:00"}, id="caller-dict"),
        pytest.param(_forged('{"child_id":"child","parent_id":"parent","change":"y"}'), id="altered"),
        pytest.param(seal_causal_witness({"parent_id": "other", "child_id": "child"}), id="wrong-parent"),
        pytest.param(seal_causal_witness({"parent_id": "parent", "child_id": "other"}), id="wrong-child"),
    ],
)
def test_unwitnessed_inheritance_edge_refuses(mode, witness):
    lineage = _lineage()
    _tamper(lineage, 0, witness)
    with pytest.raises(ValueError, match="CAUSAL_WITNESS_REQUIRED"):
        lineage.taint({"parent"})


def test_placeholder_digest_refuses(mode):
    lineage = _lineage()
    witness = seal_causal_witness({"parent_id": "parent", "child_id": "child"})
    object.__setattr__(witness, "receipt_sha256", "sha256:causal_witness_ok")
    _tamper(lineage, 0, witness)
    with pytest.raises(ValueError, match="CAUSAL_WITNESS_REQUIRED"):
        lineage.taint({"parent"})


def test_native_host_refuses_a_placeholder_witness_directly(monkeypatch):
    _use_native(monkeypatch)
    refused = immune_host.taint([{"parent": "p", "child": "c", "witness": "sha256:00"}], ["p"])
    assert refused["status"] == "REFUSED"
    assert refused["reason"].startswith("CAUSAL_WITNESS_REQUIRED")
    body = json.dumps({"child_id": "c", "parent_id": "p"}, sort_keys=True, separators=(",", ":"))
    assert "tainted_nodes" in immune_host.taint(
        [{"parent": "p", "child": "c", "witness": seal_causal_witness(json.loads(body)).receipt_sha256,
          "witness_body": body}],
        ["p"],
    )


def test_an_unknown_relationship_refuses(mode):
    lineage = _lineage()
    object.__setattr__(lineage.graph._edges[0], "relationship", "Inspired")
    with pytest.raises(ValueError, match="CAUSAL_WITNESS_REQUIRED: 'Inspired' is not a PCIV relation"):
        lineage.taint({"parent"})


def test_a_native_refusal_is_raised_not_swallowed(monkeypatch):
    monkeypatch.setattr(immune_host, "is_available", lambda: True)
    monkeypatch.setattr(
        immune_host, "taint",
        lambda edges, seeds: {"status": "REFUSED", "reason": "LINEAGE_CYCLE_REFUSED: parent -> child"},
    )
    with pytest.raises(ValueError, match="LINEAGE_CYCLE_REFUSED: parent -> child"):
        _lineage().taint({"parent"})
