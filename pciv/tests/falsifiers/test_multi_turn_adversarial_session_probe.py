"""Test suite for Multi-Turn Adversarial Session Probe.

Verifies end-to-end integration across:
- Grammar mutations (Genesis carrier balance, DDC rewrite rules)
- OEOS host adapter (OeosHostAdapter / HostPortV1)
- Prompt Civilization adapters (CAS, Durable Event Log, Genome Registry, Protected Spans,
  Immunity Armed Repertoire, Lineage Taint, Exact Ancestral Rank Solver & Verifier)
- 4-part adversarial quarantine assertions (Protected Spans, Grammar Malformation,
  Authority Escalation, Zero-Float Smuggling)

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from operating_system.adapters.oeos_host import OeosHostAdapter
from operating_system.adapters.prompt_civ.adversarial_session_probe import (
    AdversarialSessionProbeReceiptV1,
    AdversarialSessionProbeV1,
    admission_beside_host,
    validate_carrier_word,
)
from pciv.infrastructure.probes.adversarial_session_probe import (
    admission_beside_host as civilization_admission_beside_host,
)
from operating_system.adapters.prompt_civ.event_log import (
    DurableEventLogV1,
    EventIdentityConflictError,
    PromptCivEventV1,
)
from operating_system.adapters.prompt_civ.rank import (
    RankCertificateVerifierV1,
)
from operating_system.adapters.prompt_civ.record import (
    ProtectedSpanV1,
)


def test_refused_host_blocks_a_local_accepted_verdict() -> None:
    """A host status of REFUSED cannot be recorded as a local ACCEPTED verdict."""
    host = {"status": "REFUSED"}
    expected = (False, "REFUSED", "host_status is REFUSED", "REFUSED")
    assert admission_beside_host(host, local_admitted=True, local_verdict="ACCEPTED") == expected
    assert (
        civilization_admission_beside_host(host, local_admitted=True, local_verdict="ACCEPTED")
        == expected
    )
    assert admission_beside_host(
        {}, local_admitted=True, local_verdict="ACCEPTED"
    ) == expected
    assert admission_beside_host(
        host,
        local_admitted=False,
        local_verdict="QUARANTINED",
        local_reason="kept",
    ) == (False, "QUARANTINED", "kept", "REFUSED")


def test_genesis_carrier_grammar_validation_rules() -> None:
    """Verifies that validate_carrier_word adheres strictly to Genesis carrier laws."""
    # 1. Valid carriers (balanced brackets, non-negative running depth, pure alphabet)
    assert validate_carrier_word("") is True
    assert validate_carrier_word("<>") is True
    assert validate_carrier_word("<<>>") is True
    assert validate_carrier_word("<><>") is True
    assert validate_carrier_word("<<<><>>><>") is True

    # 2. Invalid carriers (unbalanced net charge)
    assert validate_carrier_word("<") is False
    assert validate_carrier_word(">") is False
    assert validate_carrier_word("<<<>>") is False
    assert validate_carrier_word("<>>>") is False

    # 3. Invalid carriers (negative running prefix depth)
    assert validate_carrier_word("><") is False
    assert validate_carrier_word("<><>>") is False

    # 4. Invalid carriers (foreign glyphs outside {'<', '>'})
    assert validate_carrier_word("<a>") is False
    assert validate_carrier_word("< >") is False
    assert validate_carrier_word("<1>") is False
    assert validate_carrier_word("[]") is False


def test_full_adversarial_session_probe_execution(tmp_path: Path) -> None:
    """Verifies full 8-turn session probe execution with 4 quarantined adversarial attacks."""
    cas_dir = tmp_path / "cas"
    event_dir = tmp_path / "events"
    host = OeosHostAdapter()

    probe = AdversarialSessionProbeV1(
        host=host,
        cas_dir=cas_dir,
        event_log_dir=event_dir,
        session_id="adv_test_session_001",
    )

    receipt = probe.run_full_session(
        system_framing="System: Genesis Carrier Grammar Assistant.\nRule: Carriers must be balanced angle brackets.",
    )

    assert isinstance(receipt, AdversarialSessionProbeReceiptV1)
    assert receipt.session_id == "adv_test_session_001"
    assert receipt.receipt_sha256.startswith("sha256:")
    assert receipt.is_consistent is True
    assert receipt.authority_effect == "None"

    # Turn execution census
    assert receipt.total_turns == 8
    assert receipt.turns_attempted == 7
    assert receipt.turns_passed == 0
    assert receipt.adversarial_attacks_quarantined == 4  # Turns 2, 3, 4, 5

    # Storage and DAG invariants
    assert receipt.cas_objects_count == 2
    assert receipt.event_count == 8
    assert receipt.lineage_nodes_count == 2
    assert receipt.lineage_edges_count == 1
    assert receipt.tainted_nodes_count == 1
    assert receipt.antibodies_armed_count >= 1
    assert receipt.rank_certificates_verified == 1

    # OEOS host audit verification
    assert receipt.host_requests_count == 8
    assert len(host.audit_log) == 8
    for entry in host.audit_log:
        req = entry["request"]
        resp = entry["response"]
        assert req["session_id"] == "adv_test_session_001"
        assert resp["host_id"] == "oeos-host-v1"
        assert resp["status"] == "REFUSED"
        assert resp["reason"] == "request was parsed and not admitted"
        assert resp["authority_effect"] == "None"
        assert "payload_sha256" in resp

    # Check individual turn results
    turns = probe.turn_results
    assert len(turns) == 7

    assert turns[0].turn_kind == "BASELINE" and turns[0].verdict == "REFUSED"
    assert turns[0].is_admitted is False
    assert turns[0].refusal_reason == "host_status is REFUSED"
    assert turns[0].host_status == "REFUSED"
    assert turns[1].turn_kind == "ADMITTED_MUTATION" and turns[1].verdict == "REFUSED"
    assert turns[1].is_admitted is False
    assert turns[1].refusal_reason == "host_status is REFUSED"
    assert turns[2].turn_kind == "ATTACK_PROTECTED_SPAN" and turns[2].verdict == "QUARANTINED"
    assert turns[3].turn_kind == "ATTACK_MALFORMED_GRAMMAR" and turns[3].verdict == "QUARANTINED"
    assert turns[4].turn_kind == "ATTACK_AUTHORITY_ESCALATION" and turns[4].verdict == "QUARANTINED"
    assert turns[5].turn_kind == "ATTACK_FLOAT_SMUGGLING" and turns[5].verdict == "QUARANTINED"
    assert turns[6].turn_kind == "SELECTION_AND_RANKING" and turns[6].verdict == "REFUSED"
    assert turns[6].is_admitted is False
    assert turns[6].host_status == "REFUSED"


def test_protected_span_mutation_attack_refusal_and_antibody_arming(tmp_path: Path) -> None:
    """Verifies that mutations inside protected spans raise and arm an antibody in the repertoire."""
    probe = AdversarialSessionProbeV1(
        cas_dir=tmp_path / "cas",
        event_log_dir=tmp_path / "events",
        session_id="span_probe_test",
    )

    framing = "System: Protected Section.\nUser: Carrier proposal: <>."
    span = ProtectedSpanV1(name="system_framing", start_byte=0, end_byte=26)
    probe.execute_baseline_turn(
        prompt_text=framing,
        protected_spans=(span,),
        domain_model={"domain": "test"},
    )

    # Attack overlapping protected span
    res = probe.execute_adversarial_protected_span_attack(
        original_prompt_text=framing,
        hostile_replacement="INTRUSION",
        edit_start_byte=10,
        edit_end_byte=20,
    )
    assert res.verdict == "QUARANTINED"
    assert "PROTECTED_SPAN_MUTATION_REFUSED" in (res.refusal_reason or "")

    # Zero-width insertion attack inside protected span
    res_zero = probe.execute_adversarial_protected_span_attack(
        original_prompt_text=framing,
        hostile_replacement="INTRUSION",
        edit_start_byte=15,
        edit_end_byte=15,
    )
    assert res_zero.verdict == "QUARANTINED"
    assert "PROTECTED_SPAN_MUTATION_REFUSED" in (res_zero.refusal_reason or "")

    # Assert armed antibodies are registered
    root_id = probe._root_genome_id
    assert root_id is not None
    armed = probe.repertoire_mgr.get_armed_repertoire(root_id, ledger_revision=1)
    assert len(armed) >= 1


def test_malformed_grammar_mutation_attack_and_lineage_tainting(tmp_path: Path) -> None:
    """Verifies that malformed carriers are quarantined and taint propagates down causal edges."""
    probe = AdversarialSessionProbeV1(
        cas_dir=tmp_path / "cas",
        event_log_dir=tmp_path / "events",
        session_id="grammar_probe_test",
    )
    framing = "System: Genesis.\nUser: <>."
    span = ProtectedSpanV1(name="system_framing", start_byte=0, end_byte=16)
    probe.execute_baseline_turn(
        prompt_text=framing,
        protected_spans=(span,),
        domain_model={"domain": "test"},
    )

    res = probe.execute_adversarial_malformed_grammar_attack(malformed_carrier="><<>")
    assert res.verdict == "QUARANTINED"
    assert "MALFORMED_CARRIER_GRAMMAR" in (res.refusal_reason or "")

    tainted_node = "cand_tainted_1"
    assert probe.taint_engine.is_tainted(tainted_node)

    # Propagate taint along edge to descendant
    probe.taint_engine.propagate_taint([(tainted_node, "descendant_cand_x")])
    assert probe.taint_engine.is_tainted("descendant_cand_x")


def test_authority_escalation_attack_refusal(tmp_path: Path) -> None:
    """Verifies that non-None authority attempts are quarantined."""
    probe = AdversarialSessionProbeV1(
        cas_dir=tmp_path / "cas",
        event_log_dir=tmp_path / "events",
        session_id="auth_probe_test",
    )
    framing = "System: Genesis.\nUser: <>."
    span = ProtectedSpanV1(name="system_framing", start_byte=0, end_byte=16)
    probe.execute_baseline_turn(
        prompt_text=framing,
        protected_spans=(span,),
        domain_model={"domain": "test"},
    )

    for forged in ["AUTHORITY_SOVEREIGN", "ROOT", "ADMIN", "None_with_suffix"]:
        res = probe.execute_adversarial_authority_attack(forged_authority=forged)
        assert res.verdict == "QUARANTINED"
        assert "REFUSAL_AUTHORITY_NON_NONE" in (res.refusal_reason or "")


def test_float_cochain_smuggling_firewall(tmp_path: Path) -> None:
    """Verifies that floats are caught by the zero-float canonical firewall."""
    probe = AdversarialSessionProbeV1(
        cas_dir=tmp_path / "cas",
        event_log_dir=tmp_path / "events",
        session_id="float_probe_test",
    )
    framing = "System: Genesis.\nUser: <>."
    span = ProtectedSpanV1(name="system_framing", start_byte=0, end_byte=16)
    probe.execute_baseline_turn(
        prompt_text=framing,
        protected_spans=(span,),
        domain_model={"domain": "test"},
    )

    for fl in [0.0, 1.25, -0.5, float("inf"), float("nan")]:
        res = probe.execute_adversarial_float_smuggling_attack(float_value=fl)
        assert res.verdict == "QUARANTINED"
        assert "float values are forbidden in exact rational arithmetic" in (res.refusal_reason or "")


def test_ancestral_ranking_exact_invariants_and_verification(tmp_path: Path) -> None:
    """Verifies exact rational inverse PageRank solving and dual certificate verification."""
    probe = AdversarialSessionProbeV1(
        cas_dir=tmp_path / "cas",
        event_log_dir=tmp_path / "events",
        session_id="rank_probe_test",
    )
    framing = "System: Genesis.\nUser: Carrier proposal: <>."
    span = ProtectedSpanV1(name="system_framing", start_byte=0, end_byte=16)
    probe.execute_baseline_turn(
        prompt_text=framing,
        protected_spans=(span,),
        domain_model={"domain": "test"},
    )
    probe.execute_grammatical_mutation_turn(
        carrier_extension="<<>>",
        original_prompt_text=framing,
        edit_start_byte=len(framing.encode("utf-8")) - 3,
        edit_end_byte=len(framing.encode("utf-8")) - 1,
    )

    rank_res = probe.execute_ancestral_ranking_turn()
    assert rank_res.verdict == "REFUSED"
    assert rank_res.is_admitted is False
    assert rank_res.refusal_reason == "host_status is REFUSED"
    assert rank_res.host_status == "REFUSED"

    nodes = list(probe.lineage_graph.nodes)
    edges = list(probe.lineage_graph.edges)
    ranks = probe.rank_solver.solve_fixed_point(
        num_nodes=len(nodes),
        edges=edges,
        evidence={nodes[0]: {"passes": 5, "failures": 0}},
    )

    # All ranks are exact Fractions summing to 1
    assert all(isinstance(r, Fraction) for r in ranks)
    assert sum(ranks) == Fraction(1, 1)

    # Valid certificate verifies
    verifier = RankCertificateVerifierV1()
    assert verifier.verify_rank_certificate(
        nodes=nodes,
        edges=edges,
        candidate_rank=ranks,
        evidence={nodes[0]: {"passes": 5, "failures": 0}},
    ) is True

    # Forged zero or uniform vector rejects
    zero_rank = [Fraction(0, 1)] * len(nodes)
    assert verifier.verify_rank_certificate(
        nodes=nodes,
        edges=edges,
        candidate_rank=zero_rank,
    ) is False


def test_durable_event_log_recovery_and_hash_chain(tmp_path: Path) -> None:
    """Verifies durable event log persistence, restart recovery, and conflict rejection."""
    event_dir = tmp_path / "events"
    probe = AdversarialSessionProbeV1(
        cas_dir=tmp_path / "cas",
        event_log_dir=event_dir,
        session_id="durability_test",
    )
    probe.run_full_session()

    # Restart: instantiate a new DurableEventLogV1 reading the same file
    recovered_log = DurableEventLogV1(log_dir=event_dir)
    recovered_events = recovered_log.get_events()
    assert len(recovered_events) == 8

    # Idempotent re-append of same event succeeds without duplication
    recovered_log.append(recovered_events[0])
    assert len(recovered_log.get_events()) == 8

    # Conflicting payload with existing event ID raises EventIdentityConflictError
    conflicting_event = PromptCivEventV1(
        producer_id=recovered_events[0].producer_id,
        event_kind=recovered_events[0].event_kind,
        run_id=recovered_events[0].run_id,
        occurrence_id=recovered_events[0].occurrence_id,
        semantic_subject=recovered_events[0].semantic_subject,
        producer_ordinal=recovered_events[0].producer_ordinal,
        payload={"tampered": "conflicting_payload"},
        event_id=recovered_events[0].event_id,
    )
    with pytest.raises(EventIdentityConflictError):
        recovered_log.append(conflicting_event)


def test_receipt_reproducibility_and_digest_immutability(tmp_path: Path) -> None:
    """Verifies that two identical sessions yield bit-for-bit identical receipt digests."""
    def _run_session(dir_name: str) -> AdversarialSessionProbeReceiptV1:
        probe = AdversarialSessionProbeV1(
            cas_dir=tmp_path / dir_name / "cas",
            event_log_dir=tmp_path / dir_name / "events",
            session_id="fixed_session_seed_123",
        )
        return probe.run_full_session()

    r1 = _run_session("run1")
    r2 = _run_session("run2")

    assert r1.receipt_sha256 == r2.receipt_sha256
    assert r1.total_turns == r2.total_turns
    assert r1.adversarial_attacks_quarantined == r2.adversarial_attacks_quarantined
