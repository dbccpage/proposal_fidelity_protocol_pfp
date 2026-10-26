"""Falsifier and specification tests for Part B & E: Inverse PageRank, Event Persistence, and E2E Fixtures.

Covers:
- F-RANK-01: Fitter child lifts parent more (q_c weighting in P<-).
- F-RANK-02: Verifier reconstructs transition matrix P<- to reject forged matrices.
- F-RANK-03: Solver budgets reported honestly (BUDGET_EXHAUSTED when limits exceeded).
- F-RES-03: Rank alone decides nothing (custody invariant under rank reversal).
- F-RES-04: Near-clones deduplicated before ranking to prevent sybil inflation.
- F-EVT-01: Producer-minted event_id ensures distinct acquisitions A & B survive.
- F-EVT-02: Same event_id with different payload raises EVENT_IDENTITY_CONFLICT.
- F-EVT-03: Lost or corrupted CAS objects raise CAS_OBJECT_MISSING / CAS_DIGEST_MISMATCH.
- F-EVT-04: Provider crash before capture records OUTCOME_UNKNOWN; retry needs authorization.
- F-EVT-05: Replaying captured responses performs zero provider calls.
- F-TX-01: Crash recovery replays event_log.jsonl to exact consistent projections.
- F-META-01: Meta proposals take effect only in future externally established evaluation epoch.
- F-E2E-01: Reference-only invariance (adding RetrievedPrecedent edge leaves rank unchanged).
- F-E2E-02: Witnessed descent (unwitnessed edge creates no inheritance edge or propagation).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def isolate_durable_storage(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate event log and CAS persistence per test under tmp_path."""
    monkeypatch.setattr(
        "omega_engine_operating_system.adapters.prompt_civ.event_log.DurableEventLogV1.DEFAULT_LOG_PATH",
        tmp_path / "event_log.jsonl",
    )
    monkeypatch.setattr(
        "omega_engine_operating_system.adapters.prompt_civ.cas.ContentAddressedStorageV1.DEFAULT_STORAGE_DIR",
        tmp_path / "cas",
    )
    monkeypatch.setattr(
        "omega_engine_operating_system.adapters.packet_seat.PacketSeatAdapterV1.DEFAULT_TURNS_DIR",
        tmp_path / "turns",
    )


def test_f_rank_01_fitter_child_lifts_parent_more() -> None:
    """F-RANK-01: Controlled single-parent test: higher child pass fraction q_c produces higher parent r_inv."""
    from omega_engine_operating_system.adapters.prompt_civ.rank import (
        AncestralRankCalculatorV1,
    )

    calc = AncestralRankCalculatorV1()

    # Case A: Child has pass fraction q_c = 1/10 (unfitter)
    rank_low_qc = calc.compute_inverse_rank(
        parent_id="P",
        child_id="C",
        child_pass_fraction=Fraction(1, 10),
    )

    # Case B: Child has pass fraction q_c = 9/10 (fitter)
    rank_high_qc = calc.compute_inverse_rank(
        parent_id="P",
        child_id="C",
        child_pass_fraction=Fraction(9, 10),
    )

    assert rank_high_qc > rank_low_qc, "Fitter child (higher q_c) must lift parent's r_inv more"


def test_f_rank_02_verifier_reconstructs_transition_matrix() -> None:
    """F-RANK-02: Verifier reconstructs P<- from bound graph and evidence to reject forged matrices."""
    from omega_engine_operating_system.adapters.prompt_civ.rank import (
        RankCertificateVerifierV1,
    )

    verifier = RankCertificateVerifierV1()

    bound_graph = {"nodes": ["P", "C"], "edges": [("P", "C")]}
    evidence = {"C": {"passes": 8, "failures": 2}}

    # Forged matrix P that satisfies fixed point equation r = 17/20 P^T r + 3/20 u
    # but does NOT match the graph and pass rates
    forged_matrix = [[Fraction(1, 2), Fraction(1, 2)], [Fraction(1, 2), Fraction(1, 2)]]
    candidate_r = [Fraction(1, 2), Fraction(1, 2)]

    with pytest.raises(ValueError, match="TRANSITION_MATRIX_RECONSTRUCTION_MISMATCH"):
        verifier.verify_certificate(
            graph=bound_graph,
            evidence=evidence,
            declared_transition_matrix=forged_matrix,
            candidate_rank=candidate_r,
        )


def test_f_rank_03_solver_budgets_reported_honestly() -> None:
    """F-RANK-03: Exceeding N <= 1000, E <= 5000, or bit-length 4096 returns BUDGET_EXHAUSTED."""
    from omega_engine_operating_system.adapters.prompt_civ.rank import (
        ExactRowReductionSolverV1,
    )

    solver = ExactRowReductionSolverV1(max_nodes=1000, max_edges=5000, max_bit_length=4096)

    # Exceed node budget (N = 1001)
    with pytest.raises(RuntimeError, match="BUDGET_EXHAUSTED"):
        solver.solve_fixed_point(num_nodes=1001, edges=[])


def test_f_res_03_rank_alone_decides_nothing() -> None:
    """F-RES-03: Holding subject bytes, evidence, and policy fixed, reversing rank leaves custody unchanged."""
    from omega_engine_epistemic_immune_system.domain.external_admission import (
        CustodyDecisionEngineV1,
    )

    engine = CustodyDecisionEngineV1()
    subject_bytes = b"def test_candidate(): pass"
    evidence_bundle = {"witness_count": 5, "passes": 5}

    # Decision under high rank
    decision_high_rank = engine.decide_custody(
        subject_bytes=subject_bytes,
        evidence=evidence_bundle,
        rank_score=Fraction(99, 100),
    )

    # Decision under low rank
    decision_low_rank = engine.decide_custody(
        subject_bytes=subject_bytes,
        evidence=evidence_bundle,
        rank_score=Fraction(1, 100),
    )

    assert decision_high_rank == decision_low_rank, "Rank alone must not decide custody"


def test_f_res_04_near_clones_deduplicated_before_ranking() -> None:
    """F-RES-04: Near-clones with identical (state, action) digests are deduplicated before ranking."""
    from omega_engine_operating_system.adapters.prompt_civ.rank import (
        AncestralRankCalculatorV1,
    )

    calc = AncestralRankCalculatorV1()

    # 1 legitimate descendant
    graph_single = [("Root", "Child1")]
    rank_single = calc.compute_community_rank(graph_single, root="Root")

    # Sybil attacker inserts 5 clone descendants with identical state/action digests
    graph_with_clones = [
        ("Root", "Child1"),
        ("Root", "Child_clone_1"),
        ("Root", "Child_clone_2"),
        ("Root", "Child_clone_3"),
    ]
    clone_digests = {
        "Child1": "digest_A",
        "Child_clone_1": "digest_A",  # Clone!
        "Child_clone_2": "digest_A",  # Clone!
        "Child_clone_3": "digest_A",  # Clone!
    }

    rank_deduped = calc.compute_community_rank(
        graph_with_clones,
        root="Root",
        genome_action_digests=clone_digests,
    )

    assert rank_single == rank_deduped, "Sybil clones must be deduplicated and not inflate ancestral rank"


def test_f_evt_01_event_identity_separate_from_payload() -> None:
    """F-EVT-01: Producer-minted event_id prevents collisions; identical replay is idempotent no-op."""
    from omega_engine_operating_system.adapters.prompt_civ.event_log import (
        DurableEventLogV1,
        PromptCivEventV1,
    )

    log = DurableEventLogV1()

    # Two distinct acquisitions at the same prompt occurrence
    evt_acq_a = PromptCivEventV1(
        producer_id="oeeis_seeder",
        event_kind="ImmunityAcquisition",
        run_id="run-10",
        occurrence_id="occ-10",
        semantic_subject="ab_rule_alpha",
        producer_ordinal=1,
        payload={"antibody_id": "ab_alpha"},
    )
    evt_acq_b = PromptCivEventV1(
        producer_id="oeeis_seeder",
        event_kind="ImmunityAcquisition",
        run_id="run-10",
        occurrence_id="occ-10",
        semantic_subject="ab_rule_beta",  # Different subject
        producer_ordinal=2,
        payload={"antibody_id": "ab_beta"},
    )

    assert evt_acq_a.event_id != evt_acq_b.event_id, "Event IDs must not collide"

    log.append_event(evt_acq_a)
    log.append_event(evt_acq_b)
    assert log.event_count() == 2

    # Idempotent replay of evt_acq_a with identical bytes
    log.append_event(evt_acq_a)
    assert log.event_count() == 2, "Identical replay must be an idempotent no-op"


def test_f_evt_02_same_id_different_bytes_is_conflict() -> None:
    """F-EVT-02: Same event_id with different payload raises EVENT_IDENTITY_CONFLICT."""
    from omega_engine_operating_system.adapters.prompt_civ.event_log import (
        DurableEventLogV1,
        EventIdentityConflictError,
        PromptCivEventV1,
    )

    log = DurableEventLogV1()
    original_evt = PromptCivEventV1(
        producer_id="prod_1",
        event_kind="CustodyDecision",
        run_id="run-1",
        occurrence_id="occ-1",
        semantic_subject="sub-1",
        producer_ordinal=1,
        payload={"custody": "Candidate"},
    )
    log.append_event(original_evt)

    # Tampered event with same event_id but different payload
    tampered_evt = PromptCivEventV1(
        producer_id="prod_1",
        event_kind="CustodyDecision",
        run_id="run-1",
        occurrence_id="occ-1",
        semantic_subject="sub-1",
        producer_ordinal=1,
        payload={"custody": "HumanAdmitted"},  # Changed payload!
    )
    # Force identical event_id
    tampered_evt.event_id = original_evt.event_id

    with pytest.raises(EventIdentityConflictError, match="EVENT_IDENTITY_CONFLICT"):
        log.append_event(tampered_evt)


def test_f_evt_03_cas_objects_durable_source_artifacts() -> None:
    """F-EVT-03: Missing or corrupted CAS objects raise CAS_OBJECT_MISSING or CAS_DIGEST_MISMATCH."""
    from omega_engine_operating_system.adapters.prompt_civ.cas import (
        ContentAddressedStorageV1,
    )

    cas = ContentAddressedStorageV1()
    data = b"Prompt text canonical bytes"
    sha = cas.store(data)

    # Corrupt storage internally
    cas.corrupt_object_bytes_for_testing(sha)

    with pytest.raises(ValueError, match="CAS_DIGEST_MISMATCH"):
        cas.retrieve(sha)

    # Missing object
    with pytest.raises(FileNotFoundError, match="CAS_OBJECT_MISSING"):
        cas.retrieve("sha256:non_existent_hash")


def test_f_evt_04_unknown_provider_outcomes_handled_honestly() -> None:
    """F-EVT-04: Crash after SENT and before capture recorded as OUTCOME_UNKNOWN; retry requires authorization."""
    from omega_engine_operating_system.adapters.packet_seat import (
        PacketSeatAdapterV1,
    )

    seat = PacketSeatAdapterV1()
    seat.record_attempt_sent(attempt_id="att_001")

    # Crash happens before response captured
    status = seat.get_attempt_status("att_001")
    assert status == "OUTCOME_UNKNOWN"

    # Unauthorized retry attempt without idempotency key or RetryAuthorizedV1 is refused
    with pytest.raises(PermissionError, match="RETRY_AUTHORIZATION_REQUIRED"):
        seat.retry_attempt("att_001", retry_authorization=None)


def test_f_evt_05_replaying_captured_responses_makes_zero_provider_calls() -> None:
    """F-EVT-05: Replaying projections after RESPONSE_CAPTURED performs zero provider calls."""
    from omega_engine_operating_system.adapters.packet_seat import (
        PacketSeatAdapterV1,
        ProviderCallSpy,
    )

    spy = ProviderCallSpy()
    seat = PacketSeatAdapterV1(provider_gateway=spy)

    # First execution captures response
    seat.execute_turn(body="Integrate x^2", turn_id="turn_01")
    assert spy.call_count == 1

    # Replaying projection from event log and CAS performs 0 calls
    seat.replay_projections_from_log(turn_id="turn_01")
    assert spy.call_count == 1, "Replaying projections must make zero additional provider calls"


def test_f_tx_01_crash_recovery_replays_event_log_to_consistent_state() -> None:
    """F-TX-01: Crash between log append and projection recovers exact state without duplicated evidence."""
    from omega_engine_operating_system.adapters.prompt_civ.persistence import (
        PromptCivProjectionEngineV1,
    )

    engine = PromptCivProjectionEngineV1()
    engine.record_event({"event_id": "evt_1", "kind": "ExecutionPass", "prompt_id": "p1"})
    engine.record_event({"event_id": "evt_2", "kind": "ExecutionPass", "prompt_id": "p1"})

    # Simulate crash before projections are written
    recovered_projections = engine.recover_from_crash()

    assert recovered_projections["p1"].pass_count == 2
    assert recovered_projections.is_consistent is True


def test_f_meta_01_meta_proposals_take_effect_only_in_future_external_epoch() -> None:
    """F-META-01: MetaOperatorProposalV1 takes effect only in future external epoch; cannot change own checkers."""
    from omega_engine_operating_system.adapters.prompt_civ.forge import (
        MetaOperatorProposalV1,
        MetaProposalRegistryV1,
    )

    registry = MetaProposalRegistryV1(current_epoch=5)

    proposal = MetaOperatorProposalV1(
        proposal_id="meta_checker_switch_01",
        proposed_checker_set="checker_set_v2",
        target_evaluation_epoch=6,  # Future epoch!
    )
    registry.register_proposal(proposal)

    # Current epoch 5 evaluation must use frozen epoch 5 checker set, not proposed one
    active_checker = registry.get_active_checker_set(for_epoch=5)
    assert active_checker == "checker_set_v1"
    assert active_checker != "checker_set_v2", "Meta proposal must not alter current epoch checker set"


def test_f_e2e_01_reference_only_invariance() -> None:
    """F-E2E-01: Adding RetrievedPrecedent edge leaves rank and inherited immunity byte-identical."""
    from omega_engine_operating_system.adapters.prompt_civ.e2e import (
        PromptCivE2EFixtureV1,
    )

    fixture = PromptCivE2EFixtureV1()
    snapshot_before = fixture.capture_rank_and_immunity_snapshot()

    # Add only a RetrievedPrecedent reference edge (all genomes, evidence, policies frozen)
    fixture.add_reference_edge(source="genome_b", target="genome_a")
    snapshot_after = fixture.capture_rank_and_immunity_snapshot()

    assert snapshot_before.rank_digest == snapshot_after.rank_digest
    assert snapshot_before.immunity_digest == snapshot_after.immunity_digest


def test_f_e2e_02_witnessed_descent() -> None:
    """F-E2E-02: Without causal witness, no edge or propagation exists; with witness, propagation reaches parent."""
    from omega_engine_operating_system.adapters.prompt_civ.e2e import (
        PromptCivE2EFixtureV1,
    )
    from omega_engine_prompt_civilization.domain.causal_witness import seal_causal_witness

    fixture = PromptCivE2EFixtureV1()

    # 1. Unwitnessed mutation: no edge, no propagation
    result_unwitnessed = fixture.attempt_mutation(
        parent="G",
        child_candidate="G_child",
        witness_receipt=None,
    )
    assert result_unwitnessed.edge_created is False
    assert result_unwitnessed.propagation_count == 0

    # 2. Witnessed mutation: edge created, backward propagation at d=1 with weight 1/2
    result_witnessed = fixture.attempt_mutation(
        parent="G",
        child_candidate="G_child",
        witness_receipt=seal_causal_witness({"edge": "mutation_realized"}),
    )
    assert result_witnessed.edge_created is True
    assert result_witnessed.propagation_count == 1
    assert result_witnessed.parent_propagation_weight == Fraction(1, 2)
