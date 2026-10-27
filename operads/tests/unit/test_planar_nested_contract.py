"""Nonzero nested slots and ordered-boundary controls for the actual planar kernel."""

from operads.domain.planar_substitution import (
    OperadOperation,
    associativity_witness,
)


def test_nested_nonzero_slots_use_i_plus_j_and_the_literal_ordered_boundary() -> None:
    theta = OperadOperation("theta", ("Paper", "Code", "Audit"), "Receipt")
    phi = OperadOperation("phi", ("Code", "Code"), "Code")
    psi = OperadOperation("psi", ("Proof", "Ledger"), "Code")

    witness = associativity_witness(theta, 1, phi, 1, psi)

    assert witness.source_colours == ("Paper", "Code", "Proof", "Ledger", "Audit")
    assert witness.target_colour == "Receipt"


def test_reordered_input_witness_does_not_match_the_original_boundary() -> None:
    theta = OperadOperation("theta", ("Paper", "Code", "Audit"), "Receipt")
    phi = OperadOperation("phi", ("State", "Code"), "Code")
    reordered = OperadOperation("phi", ("Code", "State"), "Code")
    psi = OperadOperation("psi", ("Proof", "Ledger"), "Code")

    original = associativity_witness(theta, 1, phi, 1, psi)
    foreign = associativity_witness(theta, 1, reordered, 0, psi)

    assert original.source_colours == ("Paper", "State", "Proof", "Ledger", "Audit")
    assert foreign.source_colours == ("Paper", "Proof", "Ledger", "State", "Audit")
    assert original.target_colour == foreign.target_colour == "Receipt"
    assert foreign.source_colours != original.source_colours
