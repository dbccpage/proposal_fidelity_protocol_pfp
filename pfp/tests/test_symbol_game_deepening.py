"""
test_symbol_game_deepening.py
=============================

Comprehensive unit tests for the deepened Clean Architecture components of omega_engine_pfp:
- PacketCodec (sealing, canonical JSON, SHA-256 verification)
- ProposalEvaluator (residual drops, contractiveness, kill conditions, ranking)
- SymbolGameEngine (deep facade seam)
- Protocols & Ports compliance

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from omega_engine_pfp import (
    ObstructionScore,
    PacketCodec,
    ProposalEvaluator,
    SymbolGameController,
    SymbolGameEngine,
)
from omega_engine_pfp.domain.evaluator import KillReason
from omega_engine_pfp.domain.exceptions import SymbolGameValidationError
from omega_engine_pfp.domain.models import SymbolGameEnvelope
from omega_engine_pfp.domain.ports.ports import EvaluatorPort, StoragePort
from omega_engine_pfp.functional_boundary import RustFunctionalRequired


def test_packet_codec_seal_and_verify():
    payload = {
        "title": "Discrete Cochain Retraction",
        "dimension": 28,
        "active_residue": [0.4, 0.2, 0.0],
    }
    envelope = PacketCodec.seal(payload, packet_family="retraction_turn")

    assert envelope["schema_version"] == "2.0.0"
    assert envelope["packet_family"] == "retraction_turn"
    assert envelope["authority_effect"] == "None"
    assert "payload_sha256" in envelope
    assert "envelope_sha256" in envelope

    is_valid, sha, msg = PacketCodec.verify(envelope)
    assert is_valid is True
    assert sha == envelope["payload_sha256"]
    assert msg == "OK"


def test_packet_codec_tamper_detection():
    payload = {"key": "original_value"}
    envelope = PacketCodec.seal(payload, packet_family="audit_packet")

    # Tamper with payload
    tampered_envelope = dict(envelope)
    tampered_envelope["payload"] = {"key": "tampered_value"}

    is_valid, _, msg = PacketCodec.verify(tampered_envelope)
    assert is_valid is False
    assert "mismatch" in msg


def test_packet_codec_authority_rejection():
    payload = {"key": "val"}
    envelope = PacketCodec.seal(payload, packet_family="audit")

    illegal_envelope = dict(envelope)
    illegal_envelope["authority_effect"] = "FullAdmin"

    is_valid, _, msg = PacketCodec.verify(illegal_envelope)
    assert is_valid is False
    assert "Prohibited authority effect" in msg


def test_packet_codec_verify_refuses_flipped_envelope_byte():
    payload = {"key": "original_value"}
    envelope = PacketCodec.seal(payload, packet_family="audit_packet")
    assert PacketCodec.verify(envelope)[0] is True

    family = envelope["packet_family"]
    flipped = ("X" if family[:1] != "X" else "Y") + family[1:]
    assert flipped != family
    tampered = dict(envelope)
    tampered["packet_family"] = flipped

    is_valid, _, msg = PacketCodec.verify(tampered)
    assert is_valid is False
    assert "Envelope SHA-256 mismatch" in msg


def test_proposal_evaluator_contractive_success():
    evaluator = ProposalEvaluator()
    result = evaluator.evaluate_proposal(
        proposal_id="prop_001",
        initial_mass=5.4,
        final_mass=2.8,
        effort=2.0,
    )

    assert result.is_admissible is True
    assert result.kill_reason == KillReason.NONE
    assert result.mass_drop == pytest.approx(2.6)
    assert result.efficiency > 0.0
    assert result.authority_effect == "None"


def test_proposal_evaluator_non_contractive_rejection():
    evaluator = ProposalEvaluator()
    result = evaluator.evaluate_proposal(
        proposal_id="prop_002",
        initial_mass=2.0,
        final_mass=4.5,
        effort=1.0,
    )

    assert result.is_admissible is False
    assert result.kill_reason == KillReason.NON_CONTRACTIVE
    assert result.mass_drop < 0.0


def test_proposal_evaluator_authority_leak_rejection():
    evaluator = ProposalEvaluator()
    result = evaluator.evaluate_proposal(
        proposal_id="prop_003",
        initial_mass=5.0,
        final_mass=2.0,
        metadata={"authority_effect": "StateMutation"},
    )

    assert result.is_admissible is False
    assert result.kill_reason == KillReason.AUTHORITY_LEAK


def test_proposal_evaluator_ranking():
    evaluator = ProposalEvaluator()
    p1 = evaluator.evaluate_proposal("p1", 5.0, 4.0, effort=1.0)  # drop 1.0, eff ~1.0
    p2 = evaluator.evaluate_proposal("p2", 5.0, 1.0, effort=1.0)  # drop 4.0, eff ~4.0
    p3 = evaluator.evaluate_proposal("p3", 5.0, 6.0, effort=1.0)  # non-contractive

    ranked = evaluator.rank_proposals([p1, p2, p3])
    assert len(ranked) == 2
    assert ranked[0].proposal_id == "p2"
    assert ranked[1].proposal_id == "p1"


def test_symbol_game_engine_facade_seam():
    engine = SymbolGameEngine()

    # 1. Turn execution
    outcome = engine.execute_turn("turn_task_1", "retract discrete cochain")
    assert outcome.purity > 0.0
    assert outcome.authority_effect == "None"

    # 2. Problem solving fails closed: Phi1 and Gamma2 are minted only by
    # omega_engine/crates_rs/omega_functional/src, and no Rust-backed adapter
    # backs the facade yet, so it must refuse rather than report PASSED.
    with pytest.raises(RustFunctionalRequired, match="RUST_FUNCTIONAL_REQUIRED"):
        engine.solve_problem("reduce 1-cochain boundary defect", max_steps=3)

    # 3. Packet sealing and verification
    sealed = engine.seal_packet({"metric": "phi_1", "val": 0.0}, "metric_packet")
    is_valid, _, _ = engine.verify_packet(sealed)
    assert is_valid is True

    # 4. Proposal evaluation
    eval_res = engine.evaluate_proposal("prop_seam", 10.0, 3.0)
    assert eval_res.is_admissible is True
    assert eval_res.mass_drop == pytest.approx(7.0)


def test_evaluator_port_protocol():
    evaluator = ProposalEvaluator()
    assert isinstance(evaluator, EvaluatorPort)
