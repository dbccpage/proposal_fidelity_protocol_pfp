"""Comprehensive unit, integration, and mutation-resistance test suite.

Verifies complete coverage across all Prompt Civilization adapters:
- backfill.py: PromptCivBackfillEngineV1, BackfillReceiptV1
- rank.py: ExactRowReductionSolverV1, RankCertificateVerifierV1, ancestral_rank
- packet_seat.py: PacketSeatAdapterV1 disk recovery, limits, retries, replay
- event_log.py: DurableEventLogV1 persistence, recovery, conflict detection
- fitness.py: PromptFitnessCalculatorV1, ParetoFrontSelectorV1, ComparativeClaimAuditorV1
- genealogy.py: LineageGraphV1 acyclicity, descent derivation, witness enforcement
- forge.py: GenomeMutationForgeV1 boundary protection, PopulationPolicyV1, MetaProposalRegistryV1
- record.py: PromptGenomeV1 immutability, generation derivation, registry occurrences
- cas.py: CasStoreV1 cold retrieval from disk, digest verification, corruption detection
- matching.py: ReferenceTrailEvaporationCalculatorV1, is_candidate_eligible
- immunity.py: BackwardPropagationEngineV1, DAGHopDistanceCalculatorV1, GlobalCustodyRegistryV1
- domain.py: hard_domain_eligible predicates

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType

import pytest

from operating_system.adapters.packet_seat import (
    PacketSeatAdapterV1,
    ProviderCallSpy,
    RetryAuthorizedV1,
)
from operating_system.adapters.prompt_civ.backfill import (
    BackfillReceiptV1,
    PromptCivBackfillEngineV1,
)
from operating_system.adapters.prompt_civ.cas import ContentAddressedStorageV1
from operating_system.adapters.prompt_civ.domain import (
    DomainPlacementV1,
    hard_domain_eligible,
)
from operating_system.adapters.prompt_civ.event_log import (
    DurableEventLogV1,
    EventIdentityConflictError,
    PromptCivEventV1,
)
from operating_system.adapters.prompt_civ.fitness import (
    ComparativeClaimAuditorV1,
    ParetoFrontSelectorV1,
    PromptFitnessCalculatorV1,
)
from operating_system.adapters.prompt_civ.forge import (
    MetaOperatorProposalV1,
    MetaProposalRegistryV1,
    PopulationPolicyV1,
    PromptMutationEngineV1,
)
from operating_system.adapters.prompt_civ.genealogy import (
    LineageGraphV1,
    RelationshipType,
)
from operating_system.adapters.prompt_civ.immunity import (
    DAGHopDistanceCalculatorV1,
    GlobalCustodyRegistryV1,
    ImmunityPropagationEngineV1,
    LineageTaintEngineV1,
)
from operating_system.adapters.prompt_civ.matching import (
    ReferenceTrailEvaporationCalculatorV1,
    is_candidate_eligible,
)
from operating_system.adapters.prompt_civ.rank import (
    AncestralRankCalculatorV1,
    ExactRowReductionSolverV1,
    RankCertificateVerifierV1,
    reconstruct_transition_matrix,
)
from operating_system.adapters.prompt_civ.record import (
    PromptGenomeRegistryV1,
    PromptGenomeV1,
    PromptViewEngineV1,
    PromptViewV1,
    ProtectedSpanV1,
)

# ==============================================================================
# 1. Backfill Adapter Tests (PromptCivBackfillEngineV1)
# ==============================================================================

def test_backfill_default_and_env_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("CORE_INTELLIGENCE_ROOT", raising=False)
    engine_default = PromptCivBackfillEngineV1()
    assert engine_default.intelligence_root == Path("_intelligence")

    monkeypatch.setenv("CORE_INTELLIGENCE_ROOT", str(tmp_path / "env_intel"))
    engine_env = PromptCivBackfillEngineV1()
    assert engine_env.intelligence_root == tmp_path / "env_intel"


def test_backfill_nonexistent_directory(tmp_path: Path) -> None:
    non_existent = tmp_path / "does_not_exist"
    engine = PromptCivBackfillEngineV1(intelligence_root=non_existent)
    receipt = engine.run_backfill()

    assert isinstance(receipt, BackfillReceiptV1)
    assert receipt.genomes_created == 0
    assert receipt.occurrences_recorded == 0
    assert receipt.antibodies_indexed == 0
    assert receipt.antibodies_refused == 0
    assert receipt.receipt_kind == "EXPLORATORY"
    assert receipt.authority_effect == "None"
    assert receipt.receipt_sha256.startswith("sha256:")


def test_backfill_empty_directory(tmp_path: Path) -> None:
    empty_root = tmp_path / "empty_root"
    empty_root.mkdir()
    engine = PromptCivBackfillEngineV1(intelligence_root=empty_root)
    receipt = engine.run_backfill()

    assert receipt.genomes_created == 0
    assert receipt.occurrences_recorded == 0
    assert receipt.antibodies_indexed == 0
    assert receipt.antibodies_refused == 0


def test_backfill_comprehensive_traversal_and_idempotence(tmp_path: Path) -> None:
    intel_root = tmp_path / "intel_root"
    sub_dir = intel_root / "sub_category"
    sub_dir.mkdir(parents=True)

    # 1. JSONL file with valid, placeholder, blank, and corrupted lines
    jsonl_file = sub_dir / "telemetry.jsonl"
    jsonl_content = "\n".join([
        json.dumps({"prompt_id": "p_001", "prompt_text": "First prompt", "occurrence_id": "occ_001", "defect_id": "defect_normal_1"}),
        "   ",  # Blank line
        json.dumps({"prompt_id": "p_002", "prompt_text": "Second prompt", "antibody_id": "placeholder_antibody_v1"}),  # Refused placeholder
        "CORRUPTED_JSON_NOT_VALID",
        json.dumps("JUST_A_STRING_NOT_DICT"),
        json.dumps({"defect_id": "defect:defect:nested_phantom"}),  # Refused phantom
        json.dumps({"prompt_id": "p_003", "prompt_text": "Third prompt", "occurrence_id": "occ_002", "antibody_id": "ab_valid_1"}),
    ])
    jsonl_file.write_text(jsonl_content, encoding="utf-8")

    # 2. JSON file with single dict
    json_file = sub_dir / "summary.json"
    json_content = json.dumps({"prompt_id": "p_004", "prompt_text": "Fourth prompt", "occurrence_id": "occ_003", "defect_id": "defect_normal_2"})
    json_file.write_text(json_content, encoding="utf-8")

    # 3. Non-json file (should be ignored)
    txt_file = sub_dir / "notes.txt"
    txt_file.write_text("plain text notes", encoding="utf-8")

    # 4. Binary invalid utf-8 json file (hits read exception branch)
    bad_json = sub_dir / "bad_bytes.json"
    bad_json.write_bytes(b"\x80\x81\x82\x83")

    engine = PromptCivBackfillEngineV1(intelligence_root=intel_root)
    receipt_1 = engine.run_backfill()

    # Genomes: p_001, p_002, p_003, p_004 -> 4
    # Occurrences: occ_001, occ_002, occ_003 -> 3
    # Antibodies indexed: defect_normal_1, ab_valid_1, defect_normal_2 -> 3
    # Antibodies refused: placeholder_antibody_v1, defect:defect:nested_phantom -> 2
    assert receipt_1.genomes_created == 4
    assert engine.registry.total_genome_count() == 4
    assert receipt_1.occurrences_recorded == 3
    assert receipt_1.antibodies_indexed == 3
    assert receipt_1.antibodies_refused == 2

    # Run again on same engine -> idempotent (no accumulation)
    receipt_2 = engine.run_backfill()
    assert receipt_2.genomes_created == 4
    assert receipt_2.occurrences_recorded == 3
    assert receipt_2.antibodies_indexed == 3
    assert receipt_2.antibodies_refused == 2
    assert receipt_2.receipt_sha256 == receipt_1.receipt_sha256


# ==============================================================================
# 2. Rank & Exact Solver Tests (ExactRowReductionSolverV1, RankCertificateVerifierV1)
# ==============================================================================

def test_rank_ancestral_and_empty_transitions() -> None:
    calc = AncestralRankCalculatorV1()
    # num_distinct == 0 returns Fraction(3, 20)
    assert calc.compute_community_rank([], "root_a") == Fraction(3, 20)

    # Empty node list returns empty matrix
    assert reconstruct_transition_matrix([], []) == []


def test_exact_row_reduction_solver_limits() -> None:
    solver = ExactRowReductionSolverV1(max_nodes=3, max_edges=3, max_bit_length=10)

    # Limit exceeded on nodes
    with pytest.raises(RuntimeError, match="BUDGET_EXHAUSTED: Solver limits exceeded"):
        solver.solve_fixed_point(4, [("A", "B")])

    # Limit exceeded on edges
    with pytest.raises(RuntimeError, match="BUDGET_EXHAUSTED: Solver limits exceeded"):
        solver.solve_fixed_point(2, [("A", "B"), ("B", "A"), ("A", "A"), ("B", "B")])

    # Zero nodes returns empty list
    assert solver.solve_fixed_point(0, []) == []

    # Solver fills default node names when edge list has fewer nodes than num_nodes
    solver_empty = ExactRowReductionSolverV1(max_nodes=10, max_edges=10)
    rank_3 = solver_empty.solve_fixed_point(3, [])
    assert len(rank_3) == 3
    assert all(r == Fraction(1, 3) for r in rank_3)


def test_exact_row_reduction_solver_bit_length_limit() -> None:
    # Intentionally tiny max_bit_length to trigger coefficient explosion guard
    solver = ExactRowReductionSolverV1(max_nodes=10, max_edges=10, max_bit_length=2)
    with pytest.raises(RuntimeError, match="BUDGET_EXHAUSTED: Coefficient bit-length exceeded"):
        solver.solve_fixed_point(2, [("A", "B")])


def test_exact_solver_and_rank_certificate_verifier_integration() -> None:
    nodes = ["node_a", "node_b"]
    edges = [("node_a", "node_b")]
    evidence = {
        "node_a": {"passes": 1, "failures": 1},
        "node_b": {"passes": 2, "failures": 0},
    }

    # 1. Reconstruct transition matrix
    p_mat = reconstruct_transition_matrix(nodes, edges, evidence)
    assert len(p_mat) == 2
    assert len(p_mat[0]) == 2

    # 2. Solve exact fixed point
    solver = ExactRowReductionSolverV1(max_nodes=10, max_edges=20, max_bit_length=4096)
    rank_vec = solver.solve_fixed_point(2, edges, evidence=evidence, alpha=Fraction(17, 20))

    assert len(rank_vec) == 2
    assert sum(rank_vec) == Fraction(1, 1)

    # 3. Verify certificate with RankCertificateVerifierV1
    verifier = RankCertificateVerifierV1()
    is_valid = verifier.verify_certificate(
        graph={"nodes": nodes, "edges": edges},
        evidence=evidence,
        declared_transition_matrix=p_mat,
        candidate_rank=rank_vec,
        alpha=Fraction(17, 20),
    )
    assert is_valid is True

    # 4. Verifier rejection branches
    # Mismatched rank length
    assert verifier.verify_certificate(
        graph={"nodes": nodes, "edges": edges},
        evidence=evidence,
        declared_transition_matrix=p_mat,
        candidate_rank=[Fraction(1, 1)],
    ) is False

    # Negative entry in candidate rank
    assert verifier.verify_certificate(
        graph={"nodes": nodes, "edges": edges},
        evidence=evidence,
        declared_transition_matrix=p_mat,
        candidate_rank=[Fraction(-1, 10), Fraction(11, 10)],
    ) is False

    # Non-stochastic sum != 1
    assert verifier.verify_certificate(
        graph={"nodes": nodes, "edges": edges},
        evidence=evidence,
        declared_transition_matrix=p_mat,
        candidate_rank=[Fraction(1, 2), Fraction(1, 3)],
    ) is False

    # Mismatched matrix row dimension
    assert verifier.verify_certificate(
        graph={"nodes": nodes, "edges": edges},
        evidence=evidence,
        declared_transition_matrix=[p_mat[0]],
        candidate_rank=rank_vec,
    ) is False

    # Mismatched matrix column dimension
    assert verifier.verify_certificate(
        graph={"nodes": nodes, "edges": edges},
        evidence=evidence,
        declared_transition_matrix=[[Fraction(1, 1)], [Fraction(1, 1)]],
        candidate_rank=rank_vec,
    ) is False

    # Declared matrix entry mismatch raises ValueError
    corrupt_mat = [[Fraction(1, 1), Fraction(0, 1)], [Fraction(0, 1), Fraction(1, 1)]]
    with pytest.raises(ValueError, match="TRANSITION_MATRIX_RECONSTRUCTION_MISMATCH"):
        verifier.verify_certificate(
            graph={"nodes": nodes, "edges": edges},
            evidence=evidence,
            declared_transition_matrix=corrupt_mat,
            candidate_rank=rank_vec,
        )

    # Wrong rank vector that sums to 1 but fails fixed-point equation returns False
    perturbed_rank = [Fraction(1, 2), Fraction(1, 2)]
    if perturbed_rank != rank_vec:
        assert verifier.verify_certificate(
            graph={"nodes": nodes, "edges": edges},
            evidence=evidence,
            declared_transition_matrix=p_mat,
            candidate_rank=perturbed_rank,
        ) is False


# ==============================================================================
# 3. Packet Seat Adapter & Ingress/Replay Tests (PacketSeatAdapterV1)
# ==============================================================================

def test_packet_seat_limits_and_replay(tmp_path: Path) -> None:
    spy = ProviderCallSpy()
    spy.mock_reply_size = 11
    adapter = PacketSeatAdapterV1(provider_gateway=spy, storage_dir=tmp_path / "turns")

    # Ingress prompt limit exceeded
    oversized_prompt = "x" * (64 * 1024 + 1)
    with pytest.raises(ValueError, match="REQUEST_PROMPT_LIMIT_EXCEEDED"):
        adapter.prepare_and_send(prompt=oversized_prompt)

    # Attempt status query for unknown attempt
    assert adapter.get_attempt_status("unknown_att") == "UNKNOWN"

    # Attempt status for sent attempt
    adapter.record_attempt_sent("att_001")
    assert adapter.get_attempt_status("att_001") == "OUTCOME_UNKNOWN"

    # Retry authorization validation
    with pytest.raises(PermissionError, match="RETRY_AUTHORIZATION_REQUIRED"):
        adapter.retry_attempt("att_001", retry_authorization=None)

    class InvalidAuth:
        pass

    with pytest.raises(PermissionError, match="INVALID_RETRY_AUTHORIZATION"):
        adapter.retry_attempt("att_001", retry_authorization=InvalidAuth())

    # Valid retry authorization
    adapter.retry_attempt("att_001", retry_authorization=RetryAuthorizedV1("att_001", "auth_hash_1"))
    assert adapter.get_attempt_status("att_001") == "RETRY_AUTHORIZED"

    # Execute turn writes turn file to disk and cache
    reply = adapter.execute_turn("test body", "turn_123")
    assert reply == "x" * 11
    assert (tmp_path / "turns" / "turn_123.turn").exists()

    # Replay from in-memory cache
    assert adapter.replay_projections_from_log("turn_123") == "x" * 11

    # Replay from cold disk (new adapter instance pointing to same storage_dir)
    cold_adapter = PacketSeatAdapterV1(provider_gateway=spy, storage_dir=tmp_path / "turns")
    # Verify disk loader loaded turn_123
    assert cold_adapter.replay_projections_from_log("turn_123") == "x" * 11

    # Clear memory cache to hit direct disk read branch in replay_projections_from_log
    cold_adapter._captured_turns.clear()
    assert cold_adapter.replay_projections_from_log("turn_123") == "x" * 11

    # Missing turn raises KeyError
    with pytest.raises(KeyError, match="Turn non_existent not found in log"):
        cold_adapter.replay_projections_from_log("non_existent")


# ==============================================================================
# 4. Durable Event Log Tests (DurableEventLogV1)
# ==============================================================================

def test_event_log_persistence_recovery_and_conflict(tmp_path: Path) -> None:
    # 1. Custom log file initialization
    custom_log = tmp_path / "events.jsonl"
    log = DurableEventLogV1(log_file=custom_log)

    evt1 = PromptCivEventV1(
        producer_id="prod_a",
        event_kind="OCCURRENCE",
        run_id="run_1",
        occurrence_id="occ_1",
        semantic_subject="sub_1",
        producer_ordinal=1,
        payload={"data": "abc"},
        event_id="evt_001",
    )
    log.append_event(evt1)
    assert log.event_count() == 1
    assert log.get_event("evt_001").event_id == "evt_001"

    # 2. Idempotent replay of identical payload is no-op
    log.append_event(evt1)
    assert log.event_count() == 1

    # 3. Same event_id with conflicting payload raises EventIdentityConflictError
    conflicting_evt = PromptCivEventV1(
        producer_id="prod_a",
        event_kind="OCCURRENCE",
        run_id="run_1",
        occurrence_id="occ_1",
        semantic_subject="sub_1",
        producer_ordinal=1,
        payload={"data": "DIFFERENT_CONFLICTING_DATA"},
        event_id="evt_001",
    )
    with pytest.raises(EventIdentityConflictError, match="EVENT_IDENTITY_CONFLICT"):
        log.append_event(conflicting_evt)

    # 4. Recovery from disk with whitespace and corrupted line
    with custom_log.open("a", encoding="utf-8") as f:
        f.write("\n\nMALFORMED_LINE\n")

    reloaded_log = DurableEventLogV1(log_file=custom_log)
    assert reloaded_log.event_count() == 1
    assert reloaded_log.get_event("evt_001").payload == {"data": "abc"}

    # 5. Log dir initialization branch
    dir_log = DurableEventLogV1(log_dir=tmp_path / "log_dir")
    assert dir_log.log_file == tmp_path / "log_dir" / "event_log.jsonl"


# ==============================================================================
# 5. Fitness & Pareto Selection Tests (PromptFitnessCalculatorV1, ParetoFrontSelectorV1)
# ==============================================================================

def test_fitness_obligations_and_pareto() -> None:
    calc = PromptFitnessCalculatorV1()

    # extract_gate_success_credit returns 0 regardless of status
    class MockReceipt:
        def __init__(self, gate_status: str) -> None:
            self.gate_status = gate_status

    assert calc.extract_success_credit(MockReceipt("AUTHORIZED")) == 0
    assert calc.extract_success_credit(MockReceipt("REFUSED")) == 0

    # extract_obligation_success_credit
    # 1. Mismatched obligation
    assert calc.extract_obligation_success_credit("ob_1", {"obligation_id": "ob_2"}) == 0
    # 2. Matching obligation but missing sealed digest
    assert calc.extract_obligation_success_credit(
        "ob_1", {"obligation_id": "ob_1", "verifier_status": "VERIFIED_EXACT"}
    ) == 0
    # 3. A caller dict earns no credit. A self-seal whose body says VERIFIED_EXACT does not either.
    assert calc.extract_obligation_success_credit(
        "ob_1",
        {"obligation_id": "ob_1", "sealed_receipt_digest": "sha_123", "verifier_status": "VERIFIED_EXACT"},
    ) == 0
    from pciv.domain.causal_witness import seal_causal_witness

    assert calc.extract_obligation_success_credit(
        "ob_1",
        seal_causal_witness({"obligation_id": "ob_1", "verifier_status": "VERIFIED_EXACT"}),
    ) == 0
    # 4. Matching obligation, sealed digest, but non-exact status -> 0
    assert calc.extract_obligation_success_credit(
        "ob_1",
        {"obligation_id": "ob_1", "sealed_receipt_digest": "sha_123", "verifier_status": "SYNTAX_ONLY"},
    ) == 0

    # compute_execution_metrics: a caller receipt is not a bound checker.
    exact_metrics = calc.compute_execution_metrics({
        "payload": "non-empty-valid-code",
        "exact_verifier_receipt": {"status": "ok"},
        "syntax_valid": False,
    })
    assert exact_metrics.success_credit == 0
    assert exact_metrics.is_empty_or_syntax_only is False

    # ParetoFrontSelectorV1
    selector = ParetoFrontSelectorV1()
    assert selector.partition_fronts([]) == []

    # ComparativeClaimAuditorV1
    auditor = ComparativeClaimAuditorV1()
    # Non-comparative claim passes
    assert auditor.evaluate_claim(claim_type="ABSOLUTE", has_held_out_split=False) is True

    # Comparative claim requires holdout split
    with pytest.raises(ValueError, match="COMPARATIVE_CLAIM_HOLDOUT_REQUIRED"):
        auditor.evaluate_claim(claim_type="COMPARATIVE_BENEFIT", has_held_out_split=False)

    # Comparative claim requires multiplicity correction
    with pytest.raises(ValueError, match="COMPARATIVE_CLAIM_MULTIPLICITY_REQUIRED"):
        auditor.evaluate_claim(
            claim_type="COMPARATIVE_BENEFIT",
            has_held_out_split=True,
            multiplicity_correction=None,
        )

    # Valid comparative claim
    assert auditor.evaluate_claim(
        claim_type="COMPARATIVE_BENEFIT",
        has_held_out_split=True,
        multiplicity_correction="BONFERRONI",
    ) is True


# ==============================================================================
# 6. Genealogy & Lineage DAG Tests (LineageGraphV1)
# ==============================================================================

def test_lineage_graph_dag_path_and_cycle_prevention() -> None:
    dag = LineageGraphV1()

    # Reflexive path check
    assert dag.has_path("node_a", "node_a") is True
    assert dag.has_path("node_a", "node_b") is False

    # Non-causal / unauthorized relationship rejected
    with pytest.raises(ValueError, match="CAUSAL_WITNESS_REQUIRED"):
        dag.add_edge("node_a", "node_b", "UNAUTHORIZED_RELATION")

    # Inheritance relationship without witness receipt rejected
    with pytest.raises(ValueError, match="CAUSAL_WITNESS_REQUIRED"):
        dag.add_edge("node_a", "node_b", RelationshipType.DIRECT_MUTATION, witness_receipt=None)

    with pytest.raises(ValueError, match="CAUSAL_WITNESS_REQUIRED"):
        dag.add_edge(
            "node_a",
            "node_b",
            RelationshipType.DIRECT_MUTATION,
            witness_receipt={"unverified": True},
        )

    from pciv.domain.causal_witness import seal_causal_witness

    # Add valid witnessed inheritance edge A -> B
    dag.add_edge(
        "node_a",
        "node_b",
        RelationshipType.DIRECT_MUTATION,
        witness_receipt=seal_causal_witness(
            {"parent_id": "node_a", "child_id": "node_b", "edge": "ab"}
        ),
    )
    assert dag.has_inheritance_edge("node_a", "node_b") is True
    assert dag.has_path("node_a", "node_b") is True

    # Add witnessed inheritance edge B -> C
    dag.add_edge(
        "node_b",
        "node_c",
        RelationshipType.DIRECT_MUTATION,
        witness_receipt=seal_causal_witness(
            {"parent_id": "node_b", "child_id": "node_c", "edge": "bc"}
        ),
    )
    assert dag.has_path("node_a", "node_c") is True

    # Cycle detection: attempt C -> A inheritance
    with pytest.raises(ValueError, match="LINEAGE_CYCLE_REFUSED"):
        dag.add_edge(
            "node_c",
            "node_a",
            RelationshipType.DIRECT_MUTATION,
            witness_receipt=seal_causal_witness(
                {"parent_id": "node_c", "child_id": "node_a", "edge": "ca"}
            ),
        )

    # derive_descent_path
    assert dag.derive_descent_path("node_a", "node_a") == ["node_a"]
    assert dag.derive_descent_path("node_a", "node_c") == ["node_a", "node_b", "node_c"]

    # Disconnected pair raises ValueError
    with pytest.raises(ValueError, match="DESCENT_REQUIRES_INHERITANCE_EDGE"):
        dag.derive_descent_path("node_c", "node_a")


# ==============================================================================
# 7. Forge, Population Policy & Meta Proposals (PromptMutationEngineV1, etc.)
# ==============================================================================

def test_forge_mutation_bounds_and_span_protection() -> None:
    forge = PromptMutationEngineV1()
    content = b"0123456789"
    spans = [ProtectedSpanV1("core", 3, 7)]

    # Out of bounds
    with pytest.raises(ValueError, match="INDEX_OUT_OF_BOUNDS"):
        forge.apply_mutation(
            original_bytes=content,
            protected_spans=spans,
            edit_start_byte=-1,
            edit_end_byte=5,
            replacement_bytes=b"x",
        )

    with pytest.raises(ValueError, match="INDEX_OUT_OF_BOUNDS"):
        forge.apply_mutation(
            original_bytes=content,
            protected_spans=spans,
            edit_start_byte=5,
            edit_end_byte=2,
            replacement_bytes=b"x",
        )

    with pytest.raises(ValueError, match="INDEX_OUT_OF_BOUNDS"):
        forge.apply_mutation(
            original_bytes=content,
            protected_spans=spans,
            edit_start_byte=0,
            edit_end_byte=15,
            replacement_bytes=b"x",
        )

    # Overlap with protected span
    with pytest.raises(PermissionError, match="PROTECTED_SPAN_MUTATION_REFUSED"):
        forge.apply_mutation(
            original_bytes=content,
            protected_spans=spans,
            edit_start_byte=2,
            edit_end_byte=5,
            replacement_bytes=b"xxx",
        )

    # Zero-width insertion strictly inside protected span
    with pytest.raises(PermissionError, match="PROTECTED_SPAN_MUTATION_REFUSED"):
        forge.apply_mutation(
            original_bytes=content,
            protected_spans=spans,
            edit_start_byte=5,
            edit_end_byte=5,
            replacement_bytes=b"insert",
        )

    # Valid mutation before span
    mutated = forge.apply_mutation(
        original_bytes=content,
        protected_spans=spans,
        edit_start_byte=0,
        edit_end_byte=2,
        replacement_bytes=b"AB",
    )
    assert mutated == b"AB23456789"


def test_population_policy_reserves() -> None:
    policy = PopulationPolicyV1()

    # Cap <= 0 returns all 0
    assert policy.allocate_reserves(0) == {"Front": 0, "Unmeasured": 0, "Baseline": 0}
    assert policy.allocate_reserves(-5) == {"Front": 0, "Unmeasured": 0, "Baseline": 0}

    # N=10 returns exact 6/3/1
    assert policy.allocate_reserves(10) == {"Front": 6, "Unmeasured": 3, "Baseline": 1}

    # N=20 allocates 12/6/2
    alloc_20 = policy.allocate_reserves(20)
    assert sum(alloc_20.values()) == 20
    assert alloc_20 == {"Front": 12, "Unmeasured": 6, "Baseline": 2}


def test_meta_proposal_registry() -> None:
    registry = MetaProposalRegistryV1(current_epoch=1, default_checker="default_v1")
    proposal = MetaOperatorProposalV1("prop_1", "checker_v2", target_evaluation_epoch=2)
    registry.register_proposal(proposal)

    # Future epoch without external enactment is refused
    assert registry.get_active_checker_set(2) == "Future epoch requires authenticated external enactment"

    # Enact epoch 2
    registry.enact_epoch(2)
    assert registry.get_active_checker_set(2) == "checker_v2"

    # Enact epoch 3 with no proposal returns default
    registry.enact_epoch(3)
    assert registry.get_active_checker_set(3) == "default_v1"


# ==============================================================================
# 8. Record & Immutability Tests (PromptGenomeV1, PromptGenomeRegistryV1)
# ==============================================================================

def test_protected_span_bounds_validation() -> None:
    with pytest.raises(ValueError, match="Invalid byte span"):
        ProtectedSpanV1("invalid", -1, 5)

    with pytest.raises(ValueError, match="Invalid byte span"):
        ProtectedSpanV1("invalid", 5, 2)


def test_prompt_genome_creation_and_registry() -> None:
    # 1. Generation mismatch with parents
    with pytest.raises(ValueError, match="DERIVED_FIELD_MISMATCH"):
        PromptGenomeV1.create_verified(
            source_packet_refs=[{"packet_id": "pkt_1"}],
            domain_model={"domain": "math"},
            parents=[],
            declared_generation=1,  # Expected 0
        )

    # 2. Unknown boundary name
    with pytest.raises(ValueError, match="PROTECTED_BOUNDARY_UNRESOLVED"):
        PromptGenomeV1.create_verified(
            source_packet_refs=[{"packet_id": "pkt_1"}],
            domain_model={"domain": "math"},
            parents=[],
            declared_generation=0,
            protected_spans=[ProtectedSpanV1("unknown_boundary", 0, 10)],
        )

    # 3. Valid creation
    genome = PromptGenomeV1.create_verified(
        source_packet_refs=[{"packet_id": "pkt_1"}],
        domain_model={"domain": "math"},
        parents=[],
        declared_generation=0,
    )
    assert genome.prompt_id.startswith("genome_")
    assert isinstance(genome.domain_model, MappingProxyType)

    # 4. Registry management
    reg = PromptGenomeRegistryV1()
    reg.register_genome(genome)
    assert reg.get_genome(genome.prompt_id) == genome
    assert reg.get_genome("non_existent") is None
    assert reg.total_genome_count() == 1

    # Record occurrence
    occ = reg.record_execution(genome.prompt_id, "sess_1", "in_1", "out_1")
    assert occ.prompt_id == genome.prompt_id
    assert len(reg.get_occurrences_for_prompt(genome.prompt_id)) == 1

    # 5. PromptViewEngineV1
    view_engine = PromptViewEngineV1()
    view = view_engine.derive_view(genome, ledger_revision=42)
    assert isinstance(view, PromptViewV1)
    assert view.ledger_revision == 42


# ==============================================================================
# 9. CAS Store Tests (ContentAddressedStorageV1)
# ==============================================================================

def test_cas_store_cold_recovery_and_corruption(tmp_path: Path) -> None:
    cas_dir = tmp_path / "cas"
    store1 = ContentAddressedStorageV1(storage_dir=cas_dir)

    data = b"immutable prompt packet bytes"
    digest = store1.store(data)
    assert digest.startswith("sha256:")

    # Retrieve from cache
    assert store1.retrieve(digest) == data

    # Create fresh store instance (cold cache, must read from disk)
    store2 = ContentAddressedStorageV1(storage_dir=cas_dir)
    assert store2.retrieve(digest) == data

    # Corrupt object on disk and in store
    store2.corrupt_object_bytes_for_testing(digest)
    with pytest.raises(ValueError, match="CAS_DIGEST_MISMATCH"):
        store2.retrieve(digest)

    # Missing digest raises FileNotFoundError
    with pytest.raises(FileNotFoundError, match="CAS_OBJECT_MISSING"):
        store2.retrieve("sha256:0000000000000000000000000000000000000000000000000000000000000000")


# ==============================================================================
# 10. Matching & Evaporation Tests (ReferenceTrailEvaporationCalculatorV1, etc.)
# ==============================================================================

def test_matching_evaporation_and_eligibility() -> None:
    # Negative half life rejected
    with pytest.raises(ValueError, match="half_life_epochs must be positive"):
        ReferenceTrailEvaporationCalculatorV1(half_life_epochs=0)

    # Evaporation calculation
    evap = ReferenceTrailEvaporationCalculatorV1(half_life_epochs=5)
    # 2 uses at epoch 0, evaluated at epoch 10 (2 half-lives elapsed -> (1/2)^2 = 1/4)
    # Total = 2 * (1/4) = 1/2
    weight = evap.calculate_weight([(0, 2)], current_epoch=10)
    assert weight == Fraction(1, 2)

    # Candidate eligibility
    # 1. Shelved or Dormant rejected
    assert is_candidate_eligible({"retrieval_eligibility": "Shelved"}) is False
    assert is_candidate_eligible({"retrieval_eligibility": "Dormant"}) is False

    # 2. PROPOSED or unadmitted rejected
    assert is_candidate_eligible({"domain_placement": "PROPOSED"}) is False
    assert is_candidate_eligible({"placement": {"disposition": "INDEXED_UNREAD"}}) is False
    assert is_candidate_eligible({"placement": {"disposition": "QUARANTINED"}}) is False

    # 3. Read scope filtering
    assert is_candidate_eligible({"read_scope": ["domain_a"]}, query_domain="domain_b") is False
    assert is_candidate_eligible({"read_scope": ["domain_a"]}, query_domain="domain_a") is True


# ==============================================================================
# 11. Immunity & Propagation Tests (DAGHopDistanceCalculatorV1, etc.)
# ==============================================================================

def test_immunity_propagation_and_custody() -> None:
    # 1. ImmunityPropagationEngineV1
    engine = ImmunityPropagationEngineV1(max_backward_hops=10)
    with pytest.raises(ValueError, match="HORIZON_RESET_PROHIBITED"):
        engine.propagate_backward(
            acquisition={},
            current_prompt_id="p_child",
            pretend_as_new_origin=True,
        )
    assert engine.propagate_backward(
        acquisition={},
        current_prompt_id="p_child",
        pretend_as_new_origin=False,
    ) == ["p_child"]

    # 2. DAGHopDistanceCalculatorV1
    calc = DAGHopDistanceCalculatorV1()
    edges = [("A", "B"), ("B", "C")]
    assert calc.calculate_shortest_hop_distance(edges, "A", "A") == 0
    assert calc.calculate_shortest_hop_distance(edges, "A", "C") == 2

    with pytest.raises(ValueError, match="No path found"):
        calc.calculate_shortest_hop_distance(edges, "C", "A")

    # 3. GlobalCustodyRegistryV1
    reg = GlobalCustodyRegistryV1()
    assert reg.is_armed("p_1", "rule_1") is False

    reg.bind_antibody("p_1", "rule_1")
    assert reg.is_armed("p_1", "rule_1") is True

    reg.revoke_rule_version("rule_1")
    assert reg.is_armed("p_1", "rule_1") is False

    # 4. LineageTaintEngineV1
    taint_engine = LineageTaintEngineV1()
    assert taint_engine.is_tainted("node_parent") is False
    taint_engine.mark_tainted("node_parent")
    assert taint_engine.is_tainted("node_parent") is True
    taint_engine.propagate_taint([("node_parent", "node_child")])
    assert taint_engine.is_tainted("node_child") is True


# ==============================================================================
# 12. Domain Eligibility Tests (hard_domain_eligible)
# ==============================================================================

def test_hard_domain_eligible_predicates() -> None:
    # 1. Disposition not ADMITTED_LOCAL
    p1 = DomainPlacementV1("pl_1", "sha_1", "math", ["math"], "PROPOSED")
    assert hard_domain_eligible(p1, "math") is False

    # 2. F4: Domain assignment is origin metadata; cross-assignment with admitted read_scope is ELIGIBLE
    p2 = DomainPlacementV1("pl_2", "sha_2", "physics", ["physics", "math"], "ADMITTED_LOCAL")
    assert hard_domain_eligible(p2, "math") is True
    assert hard_domain_eligible(p2, "biology") is False
    wildcard = DomainPlacementV1("pl_w", "sha_w", "math", ["math.*"], "ADMITTED_LOCAL")
    assert hard_domain_eligible(wildcard, "math.integral") is True
    assert hard_domain_eligible(wildcard, "mathematics") is False
    exact = DomainPlacementV1("pl_e", "sha_e", "physics", ["physics"], "ADMITTED_LOCAL")
    assert hard_domain_eligible(exact, "physics.quantum") is False

    # 3. Required domain not in read scope
    p3 = DomainPlacementV1("pl_3", "sha_3", "math", ["physics"], "ADMITTED_LOCAL")
    assert hard_domain_eligible(p3, "math") is False

    # 4. Valid eligible placement
    p4 = DomainPlacementV1("pl_4", "sha_4", "math", ["math", "general"], "ADMITTED_LOCAL")
    assert hard_domain_eligible(p4, "math") is True
