"""Literal request assembly controls, not execution of the native mathematics.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal
from omega_engine_pfp import ffi
from omega_engine_pfp.domain.cochain import PromptCellComplex


def canonical_complex():
    return {
        "c0_dim": 2,
        "c1_dim": 1,
        "c2_dim": 0,
        "d0": [["-1", "1"]],
        "d1": [],
        "source_bytes_hash": None,
    }


class WireRecorder(ffi.RustSymbolGameHost):
    """Intercept only the actual adapter's native invocation boundary."""

    def __init__(self, crossing):
        self.crossing = crossing
        self.calls = []

    def invoke_runtime(self, action, payload):
        self.calls.append((action, payload))
        return self.crossing


def test_complex_serializes_one_spelling_per_field() -> None:
    value = PromptCellComplex(
        v_count=2,
        e_count=1,
        f_count=0,
        d0_matrix=((Fraction(-1, 3), Fraction(1, 3)),),
    )
    expected = canonical_complex()
    expected["d0"] = [["-1/3", "1/3"]]
    assert value.to_dict() == expected


@pytest.mark.parametrize(
    ("convenience", "context"),
    [
        ({"budget": 0}, {"remaining_budget": 0}),
        ({"budget": 7}, {"remaining_budget": 7}),
        ({"source_bytes": ""}, {"source_bytes": ""}),
        ({"source_bytes": "frozen"}, {"source_bytes": "frozen"}),
        ({"expected_source_hash": "literal"}, {"expected_source_hash": "literal"}),
        ({"protected_answers": {}}, {"protected_answers": {}}),
    ],
    ids=["zero-budget", "budget", "empty-source", "source", "hash", "empty-answers"],
)
def test_convenience_arguments_lower_to_nested_wire(convenience, context) -> None:
    crossing = Ok({"literal": "not a native verdict"})
    host = WireRecorder(crossing)
    received = host.evaluate_prompt_cochain(
        complex=canonical_complex(), cochain=["1"], **convenience
    )
    assert received is crossing
    assert host.calls == [
        (
            "cochain_evaluate",
            {"complex": canonical_complex(), "cochain": ["1"], "triad_context": context},
        )
    ]


def test_public_wrapper_keeps_result_identity_and_canonical_native_wire() -> None:
    crossing = Err(Refusal("HOST_TIMEOUT", "literal timeout"))
    host = WireRecorder(crossing)
    supplied_context = {"candidate_answers": {"remaining_budget": "answer data"}}
    protected = {"remaining_budget": "answer data"}
    received = ffi.evaluate_prompt_cochain(
        complex=canonical_complex(),
        cochain=["1"],
        primal_potential=[],
        dual_witness=[],
        triad_context=supplied_context,
        budget=0,
        source_bytes="",
        expected_source_hash="literal hash",
        protected_answers=protected,
        host=host,
    )
    assert received is crossing
    assert supplied_context == {"candidate_answers": {"remaining_budget": "answer data"}}
    assert protected == {"remaining_budget": "answer data"}
    assert host.calls == [
        (
            "cochain_evaluate",
            {
                "complex": canonical_complex(),
                "cochain": ["1"],
                "primal_potential": [],
                "dual_witness": [],
                "triad_context": {
                    **supplied_context,
                    "remaining_budget": 0,
                    "source_bytes": "",
                    "expected_source_hash": "literal hash",
                    "protected_answers": protected,
                },
            },
        )
    ]


@pytest.mark.parametrize(
    ("convenience", "context"),
    [
        ({"budget": 0}, {"remaining_budget": None}),
        ({"budget": 0}, {"remaining_budget": 0}),
        ({"source_bytes": ""}, {"source_bytes": None}),
        ({"expected_source_hash": "literal"}, {"expected_source_hash": None}),
        ({"protected_answers": {}}, {"protected_answers": None}),
    ],
    ids=["null-budget", "equal-budget", "source", "hash", "answers"],
)
def test_duplicate_context_source_refuses_before_native_dispatch(convenience, context) -> None:
    host = WireRecorder(Ok({"literal": "not a native verdict"}))
    before = dict(context)
    result = host.evaluate_prompt_cochain(
        complex=canonical_complex(), cochain=["1"], triad_context=context, **convenience
    )
    assert result.is_err
    assert result.unwrap_err().code == "COCHAIN_CONTEXT_CONFLICT"
    assert host.calls == []
    assert context == before


@pytest.mark.parametrize("context", [None, {}, {"remaining_budget": None}])
def test_optional_context_preserves_absence_empty_and_null_budget(context) -> None:
    crossing = Ok({"literal": "not a native verdict"})
    host = WireRecorder(crossing)
    result = host.evaluate_prompt_cochain(
        complex=canonical_complex(), cochain=[], triad_context=context
    )
    expected = {"complex": canonical_complex(), "cochain": []}
    if context is not None:
        expected["triad_context"] = context
    assert result is crossing
    assert host.calls == [("cochain_evaluate", expected)]
