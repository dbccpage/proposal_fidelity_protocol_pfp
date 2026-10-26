"""
Unit tests for the Conversational Repair DAG (Paper 032 Section 7.1).
Reference: Paper 032 (PO-032), claims PO032-C43, PO032-C48.
"""

import pytest

from conversational_repair_dag import (
    ConversationalRepairDAG,
    Event,
    EventType,
    build_example_governed_conversation,
    compute_event_id,
)


def test_content_addressing_is_deterministic_and_sensitive():
    """Identical content yields the same id; any change of content changes it."""
    a = compute_event_id(EventType.PROMPT, "demand", {"k": [1, 2]}, [])
    b = compute_event_id(EventType.PROMPT, "demand", {"k": [1, 2]}, [])
    assert a == b
    assert len(a) == 64  # full SHA-256 hex digest
    # Sensitivity to type, label, payload, and parents independently.
    assert compute_event_id(EventType.RESPONSE, "demand", {"k": [1, 2]}, []) != a
    assert compute_event_id(EventType.PROMPT, "other", {"k": [1, 2]}, []) != a
    assert compute_event_id(EventType.PROMPT, "demand", {"k": [1, 3]}, []) != a
    assert compute_event_id(EventType.PROMPT, "demand", {"k": [1, 2]}, ["p"]) != a


def test_parent_closure_is_fail_closed():
    """Referencing an absent parent is rejected rather than silently linked."""
    dag = ConversationalRepairDAG()
    with pytest.raises(KeyError):
        dag.add_response("orphan", {"x": 1}, parents=["deadbeef" * 8])


def test_dedup_is_idempotent():
    """Adding identical content twice collapses to a single node."""
    dag = ConversationalRepairDAG()
    id1 = dag.add_prompt("demand", {"v": 1})
    id2 = dag.add_prompt("demand", {"v": 1})
    assert id1 == id2
    assert len(dag) == 1


def test_worked_example_verifies_clean():
    """The five-event worked conversation is acyclic with consistent hashes."""
    dag = build_example_governed_conversation()
    report = dag.verify_integrity()
    assert report.ok
    assert report.n_events == 5
    assert report.n_edges == 4          # a linear PROMPT->...->ADMISSION chain
    assert not report.has_cycle
    assert report.hash_mismatches == ()
    assert dag.topological_order() is not None


def test_merkle_history_propagates_to_descendants():
    """Changing an ancestor's payload changes every descendant id."""
    d1 = ConversationalRepairDAG()
    p1 = d1.add_prompt("q", {"v": 1})
    r1 = d1.add_response("a", {}, parents=[p1])

    d2 = ConversationalRepairDAG()
    p2 = d2.add_prompt("q", {"v": 2})
    r2 = d2.add_response("a", {}, parents=[p2])

    assert p1 != p2
    assert r1 != r2  # the ordered-parent digest carries the ancestor change forward


def test_tamper_of_stored_payload_is_detected():
    """A payload mutation that keeps the old key is caught by the hash recheck."""
    dag = build_example_governed_conversation()
    victim = dag.order()[0]
    original = dag.events[victim]
    # Replace the stored event with a mutated payload but the *same* id key.
    dag.events[victim] = Event(
        event_id=victim,
        event_type=original.event_type,
        label=original.label,
        payload={"tampered": True},
        parents=original.parents,
    )
    report = dag.verify_integrity()
    assert not report.ok
    assert victim in report.hash_mismatches


def test_children_and_projected_edges():
    """Child links and projected edges reflect the recorded parent references."""
    dag = ConversationalRepairDAG()
    root = dag.add_prompt("root", {})
    c1 = dag.add_response("c1", {}, parents=[root])
    c2 = dag.add_audit("c2", {}, parents=[root])
    assert set(dag.children_of(root)) == {c1, c2}
    assert dag.projected_edges() == {(root, c1), (root, c2)}


def test_injected_cycle_is_reported():
    """A tampered forward parent reference makes verify_integrity report a cycle."""
    dag = ConversationalRepairDAG()
    a = dag.add_prompt("a", {})
    b = dag.add_response("b", {}, parents=[a])
    # Tamper: rewrite 'a' so it declares 'b' as a parent, forming a 2-cycle.
    dag.events[a] = Event(
        event_id=a,
        event_type=EventType.PROMPT,
        label="a",
        payload={},
        parents=(b,),
    )
    report = dag.verify_integrity()
    assert report.has_cycle
    assert not report.ok
