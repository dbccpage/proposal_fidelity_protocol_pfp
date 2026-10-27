"""Finite ordered-boundary controls for the existing planar substitution kernel.

These literal examples inspect ordered inputs, not operation-name equality.
They reuse an already-correct nested offset; no general theorem is claimed.
AuthorityEffect: None.
"""

import pytest

from workflows_agents_skills.domain.planar_substitution import (
    OperadOperation,
    SubstitutionError,
    associativity_witness,
    substitute,
)


@pytest.mark.parametrize(
    ("theta_inputs", "i", "phi_inputs", "j", "psi_inputs", "expected"),
    [
        (
            ("Paper", "Code", "Audit"),
            1,
            ("Code", "Code"),
            1,
            ("Proof", "Ledger"),
            ("Paper", "Code", "Proof", "Ledger", "Audit"),
        ),
        (
            ("Code", "Paper", "Code", "Audit"),
            2,
            ("Code", "Code", "State"),
            0,
            ("Proof", "Ledger"),
            ("Code", "Paper", "Proof", "Ledger", "Code", "State", "Audit"),
        ),
        (
            ("Paper", "Code", "Code", "Post"),
            2,
            ("Code", "Code", "Audit"),
            1,
            ("State",),
            ("Paper", "Code", "Code", "State", "Audit", "Post"),
        ),
    ],
)
def test_nested_nonzero_slots_preserve_literal_positions(
    theta_inputs,
    i,
    phi_inputs,
    j,
    psi_inputs,
    expected,
) -> None:
    theta = OperadOperation("theta", theta_inputs, "Receipt")
    phi = OperadOperation("phi", phi_inputs, "Code")
    psi = OperadOperation("psi", psi_inputs, "Code")

    witness = associativity_witness(theta, i, phi, j, psi)
    outer = substitute(theta, i, phi)
    correct = substitute(outer, i + j, psi)
    # All selected wrong slots also expect Code: colour checks cannot rescue a
    # wrong positional offset in these examples.
    unshifted = substitute(outer, j, psi)

    assert witness.source_colours == correct.source_colours == expected
    assert witness.target_colour == correct.target_colour == "Receipt"
    assert witness.arity == len(expected)
    assert unshifted.target_colour == "Receipt"
    assert unshifted.source_colours != expected
    assert sorted(unshifted.source_colours) == sorted(expected)


@pytest.mark.parametrize(
    ("phi_inputs", "expected"),
    [
        ((), ("Paper", "Audit", "Ledger", "Receipt", "Post")),
        (("Proof",), ("Paper", "Proof", "Audit", "Ledger", "Receipt", "Post")),
        (
            ("Proof", "Code", "State"),
            ("Paper", "Proof", "Code", "State", "Audit", "Ledger", "Receipt", "Post"),
        ),
    ],
)
def test_disjoint_right_slot_reindexes_after_left_splice(phi_inputs, expected) -> None:
    theta = OperadOperation("theta", ("Paper", "Code", "Audit", "State", "Post"), "Receipt")
    phi = OperadOperation("left", phi_inputs, "Code")
    psi = OperadOperation("right", ("Ledger", "Receipt"), "State")
    left_slot, right_slot = 1, 3

    left_first = substitute(
        substitute(theta, left_slot, phi),
        right_slot + phi.arity - 1,
        psi,
    )
    right_first = substitute(substitute(theta, right_slot, psi), left_slot, phi)

    assert left_first.source_colours == right_first.source_colours == expected
    assert left_first.target_colour == right_first.target_colour == "Receipt"
    assert left_first.arity == right_first.arity == len(expected)


def test_disjoint_original_slot_can_be_admissible_and_still_be_wrong() -> None:
    theta = OperadOperation("theta", ("Paper", "Code", "Audit", "State", "Post"), "Receipt")
    phi = OperadOperation("left", ("Proof", "Code", "State"), "Code")
    psi = OperadOperation("right", ("Ledger", "Receipt"), "State")
    outer = substitute(theta, 1, phi)

    correct = substitute(outer, 5, psi)
    unshifted = substitute(outer, 3, psi)

    assert correct.source_colours == (
        "Paper",
        "Proof",
        "Code",
        "State",
        "Audit",
        "Ledger",
        "Receipt",
        "Post",
    )
    assert unshifted.source_colours == (
        "Paper",
        "Proof",
        "Code",
        "Ledger",
        "Receipt",
        "Audit",
        "State",
        "Post",
    )
    assert unshifted.target_colour == correct.target_colour == "Receipt"
    assert sorted(unshifted.source_colours) == sorted(correct.source_colours)
    assert unshifted.source_colours != correct.source_colours


def test_identity_insertions_preserve_each_ordered_boundary() -> None:
    theta = OperadOperation("theta", ("Paper", "Code", "Audit"), "Receipt")
    for slot, colour in enumerate(theta.source_colours):
        identity = OperadOperation("identity", (colour,), colour)
        composed = substitute(theta, slot, identity)
        assert composed.source_colours == ("Paper", "Code", "Audit")
        assert composed.target_colour == "Receipt"
    outer_identity = OperadOperation("identity", ("Receipt",), "Receipt")
    composed = substitute(outer_identity, 0, theta)
    assert composed.source_colours == ("Paper", "Code", "Audit")
    assert composed.target_colour == "Receipt"


def test_nullary_substitution_removes_only_the_selected_slot() -> None:
    theta = OperadOperation("theta", ("Paper", "Code", "Audit"), "Receipt")
    constant = OperadOperation("constant", (), "Code")
    composed = substitute(theta, 1, constant)
    assert composed.source_colours == ("Paper", "Audit")
    assert composed.target_colour == "Receipt"
    assert composed.arity == 2

    nullary_receipt = OperadOperation("receipt", (), "Receipt")
    identity = OperadOperation("identity", ("Receipt",), "Receipt")
    terminal = substitute(identity, 0, nullary_receipt)
    assert terminal.source_colours == ()
    assert terminal.target_colour == "Receipt"
    assert terminal.arity == 0
    with pytest.raises(SubstitutionError) as refused:
        substitute(terminal, 0, nullary_receipt)
    assert refused.value.code == "INDEX_OUT_OF_RANGE"


def test_nested_nullary_substitution_preserves_the_surviving_order() -> None:
    theta = OperadOperation("theta", ("Paper", "Code", "Audit"), "Receipt")
    phi = OperadOperation("phi", ("State", "Code"), "Code")
    psi = OperadOperation("constant", (), "Code")
    witness = associativity_witness(theta, 1, phi, 1, psi)
    assert witness.source_colours == ("Paper", "State", "Audit")
    assert witness.target_colour == "Receipt"
    assert witness.arity == 3


@pytest.mark.parametrize(
    ("slot", "code"),
    [
        (True, "BAD_INDEX"),
        (False, "BAD_INDEX"),
        (1.0, "BAD_INDEX"),
        ("1", "BAD_INDEX"),
        (None, "BAD_INDEX"),
        (-1, "INDEX_OUT_OF_RANGE"),
        (3, "INDEX_OUT_OF_RANGE"),
        (100, "INDEX_OUT_OF_RANGE"),
    ],
)
def test_substitution_slots_have_exact_typed_refusals(slot, code) -> None:
    theta = OperadOperation("theta", ("Code", "Code", "Code"), "Receipt")
    phi = OperadOperation("phi", ("State",), "Code")
    with pytest.raises(SubstitutionError) as refused:
        substitute(theta, slot, phi)
    assert refused.value.code == code


@pytest.mark.parametrize(
    ("i", "j", "code"),
    [
        (True, 1, "BAD_INDEX"),
        (1, False, "BAD_INDEX"),
        (3, 1, "INDEX_OUT_OF_RANGE"),
        (1, -1, "INDEX_OUT_OF_RANGE"),
        (1, 2, "INDEX_OUT_OF_RANGE"),
    ],
)
def test_nested_invalid_slots_do_not_return_a_witness(i, j, code) -> None:
    theta = OperadOperation("theta", ("Code", "Code", "Code"), "Receipt")
    phi = OperadOperation("phi", ("Code", "Code"), "Code")
    psi = OperadOperation("psi", ("State",), "Code")
    with pytest.raises(SubstitutionError) as refused:
        associativity_witness(theta, i, phi, j, psi)
    assert refused.value.code == code
