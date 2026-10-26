"""
test_llm_streaming_harness.py — Unit tests for Paper 033 streaming integration harness.
"""

import os
from fractions import Fraction

import pytest

from llm_streaming_harness import (
    LLMStreamChunk,
    MockLLMStreamingProposer,
    StreamingEnvelopeParser,
    SymbolGameStreamingSession,
    run_and_generate_receipt,
)


def test_mock_streaming_chunks_and_parser():
    envelope = {
        "schema": "TAU_SG_V1",
        "step_id": "test_01",
        "parent_step_id": "root",
        "move_type": "CUT",
        "move_parameters": {
            "rule_id": "R1.test",
            "proposed_claims": {"a, b": 1},
        },
        "expected_defect_delta": "-1",
    }
    proposer = MockLLMStreamingProposer([envelope], chunk_size=8)
    parser = StreamingEnvelopeParser()

    chunks = list(proposer.stream_proposal("test prompt"))
    assert len(chunks) > 1  # Verify chunked streaming
    assert chunks[-1].is_terminal is True

    for c in chunks:
        parser.append_chunk(c)

    parsed = parser.parse_envelope()
    assert parsed["schema"] == "TAU_SG_V1"
    assert parsed["step_id"] == "test_01"
    assert parsed["move_type"] == "CUT"


def test_streaming_envelope_parser_malformed_refusal():
    parser = StreamingEnvelopeParser()
    parser.append_chunk(LLMStreamChunk(text="```json\n{ malformed: json \n```", is_terminal=True))
    with pytest.raises(ValueError, match="Envelope parse failure"):
        parser.parse_envelope()


def test_streaming_session_defect_monotonicity(native_functional):
    # 3-node cycle with weights 1, 2, 2
    envelopes = [
        # Bad cut: should be refused
        {
            "schema": "TAU_SG_V1",
            "step_id": "s01",
            "parent_step_id": "root",
            "move_type": "CUT",
            "move_parameters": {
                "rule_id": "R1.bad",
                "proposed_claims": {"a, b": 10, "b, c": 0, "c, a": 0},
            },
            "expected_defect_delta": "+7",
        },
        # Good cut: should be admitted
        {
            "schema": "TAU_SG_V1",
            "step_id": "s02",
            "parent_step_id": "root",
            "move_type": "CUT",
            "move_parameters": {
                "rule_id": "R1.repair",
                "proposed_claims": {"a, b": -2, "b, c": 1, "c, a": 1},
            },
            "expected_defect_delta": "-3",
        },
        # Verify: should be admitted
        {
            "schema": "TAU_SG_V1",
            "step_id": "s03",
            "parent_step_id": "s02",
            "move_type": "VERIFY",
            "move_parameters": {"claim": "ZERO_OBSTRUCTION"},
            "expected_defect_delta": "0",
        },
    ]
    proposer = MockLLMStreamingProposer(envelopes)
    session = SymbolGameStreamingSession(
        vertices=["a", "b", "c"],
        edges=[("a", "b", 1), ("b", "c", 2), ("c", "a", 2)],
        initial_claims={("a", "b"): 1, ("b", "c"): 1, ("c", "a"): 1},
        proposer=proposer,
    )

    init_phi1 = session.initialize()
    assert init_phi1 == Fraction(3)

    v1 = session.run_turn("Turn 1")
    assert v1["status"] == "DefectIncrease"
    assert v1["admitted"] is False
    assert v1["defect_after"] == "10"  # Evaluated candidate defect that caused refusal
    assert session.governor.primary_obstruction() == Fraction(3)  # Host state preserved untouched

    v2 = session.run_turn("Turn 2")
    assert v2["status"] == "ExactRepair"
    assert v2["admitted"] is True
    assert v2["defect_after"] == "0"

    v3 = session.run_turn("Turn 3")
    assert v3["admitted"] is True
    assert v3["defect_after"] == "0"


def test_receipt_generation_and_digest(tmp_path, native_functional):
    out_file = str(tmp_path / "test_receipt.json")
    receipt = run_and_generate_receipt(out_file)

    assert os.path.exists(out_file)
    assert receipt["summary"]["status"] == "PASS_ALL_INVARIANTS"
    assert receipt["summary"]["refusals_caught_fail_closed"] == 1
    assert receipt["summary"]["zero_defect_terminals_verified"] == 2
    assert "sha256_digest" in receipt
    assert len(receipt["sha256_digest"]) == 64
