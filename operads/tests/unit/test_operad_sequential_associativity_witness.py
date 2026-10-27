"""The sequential associativity witness must compose both bracketings.

`TreeCompositionWitness.verify_sequential_associativity` used to return
`is_associative=True` with "Verified formal operadic sequential associativity
axiom" after four typing checks. It never composed anything, so any defect in
how the two bracketings are computed -- the classic one is the index shift
`i + j` -- could not change its answer. These tests pin the composite each
bracketing produces and mutate the bracketing to show the comparison is live.
"""

from __future__ import annotations

import pytest

from operads.domain.operad import (
    ColourSignature,
    OperationId,
    OperationSignature,
    TreeCompositionWitness,
    planar,
)


def _op(name: str, sources: list[str], target: str) -> OperationSignature:
    return OperationSignature(
        op_id=OperationId(name), signature=ColourSignature(source=sources, target=target)
    )


def test_the_witness_carries_the_hand_computed_composite_of_both_bracketings() -> None:
    """f: (Paper, Audit) -> Receipt, g: (Proof, Code) -> Audit, h: (State) -> Proof.

    f o_1 g = (Paper, Proof, Code) -> Receipt; then o_1 h = (Paper, State, Code).
    g o_0 h = (State, Code) -> Audit; f o_1 that = (Paper, State, Code) -> Receipt.
    """
    f = _op("f", ["Paper", "Audit"], "Receipt")
    g = _op("g", ["Proof", "Code"], "Audit")
    h = _op("h", ["State"], "Proof")
    expected = ColourSignature(source=["Paper", "State", "Code"], target="Receipt")

    res = TreeCompositionWitness.verify_sequential_associativity(f, g, h, i=1, j=0)

    assert res.is_ok
    witness = res.unwrap()
    assert witness.is_associative
    assert witness.left_composite == expected
    assert witness.right_composite == expected
    assert str(expected) in witness.details


def test_a_wrong_index_shift_is_caught_where_a_typing_only_witness_would_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Counterexample: shift the second insertion to `j` instead of `i + j`.

    f: (Code, Code) -> Receipt, g: (Code, Code) -> Code, h: (State) -> Code,
    i = 1, j = 1. Every typing check the old witness made passes, so it would
    report associativity whatever the bracketings computed. Correctly, both are
    (Code, Code, State) -> Receipt; with the mutated shift the left bracketing
    is (Code, State, Code) -> Receipt, and the witness must refuse.
    """
    f = _op("f", ["Code", "Code"], "Receipt")
    g = _op("g", ["Code", "Code"], "Code")
    h = _op("h", ["State"], "Code")

    honest = TreeCompositionWitness.verify_sequential_associativity(f, g, h, i=1, j=1)
    assert honest.is_ok
    assert honest.unwrap().left_composite == ColourSignature(
        source=["Code", "Code", "State"], target="Receipt"
    )

    def left_with_wrong_shift(f_sig, g_sig, h_sig, i, j):
        return planar.compose_colour_signatures(f_sig, g_sig, i).bind(
            lambda fg: planar.compose_colour_signatures(fg, h_sig, j)
        )

    monkeypatch.setattr(planar, "_left_bracketing", left_with_wrong_shift)
    mutated = TreeCompositionWitness.verify_sequential_associativity(f, g, h, i=1, j=1)

    assert mutated.is_err
    assert "bracketings disagree" in mutated.error.message


def test_an_off_by_one_shift_is_refused_rather_than_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    f = _op("f", ["Code", "Code"], "Receipt")
    g = _op("g", ["Code", "Code"], "Code")
    h = _op("h", ["State"], "Code")

    def left_off_by_one(f_sig, g_sig, h_sig, i, j):
        return planar.compose_colour_signatures(f_sig, g_sig, i).bind(
            lambda fg: planar.compose_colour_signatures(fg, h_sig, i + j + 1)
        )

    monkeypatch.setattr(planar, "_left_bracketing", left_off_by_one)
    res = TreeCompositionWitness.verify_sequential_associativity(f, g, h, i=1, j=1)

    assert res.is_err
    assert "left bracketing refused" in res.error.message


def test_a_boolean_index_is_refused_not_read_as_one() -> None:
    """`True` passed the old `0 <= i < arity` check as the integer 1."""
    f = _op("f", ["Paper", "Audit"], "Receipt")
    g = _op("g", ["Proof", "Code"], "Audit")
    h = _op("h", ["State"], "Proof")

    res = TreeCompositionWitness.verify_sequential_associativity(f, g, h, i=True, j=0)

    assert res.is_err


def test_an_ill_typed_inner_composition_is_refused() -> None:
    f = _op("f", ["Paper", "Audit"], "Receipt")
    g = _op("g", ["Proof", "Code"], "Audit")
    h = _op("h", ["State"], "Code")  # g expects Proof at slot 0

    res = TreeCompositionWitness.verify_sequential_associativity(f, g, h, i=1, j=0)

    assert res.is_err
