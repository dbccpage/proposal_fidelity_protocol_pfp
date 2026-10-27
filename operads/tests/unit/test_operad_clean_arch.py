"""
Unit Tests for OEWAS Coloured Operad Domain & Clean Architecture Invariants.
============================================================================

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from operads.domain.operad import (
    ADMITTED_FINITE_COLOURS,
    AgentSlice,
    ArityMismatchError,
    Colour,
    ColourSignature,
    ColouredOperad,
    Err,
    IllTypedCompositionError,
    InvalidColourError,
    Ok,
    OperationId,
    OperationSignature,
    PlanarTree,
    TreeCompositionWitness,
)


def test_colour_creation_and_exact_equality():
    c_code1 = Colour("Code")
    c_code2 = Colour("Code")
    c_audit = Colour("Audit")

    assert c_code1 == c_code2
    assert hash(c_code1) == hash(c_code2)
    assert c_code1 != c_audit
    assert c_code1 != "Code"  # Value Object exact-type equality guard

    with pytest.raises(ValueError):
        Colour("InvalidColourName")


def test_operation_signature_properties():
    sig = ColourSignature(source=["Code", "Audit"], target="Receipt")
    assert sig.arity == 2
    assert not sig.is_nullary
    assert str(sig) == "(Code, Audit) -> Receipt"

    op = OperationSignature(
        op_id=OperationId("test_op"),
        signature=sig,
    )
    assert op.arity == 2
    assert op.source_colours == ("Code", "Audit")
    assert op.target_colour == "Receipt"


def test_coloured_operad_ensure_units():
    operad = ColouredOperad()
    units = operad.ensure_units()
    assert len(units) == len(ADMITTED_FINITE_COLOURS)
    for c in ADMITTED_FINITE_COLOURS:
        assert f"id_{c}" in operad.operations
        unit_op = operad.operations[f"id_{c}"]
        assert unit_op.arity == 1
        assert unit_op.source[0].name == c
        assert unit_op.target.name == c


def test_partial_composition_success_and_failure():
    operad = ColouredOperad()
    f = OperationSignature(
        op_id=OperationId("f_eval"),
        signature=ColourSignature(source=["Code", "Audit"], target="Receipt"),
    )
    g = OperationSignature(
        op_id=OperationId("g_lint"),
        signature=ColourSignature(source=["State"], target="Audit"),
    )

    # Compose f circle_1 g (g outputs Audit, which matches f's source[1])
    res = operad.partial_compose(f, g, i=1)
    assert res.is_ok
    composite = res.unwrap()
    assert composite.arity == 2  # Code, State
    assert composite.source_colours == ("Code", "State")
    assert composite.target_colour == "Receipt"

    # Ill-typed composition: g outputs Audit, but f's source[0] is Code
    res_err = operad.partial_compose(f, g, i=0)
    assert res_err.is_err
    assert isinstance(res_err.error, IllTypedCompositionError)


def test_sequential_associativity_witness():
    f = OperationSignature(
        op_id=OperationId("f_receipt"),
        signature=ColourSignature(source=["Paper", "Audit"], target="Receipt"),
    )
    g = OperationSignature(
        op_id=OperationId("g_audit"),
        signature=ColourSignature(source=["Proof", "Code"], target="Audit"),
    )
    h = OperationSignature(
        op_id=OperationId("h_prover"),
        signature=ColourSignature(source=["State"], target="Proof"),
    )

    # f circle_1 g -> target Proof, Code
    # g circle_0 h -> replaces Proof with State
    res = TreeCompositionWitness.verify_sequential_associativity(f, g, h, i=1, j=0)
    assert res.is_ok
    witness = res.unwrap()
    assert witness.is_associative


def test_agent_slice_permission_gate():
    operad = ColouredOperad()
    op = OperationSignature(
        op_id=OperationId("code_reviewer"),
        signature=ColourSignature(source=["Code"], target="Audit"),
    )
    operad.add_operation(op)

    licensed_slice = AgentSlice(
        agent_id="agent_reviewer",
        licensed_operations={"code_reviewer"},
        allowed_sources={"Code"},
        allowed_targets={"Audit"},
    )
    unlicensed_slice = AgentSlice(
        agent_id="agent_rogue",
        licensed_operations={"other_op"},
    )

    assert operad.verify_agent_permission(licensed_slice, "code_reviewer").is_ok
    err_res = operad.verify_agent_permission(unlicensed_slice, "code_reviewer")
    assert err_res.is_err
