"""Unit tests for PCIV transitive immunity, fixed-point taint, operational workflow quotient,
protected-span seed evolution, and hash-chained verified projection recovery.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from itertools import permutations
from pathlib import Path

import pytest

from pciv.domain.causal_witness import SealedCausalWitness, seal_causal_witness
from pciv.infrastructure.verified_projection import (
    GENESIS_PREV_SHA256,
    VerifiedProjectionEngineV1,
    compute_event_sha256,
)
from pciv.use_cases.genealogy import LineageEdgeV1, LineageGraphV1, RelationshipType
from pciv.use_cases.immunity import GlobalCustodyRegistryV1, LineageTaintEngineV1
from pciv.use_cases.transitive_immunity import (
    CandidateWorkflowSpec,
    FixedPointLineageTaintEngineV1,
    OperationalWorkflowQuotientV1,
    ProtectedSpanEvolutionV1,
    TransitiveImmunityEngineV1,
    WorkflowStageSpec,
)


def _sealed_edge(parent_id: str, child_id: str, rel: RelationshipType = RelationshipType.DIRECT_MUTATION):
    return seal_causal_witness({"parent_id": parent_id, "child_id": child_id, "kind": rel.value})


# =============================================================================
# 1. FixedPointLineageTaintEngineV1 (SYS-PCIV-009 Remediation)
# =============================================================================


def test_fixed_point_taint_or_policy_is_permutation_invariant() -> None:
    chain_edges = [("n0", "n1"), ("n1", "n2"), ("n2", "n3"), ("n3", "n4")]

    # Legacy single-pass engine fails on reversed insertion order (demonstrating SYS-PCIV-009)
    legacy = LineageTaintEngineV1()
    legacy.mark_tainted("n0")
    legacy.propagate_taint(list(reversed(chain_edges)))
    assert legacy.is_tainted("n4") is False

    # FixedPointLineageTaintEngineV1 yields identical tainted set under all 24 permutations
    expected = frozenset({"n0", "n1", "n2", "n3", "n4"})
    for perm in permutations(chain_edges):
        engine = FixedPointLineageTaintEngineV1(policy_rule="OR", initial_tainted=("n0",))
        result = engine.propagate_taint(list(perm))
        assert result == expected
        assert engine.tainted_nodes() == expected


def test_fixed_point_taint_with_lineage_graph_and_non_inheritance_precedent() -> None:
    graph = LineageGraphV1()
    graph.add_edge("p0", "p1", RelationshipType.DIRECT_MUTATION, _sealed_edge("p0", "p1"))
    graph.add_edge("p1", "p2", RelationshipType.REPAIR, _sealed_edge("p1", "p2", RelationshipType.REPAIR))
    # RetrievedPrecedent is not a causal inheritance edge and does not transmit inheritance taint
    graph.add_edge("p0", "ref_only", RelationshipType.RETRIEVED_PRECEDENT, witness_receipt=None)

    engine = FixedPointLineageTaintEngineV1(policy_rule="OR", initial_tainted=("p0",))
    tainted = engine.propagate_taint(graph)
    assert tainted == frozenset({"p0", "p1", "p2"})
    assert engine.is_tainted("ref_only") is False


def test_fixed_point_taint_quorum_policy_iterates_to_least_fixed_point() -> None:
    # Diamond + cascade requiring multi-round convergence at quorum_k=2:
    # a, b -> m1; m1, b -> m2; m1, m2 -> leaf; a -> single_parent_child
    edges = [
        ("m1", "leaf"),
        ("m2", "leaf"),
        ("m1", "m2"),
        ("b", "m2"),
        ("a", "m1"),
        ("b", "m1"),
        ("a", "single_parent_child"),
    ]

    # Only 'a' tainted: neither m1 nor m2 reaches quorum 2
    partial = FixedPointLineageTaintEngineV1(policy_rule="QUORUM", quorum_k=2, initial_tainted=("a",))
    assert partial.propagate_taint(edges) == frozenset({"a"})

    # Both 'a' and 'b' tainted: m1 taints -> m2 taints -> leaf taints; single_parent_child stays untainted
    for ordered in (edges, list(reversed(edges))):
        full = FixedPointLineageTaintEngineV1(policy_rule="QUORUM", quorum_k=2, initial_tainted=("a", "b"))
        assert full.propagate_taint(ordered) == frozenset({"a", "b", "m1", "m2", "leaf"})
        assert full.is_tainted("single_parent_child") is False


def test_fixed_point_taint_refuses_cycles_and_unwitnessed_inheritance_edges() -> None:
    engine = FixedPointLineageTaintEngineV1(policy_rule="OR", initial_tainted=("x",))
    with pytest.raises(ValueError, match="LINEAGE_CYCLE_REFUSED"):
        engine.propagate_taint([("x", "y"), ("y", "z"), ("z", "x")])

    with pytest.raises(ValueError, match="LINEAGE_CYCLE_REFUSED"):
        engine.propagate_taint([("x", "x")])

    unwitnessed = [LineageEdgeV1(parent_id="x", child_id="y", relationship=RelationshipType.DIRECT_MUTATION)]
    with pytest.raises(ValueError, match="CAUSAL_WITNESS_REQUIRED"):
        engine.propagate_taint(unwitnessed)


# =============================================================================
# 2. TransitiveImmunityEngineV1
# =============================================================================


def test_transitive_immunity_refuses_horizon_reset() -> None:
    engine = TransitiveImmunityEngineV1(max_backward_hops=10)
    with pytest.raises(ValueError, match="HORIZON_RESET_PROHIBITED"):
        engine.propagate_backward(
            graph_or_edges=[("g0", "g1")],
            current_prompt_id="g1",
            rule_id="rule_alpha",
            pretend_as_new_origin=True,
        )


def test_transitive_immunity_shortest_hop_weights_and_hop_ceiling() -> None:
    graph = LineageGraphV1()
    # Shortcut g0 -> g2 -> g4 (2 hops from g4 to g0) alongside longer path g0 -> g1 -> g3 -> g4 (3 hops)
    for u, v in [("g0", "g2"), ("g2", "g4"), ("g0", "g1"), ("g1", "g3"), ("g3", "g4")]:
        graph.add_edge(u, v, RelationshipType.DIRECT_MUTATION, _sealed_edge(u, v))

    engine = TransitiveImmunityEngineV1(max_backward_hops=10)
    receipts = engine.propagate_backward(
        graph_or_edges=graph,
        current_prompt_id="g4",
        rule_id="ab_rule_01",
    )
    by_id = {r.ancestor_id: r for r in receipts}
    assert set(by_id.keys()) == {"g2", "g3", "g0", "g1"}
    assert by_id["g2"].hop_distance == 1
    assert by_id["g2"].attenuation_weight == Fraction(1, 2)
    assert by_id["g3"].hop_distance == 1
    assert by_id["g3"].attenuation_weight == Fraction(1, 2)
    # Shortest hop from g4 to g0 is 2 (via g2), so weight is (1/2)^2 = 1/4
    assert by_id["g0"].hop_distance == 2
    assert by_id["g0"].attenuation_weight == Fraction(1, 4)
    assert by_id["g1"].hop_distance == 2
    assert by_id["g1"].attenuation_weight == Fraction(1, 4)

    # Enforce hop ceiling = 1
    capped = engine.propagate_backward(
        graph_or_edges=graph,
        current_prompt_id="g4",
        rule_id="ab_rule_01",
        max_backward_hops=1,
    )
    assert [r.ancestor_id for r in capped] == ["g2", "g3"]


def test_transitive_immunity_global_custody_revocation_disarms_all_ancestors() -> None:
    edges = [("a0", "a1"), ("a1", "a2"), ("a2", "a3")]
    registry = GlobalCustodyRegistryV1()
    engine = TransitiveImmunityEngineV1(max_backward_hops=10)

    armed_receipts = engine.propagate_backward(
        graph_or_edges=edges,
        current_prompt_id="a3",
        rule_id="rule_v1",
        custody_registry=registry,
    )
    assert len(armed_receipts) == 3
    assert all(r.armed is True for r in armed_receipts)

    # Revoking rule_v1 disarms all ancestors on refresh and on subsequent propagations
    registry.revoke_rule_version("rule_v1")
    refreshed = engine.refresh_custody(armed_receipts, registry)
    assert all(r.armed is False for r in refreshed)

    revoked_receipts = engine.propagate_backward(
        graph_or_edges=edges,
        current_prompt_id="a3",
        rule_id="rule_v1",
        custody_registry=registry,
    )
    assert all(r.armed is False for r in revoked_receipts)


# =============================================================================
# 3. OperationalWorkflowQuotientV1
# =============================================================================


def test_operational_quotient_port_mismatch_and_noncommutativity() -> None:
    op_norm = WorkflowStageSpec("charpoly_wire_normalize", "Wire", "Wire", "norm_v1", idempotent=True)
    op_check = WorkflowStageSpec("charpoly_grid_check", "Wire", "Wire", "check_v1", idempotent=False)
    op_synth = WorkflowStageSpec("draft_refine", "Wire", "Wire", "synth_v1", idempotent=False)
    op_bad = WorkflowStageSpec("solve_answer", "Matrix", "Answer", "solve_v1", idempotent=False)

    quotient = OperationalWorkflowQuotientV1()

    # Incompatible sequential colours raise PORT_MISMATCH
    bad_wf = CandidateWorkflowSpec("wf_port_error", (op_norm, op_bad))
    with pytest.raises(ValueError, match="PORT_MISMATCH"):
        quotient.quotient((bad_wf,))

    # Adjacent idempotent duplicates collapse; noncommuting orders remain distinct
    wf_norm_check = CandidateWorkflowSpec(
        "wf_norm_check", (op_norm, op_check), obligation_pass_fraction=Fraction(5, 5), byte_or_token_cost=100
    )
    wf_norm2_check = CandidateWorkflowSpec(
        "wf_norm2_check",
        (op_norm, op_norm, op_check),
        obligation_pass_fraction=Fraction(5, 5),
        byte_or_token_cost=150,
    )
    wf_check_norm = CandidateWorkflowSpec(
        "wf_check_norm", (op_check, op_norm), obligation_pass_fraction=Fraction(4, 5), byte_or_token_cost=110
    )
    wf_check_synth = CandidateWorkflowSpec(
        "wf_check_synth", (op_check, op_synth), obligation_pass_fraction=Fraction(4, 5), byte_or_token_cost=200
    )
    wf_synth_check = CandidateWorkflowSpec(
        "wf_synth_check", (op_synth, op_check), obligation_pass_fraction=Fraction(3, 5), byte_or_token_cost=200
    )
    # Non-idempotent adjacent duplicates must NOT collapse
    wf_double_check = CandidateWorkflowSpec(
        "wf_double_check", (op_check, op_check), obligation_pass_fraction=None, byte_or_token_cost=180
    )
    wf_baseline = CandidateWorkflowSpec(
        "wf_baseline", (op_synth,), obligation_pass_fraction=Fraction(2, 5), byte_or_token_cost=50, is_baseline=True
    )

    reps, collapsed = quotient.quotient(
        (
            wf_norm_check,
            wf_norm2_check,
            wf_check_norm,
            wf_check_synth,
            wf_synth_check,
            wf_double_check,
            wf_baseline,
        )
    )
    assert [c.workflow_id for c in collapsed] == ["wf_norm2_check"]
    rep_map = {r.workflow.workflow_id: r for r in reps}
    assert len(rep_map) == 6
    assert rep_map["wf_norm_check"].canonical_trace_sha256 != rep_map["wf_check_norm"].canonical_trace_sha256
    assert rep_map["wf_check_synth"].canonical_trace_sha256 != rep_map["wf_synth_check"].canonical_trace_sha256
    assert len(rep_map["wf_double_check"].canonical_stages) == 2

    allocation = quotient.allocate_ecological_reserves(reps, reserve_cap=10)
    assert allocation.reserve_quotas == {"Front": 6, "Unmeasured": 3, "Baseline": 1}
    assert allocation.buckets["Baseline"] == ("wf_baseline",)
    assert allocation.buckets["Unmeasured"] == ("wf_double_check",)
    assert "wf_norm_check" in allocation.buckets["Front"]


# =============================================================================
# 4. ProtectedSpanEvolutionV1
# =============================================================================


def test_protected_span_evolution_preserves_seed_bytes_and_blocks_overlap() -> None:
    fencer = ProtectedSpanEvolutionV1()
    prefix = b"HEADER_V1\n"
    seed = b"FROZEN_IMMUTABLE_SEED_BYTES_0123456789\n"
    suffix = b"FOOTER_V1"

    art = fencer.create_fenced_template(prefix_bytes=prefix, seed_bytes=seed, suffix_bytes=suffix)
    expected_sha = hashlib.sha256(seed).hexdigest()
    assert art.seed_sha256 == expected_sha

    # Mutate governed prefix with longer text -> seed span shifts and stays byte-identical
    art_prefix_mut = fencer.mutate_governed_span(
        art,
        edit_start_byte=0,
        edit_end_byte=len(prefix),
        replacement_bytes=b"EXTENDED_GOVERNED_HEADER_V2\n",
    )
    assert art_prefix_mut.seed_sha256 == expected_sha
    s0, s1 = art_prefix_mut.seed_span.start_byte, art_prefix_mut.seed_span.end_byte
    assert art_prefix_mut.composite_bytes[s0:s1] == seed

    # Mutate governed suffix -> seed span stays byte-identical
    art_suffix_mut = fencer.mutate_governed_span(
        art_prefix_mut,
        edit_start_byte=s1,
        edit_end_byte=len(art_prefix_mut.composite_bytes),
        replacement_bytes=b"UPDATED_FOOTER_V2",
    )
    assert art_suffix_mut.composite_bytes[s0:s1] == seed

    # Overlapping edit into seed span is refused
    with pytest.raises(PermissionError, match="PROTECTED_SPAN_MUTATION_REFUSED"):
        fencer.mutate_governed_span(
            art_suffix_mut,
            edit_start_byte=s0 + 2,
            edit_end_byte=s0 + 5,
            replacement_bytes=b"XXX",
        )

    # Zero-width insertion strictly inside seed span is refused
    with pytest.raises(PermissionError, match="PROTECTED_SPAN_MUTATION_REFUSED"):
        fencer.mutate_governed_span(
            art_suffix_mut,
            edit_start_byte=s0 + 1,
            edit_end_byte=s0 + 1,
            replacement_bytes=b"!",
        )


# =============================================================================
# 5. VerifiedProjectionEngineV1 (SYS-PCIV-008 Remediation)
# =============================================================================


def test_verified_projection_consistent_in_memory_and_durable_jsonl(tmp_path: Path) -> None:
    log_file = tmp_path / "events.jsonl"
    engine = VerifiedProjectionEngineV1(log_path=log_file)
    e0 = engine.append_event(prompt_id="p_alpha", kind="ExecutionPass", payload={"trial": 1})
    e1 = engine.append_event(prompt_id="p_beta", kind="ExecutionFail", payload={"trial": 1})
    e2 = engine.append_event(prompt_id="p_alpha", kind="ExecutionPass", payload={"trial": 2})

    assert e0["prev_sha256"] == GENESIS_PREV_SHA256
    assert e1["prev_sha256"] == e0["event_sha256"]
    assert e2["prev_sha256"] == e1["event_sha256"]

    # Restart fresh engine from durable .jsonl file
    restarted = VerifiedProjectionEngineV1(log_path=log_file)
    recovered = restarted.recover_from_crash()
    assert recovered.is_consistent is True
    assert recovered.corruption_code is None
    assert recovered.verified_event_count == 3
    assert recovered["p_alpha"].pass_count == 2
    assert recovered["p_beta"].pass_count == 0


def test_verified_projection_detects_tampered_payload_digest(tmp_path: Path) -> None:
    log_file = tmp_path / "tampered.jsonl"
    engine = VerifiedProjectionEngineV1(log_path=log_file)
    engine.append_event(prompt_id="p1", kind="ExecutionFail", payload={"score": 0})
    engine.append_event(prompt_id="p1", kind="ExecutionPass", payload={"score": 1})

    # Tamper payload on disk without updating event_sha256
    content = log_file.read_text(encoding="utf-8").replace('"ExecutionFail"', '"ExecutionPass"', 1)
    log_file.write_text(content, encoding="utf-8")

    recovered = VerifiedProjectionEngineV1(log_path=log_file).recover_from_crash()
    assert recovered.is_consistent is False
    assert recovered.corruption_code == "EVENT_DIGEST_TAMPERED"
    assert len(recovered) == 0


def test_verified_projection_detects_deleted_middle_and_swapped_order(tmp_path: Path) -> None:
    log_file = tmp_path / "gap.jsonl"
    engine = VerifiedProjectionEngineV1(log_path=log_file)
    for idx in range(3):
        engine.append_event(prompt_id="p1", kind="ExecutionPass", payload={"idx": idx})

    lines = log_file.read_text(encoding="utf-8").splitlines()

    # Delete middle event (seq 1 missing -> seq jumps 0 -> 2)
    deleted_path = tmp_path / "deleted.jsonl"
    deleted_path.write_text("\n".join([lines[0], lines[2]]) + "\n", encoding="utf-8")
    rec_deleted = VerifiedProjectionEngineV1(log_path=deleted_path).recover_from_crash()
    assert rec_deleted.is_consistent is False
    assert rec_deleted.corruption_code == "SEQUENCE_GAP"
    assert rec_deleted.verified_event_count == 1

    # Swap events 1 and 2
    swapped_path = tmp_path / "swapped.jsonl"
    swapped_path.write_text("\n".join([lines[0], lines[2], lines[1]]) + "\n", encoding="utf-8")
    rec_swapped = VerifiedProjectionEngineV1(log_path=swapped_path).recover_from_crash()
    assert rec_swapped.is_consistent is False
    assert rec_swapped.corruption_code == "SEQUENCE_GAP"


def test_verified_projection_detects_broken_hash_chain() -> None:
    engine = VerifiedProjectionEngineV1()
    engine.append_event(prompt_id="p1", kind="ExecutionPass", payload={"step": 0})
    engine.append_event(prompt_id="p1", kind="ExecutionPass", payload={"step": 1})

    # Forge valid event_sha256 for seq=1 with a bogus prev_sha256 link
    bogus_prev = "f" * 64
    forged_sha = compute_event_sha256(
        seq=1,
        prompt_id="p1",
        kind="ExecutionPass",
        payload={"step": 1},
        prev_sha256=bogus_prev,
    )
    engine.events[1]["prev_sha256"] = bogus_prev
    engine.events[1]["event_sha256"] = forged_sha

    recovered = engine.recover_from_crash()
    assert recovered.is_consistent is False
    assert recovered.corruption_code == "HASH_CHAIN_MISMATCH"
    assert recovered.verified_event_count == 1


def test_verified_projection_detects_truncated_crash_tail(tmp_path: Path) -> None:
    log_file = tmp_path / "crash_tail.jsonl"
    engine = VerifiedProjectionEngineV1(log_path=log_file)
    engine.append_event(prompt_id="p1", kind="ExecutionPass", payload={"ok": True})
    engine.append_event(prompt_id="p2", kind="ExecutionPass", payload={"ok": True})

    # Simulate partial crash write at tail
    with log_file.open("ab") as handle:
        handle.write(b'{"seq":2,"prompt_id":"p1","kind":"ExecutionPass"')

    crashed_engine = VerifiedProjectionEngineV1(log_path=log_file)
    recovered = crashed_engine.recover_from_crash()
    assert recovered.is_consistent is False
    assert recovered.corruption_code == "TRUNCATED_JSON_RECORD"
    assert recovered.verified_event_count == 2

    # Appending onto a corrupted crash log is refused
    with pytest.raises(ValueError, match="APPEND_REFUSED_CORRUPTED_LOG"):
        crashed_engine.append_event(prompt_id="p3", kind="ExecutionPass", payload={})

    # Verify JSON roundtrip formatting sanity
    assert json.loads(log_file.read_text(encoding="utf-8").splitlines()[0])["seq"] == 0


def test_single_measured_candidate_quotient_allocation() -> None:
    op_solve = WorkflowStageSpec("direct_solve", "Seed", "Answer", "direct_v1", idempotent=False)
    op_probe = WorkflowStageSpec("probe_solve", "Seed", "Answer", "probe_v1", idempotent=False)
    wf_single = CandidateWorkflowSpec(
        "wf_single_measured",
        (op_solve,),
        obligation_pass_fraction=Fraction(4, 5),
        byte_or_token_cost=100,
        is_baseline=True,
    )
    wf_unmeasured = CandidateWorkflowSpec(
        "wf_unmeasured", (op_probe,), obligation_pass_fraction=None, byte_or_token_cost=80
    )
    report = OperationalWorkflowQuotientV1().evaluate((wf_single, wf_unmeasured), reserve_cap=10)
    assert report.reserve_allocation.pareto_fronts == (("wf_single_measured",),)
    assert report.reserve_allocation.buckets["Baseline"] == ("wf_single_measured",)
    assert report.reserve_allocation.buckets["Unmeasured"] == ("wf_unmeasured",)


def test_forged_subclass_and_tampered_seal_witness_refused() -> None:
    class _ForgedWitnessSubclass(SealedCausalWitness):
        def __init__(self) -> None:
            object.__setattr__(self, "receipt_sha256", "sha256:" + "0" * 64)
            object.__setattr__(self, "canonical_body", '{"child_id":"y","parent_id":"x"}')

    engine = FixedPointLineageTaintEngineV1(policy_rule="OR", initial_tainted=("x",))
    forged_sub = [LineageEdgeV1("x", "y", RelationshipType.DIRECT_MUTATION, witness_receipt=_ForgedWitnessSubclass())]
    with pytest.raises(ValueError, match="CAUSAL_WITNESS_REQUIRED"):
        engine.propagate_taint(forged_sub)

    bypassed_seal = object.__new__(SealedCausalWitness)
    object.__setattr__(bypassed_seal, "receipt_sha256", "sha256:" + "a" * 64)
    object.__setattr__(bypassed_seal, "canonical_body", '{"child_id":"y","parent_id":"x"}')
    forged_raw = [LineageEdgeV1("x", "y", RelationshipType.DIRECT_MUTATION, witness_receipt=bypassed_seal)]
    with pytest.raises(ValueError, match="CAUSAL_WITNESS_REQUIRED"):
        engine.propagate_taint(forged_raw)


def test_verified_projection_blocks_extra_fields_duplicate_keys_and_syncs_disk_writers(tmp_path: Path) -> None:
    # 1. Extra top-level unhashed field on disk -> EVENT_DIGEST_TAMPERED
    extra_log = tmp_path / "extra.jsonl"
    eng1 = VerifiedProjectionEngineV1(log_path=extra_log)
    rec0 = eng1.append_event(prompt_id="p1", kind="ExecutionPass", payload={"ok": 1})
    tampered_obj = dict(rec0)
    tampered_obj["injected_unhashed_top_level_field"] = "MALICIOUS"
    extra_log.write_text(json.dumps(tampered_obj, sort_keys=True) + "\n", encoding="utf-8")
    rec_extra = VerifiedProjectionEngineV1(log_path=extra_log).recover_from_crash()
    assert rec_extra.is_consistent is False
    assert rec_extra.corruption_code == "EVENT_DIGEST_TAMPERED"

    # 2. Duplicate JSON key smuggling on disk -> TRUNCATED_JSON_RECORD
    dup_log = tmp_path / "dup.jsonl"
    eng2 = VerifiedProjectionEngineV1(log_path=dup_log)
    eng2.append_event(prompt_id="p1", kind="ExecutionPass", payload={"ok": 1})
    raw_line = dup_log.read_text(encoding="utf-8").strip()
    smuggled_line = '{"kind":"SMUGGLED",' + raw_line[1:] + "\n"
    dup_log.write_text(smuggled_line, encoding="utf-8")
    rec_dup = VerifiedProjectionEngineV1(log_path=dup_log).recover_from_crash()
    assert rec_dup.is_consistent is False
    assert rec_dup.corruption_code == "TRUNCATED_JSON_RECORD"

    # 3. Multi-writer disk synchronization + in-memory corruption guard on append_event
    shared_log = tmp_path / "shared.jsonl"
    writer_a = VerifiedProjectionEngineV1(log_path=shared_log)
    writer_b = VerifiedProjectionEngineV1(log_path=shared_log)
    writer_a.append_event(prompt_id="p1", kind="ExecutionPass", payload={"w": "a"})
    writer_b.append_event(prompt_id="p2", kind="ExecutionPass", payload={"w": "b"})
    rec_shared = VerifiedProjectionEngineV1(log_path=shared_log).recover_from_crash()
    assert rec_shared.is_consistent is True
    assert rec_shared.verified_event_count == 2
    assert rec_shared["p1"].pass_count == 1
    assert rec_shared["p2"].pass_count == 1

    mem_eng = VerifiedProjectionEngineV1()
    mem_eng.append_event(prompt_id="p1", kind="ExecutionPass", payload={"k": 1})
    mem_eng.events[0]["payload"]["k"] = 999
    with pytest.raises(ValueError, match="APPEND_REFUSED_CORRUPTED_LOG"):
        mem_eng.append_event(prompt_id="p1", kind="ExecutionPass", payload={"k": 2})

