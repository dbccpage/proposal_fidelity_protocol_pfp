"""C004 fixed-slot language and existing decode-port handoff, without inference."""

from __future__ import annotations

from hashlib import sha256

import pytest

from pfp.domain import carrier_decoding
from pfp.domain.ports.decode_control_port import ControlKind
from pfp.infrastructure.adapters.decode_controls import VllmDecodeAdapter


def test_slot_grammar_requires_three_separated_signed_integers():
    grammar = carrier_decoding.integer_slots_gbnf(3)
    assert grammar == (
        'root ::= integer " " integer " " integer\n'
        'integer ::= "-"? [0-9]+\n'
    )


@pytest.mark.parametrize("k", [3, 12])
def test_slot_count_covers_original_c004_boundary_cases(k):
    values = tuple(str(i - k) for i in range(k))
    assert carrier_decoding.parse_integer_slots(" ".join(values), k) == values
    assert carrier_decoding.parse_integer_slots(" ".join(values[:-1]), k) is None
    assert carrier_decoding.parse_integer_slots(" ".join((*values, "0")), k) is None


@pytest.mark.parametrize("k", [True, 3.0, "3", 0, 2, 13])
def test_slot_count_does_not_coerce_or_expand_the_original_problem(k):
    with pytest.raises(ValueError, match="3.*12"):
        carrier_decoding.integer_slots_gbnf(k)


@pytest.mark.parametrize(
    "text",
    [
        "123",  # Alphabet-valid digit run is not three slots.
        "1 2", "1 2 3 4", "--3 0 3", "3. 0 -3",
        "+3 0 -3", "3  0 -3", "3\t0 -3", "3 0 -3\n",
        " 3 0 -3", "3 0 -3 ", "３ 0 -3", "repair: 3 0 -3",
    ],
)
def test_shape_checker_rejects_original_mutations_and_carrier_only_failures(text):
    assert carrier_decoding.parse_integer_slots(text, 3) is None


def test_shape_check_preserves_integer_text_without_claiming_repair_correctness():
    # C004 declares signed integers, no output magnitude/canonical-zero bound.
    text = "-" + "9" * 5000 + " 00 -0"
    assert carrier_decoding.parse_integer_slots(text, 3) == tuple(text.split(" "))
    # A format constraint cannot determine zero sum or weighted optimality.
    assert carrier_decoding.parse_integer_slots("555555 555555 555555", 3) is not None
    assert carrier_decoding.parse_integer_slots(["1", "0", "-1"], 3) is None


def test_existing_decode_adapter_receives_actual_grammar_and_retains_response():
    submitted = []

    def runner(body):
        submitted.append(body)
        return "3 0 -3", [17, 220, 15, 220, 12, 18], True

    spec = carrier_decoding.integer_slots_control(3, max_tokens=96)
    text, receipt = VllmDecodeAdapter(runner=runner).apply_decode_control(
        spec, "Repair the declared cycle", case_id="c004_slots3"
    )
    assert spec.control_kind is ControlKind.GBNF
    assert spec.grammar_mask.grammar_type == "gbnf"
    assert submitted == [{
        "model": "meta-llama/Llama-3.1-8B-Instruct",
        "messages": [{"role": "user", "content": "Repair the declared cycle"}],
        "max_tokens": 96,
        "temperature": 0.0,
        "grammar": carrier_decoding.integer_slots_gbnf(3),
    }]
    assert text == "3 0 -3"
    assert receipt.output_tokens == (17, 220, 15, 220, 12, 18)
    assert receipt.grammar_sha256 == sha256(submitted[0]["grammar"].encode()).hexdigest()
    # This is injected-runner handoff evidence, not tokenizer/sampler evidence.
    assert carrier_decoding.parse_integer_slots(text, 3) == ("3", "0", "-3")


def test_grammar_request_cannot_turn_unavailable_execution_into_success():
    spec = carrier_decoding.integer_slots_control(3)
    with pytest.raises(RuntimeError, match="EXECUTION_UNAVAILABLE"):
        VllmDecodeAdapter().apply_decode_control(spec, "Repair the declared cycle")


def test_runner_claim_does_not_bypass_the_independent_shape_check():
    spec = carrier_decoding.integer_slots_control(3)
    text, receipt = VllmDecodeAdapter(
        runner=lambda body: ("555555", [999], True)
    ).apply_decode_control(spec, "Repair the declared cycle")
    assert receipt.honored is True  # Existing port records the runner's assertion.
    assert carrier_decoding.parse_integer_slots(text, 3) is None
