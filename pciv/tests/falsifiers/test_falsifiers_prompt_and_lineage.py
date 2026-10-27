"""Falsifier and specification tests for Part B: Prompt Civilization, Lineage, and Population Policies.

Covers:
- F-PROMPT-01: Retired Python crate path stays gone (ModuleNotFoundError).
- F-PROMPT-02: AntiSkillSpecV2 stays PROPOSED with runtime_enforcement=False.
- F-PROMPT-03: MutationOperatorCandidateV1 cannot self-admit (SELF_ADMISSION_REFUSED).
- F-GENOME-01: PromptGenomeV1 immutable; PromptViewV1 derived at declared ledger revision.
- F-GENOME-02: Re-executing unchanged prompt creates ExecutionOccurrenceV1, not new genome.
- F-GENOME-03: Derived fields (generation, protected_spans) re-derived (DERIVED_FIELD_MISMATCH).
- F-LINEAGE-01: Lineage edges exist only for witnessed causal relations, not task matching.
- F-DOMAIN-01: Hard domain eligibility requires ADMITTED_LOCAL placement with valid read_scope.
- F-BIO-03: Protected spans are immutable (PROTECTED_SPAN_MUTATION_REFUSED).
- F-BIO-04: Reference-trail evaporation ages per contribution (281/256 at epoch 100, not 101).
- F-BIO-05: Population policy reserves use largest-remainder integer allocation (6/3/1 at N=10).
- F-SELECT-01: Pareto front selection + lexicographic tiebreak (no composite scalar).
- F-SELECT-02: Exploration quota for unmeasured prompts prevents lockout by mature lineages.
- F-SELECT-03: Verifier receipt acceptance bound to declared task obligation_id.
- F-IMMUNE-09: No horizon-reset relay; preserves original acquisition_id and 10-hop ceiling.
- F-IMMUNE-10: Distance is shortest path in inheritance-edge hops, not generation subtraction.
- F-IMMUNE-11: Stale armed caches invalidated before execution upon suspension or revocation.
- F-RES-06: Validity or emptiness alone earns no success credit in fitness.
- F-RES-07: Global custody invalidation disarms every binding of the rule version.
- F-RES-09: Comparative claims require held-out data and multiplicity correction.
- F-RES-11: Lineage taint moves forward under host-bound TaintPolicyV1 (default OR).
"""

from __future__ import annotations

from fractions import Fraction

import pytest


def test_f_prompt_01_retired_python_crates_path_is_gone() -> None:
    """F-PROMPT-01: The retired Python crate path engine.crates.prompt_civilization stays gone."""
    with pytest.raises(ModuleNotFoundError):
        import engine.crates.prompt_civilization  # noqa: F401


def test_f_prompt_02_antiskillspecv2_stays_proposed_with_no_runtime_enforcement() -> None:
    """F-PROMPT-02: AntiSkillSpecV2 constructor rejects non-PROPOSED status or runtime_enforcement=True."""
    from operads.domain.anti_skills.anti_skill_v2 import (
        AntiSkillSpecV2,
    )

    # Status must be PROPOSED
    with pytest.raises(ValueError, match="PROPOSED_STATUS_REQUIRED"):
        AntiSkillSpecV2(
            skill_id="anti_skill_test",
            status="ADMITTED",
            runtime_enforcement=False,
        )

    # runtime_enforcement must be False
    with pytest.raises(ValueError, match="RUNTIME_ENFORCEMENT_MUST_BE_FALSE"):
        AntiSkillSpecV2(
            skill_id="anti_skill_test",
            status="PROPOSED",
            runtime_enforcement=True,
        )

    # Valid construction
    valid_spec = AntiSkillSpecV2(
        skill_id="anti_skill_test",
        status="PROPOSED",
        runtime_enforcement=False,
    )
    assert valid_spec.status == "PROPOSED"
    assert valid_spec.runtime_enforcement is False


def test_f_prompt_03_mutation_operator_cannot_admit() -> None:
    """F-PROMPT-03: MutationOperatorCandidateV1 has no admission field and attempting self-admission refuses."""
    from operating_system.adapters.prompt_civ.forge import (
        MutationOperatorCandidateV1,
    )

    op = MutationOperatorCandidateV1(
        operator_id="mutate_prompt_v1",
        target_span="variable_explanation_body",
    )

    assert not hasattr(op, "admit"), "Mutation operator must not have an admit method"
    assert not hasattr(op, "is_admitted"), "Mutation operator must not have an is_admitted attribute"

    # Attempt to invoke admission path raises SELF_ADMISSION_REFUSED
    with pytest.raises(PermissionError, match="SELF_ADMISSION_REFUSED"):
        op.attempt_self_admission(target_genome_id="genome_123")


def test_f_genome_01_genome_immutable_view_derived_at_declared_revision() -> None:
    """F-GENOME-01: PromptGenomeV1 is immutable; PromptViewV1 derived at declared ledger revision."""
    from operating_system.adapters.prompt_civ.record import (
        CustodyTier,
        PromptGenomeV1,
        PromptViewEngineV1,
    )

    genome = PromptGenomeV1(
        source_packet_refs=[{"packet_id": "pkt_01", "sha256": "sha_01"}],
        domain_model={"domain": "core.math"},
        parents=[],
        birth_custody=CustodyTier.WILD,
    )

    # Attempting to mutate genome custody directly is blocked / attribute error
    with pytest.raises((AttributeError, TypeError)):
        genome.current_custody = CustodyTier.ADMITTED  # type: ignore[misc]

    # View engine derives view at ledger revision
    engine = PromptViewEngineV1()
    view = engine.derive_view(genome, ledger_revision=42)
    assert view.prompt_id == genome.prompt_id
    assert view.ledger_revision == 42
    assert view.current_custody == CustodyTier.WILD


def test_f_genome_02_re_execution_creates_occurrence_not_new_genome() -> None:
    """F-GENOME-02: Executing an unchanged prompt creates ExecutionOccurrenceV1, not a new PromptGenomeV1."""
    from operating_system.adapters.prompt_civ.record import (
        ExecutionOccurrenceV1,
        PromptGenomeRegistryV1,
        PromptGenomeV1,
    )

    registry = PromptGenomeRegistryV1()
    genome = PromptGenomeV1(
        source_packet_refs=[{"packet_id": "pkt_same", "sha256": "sha_same"}],
        domain_model={"domain": "core.math"},
        parents=[],
    )
    registry.register_genome(genome)

    # Execute run 1
    occ1 = registry.record_execution(
        prompt_id=genome.prompt_id,
        session_id="sess_1",
        input_packet_id="pkt_in_1",
        output_packet_id="pkt_out_1",
    )
    # Execute run 2 (different response to same prompt)
    occ2 = registry.record_execution(
        prompt_id=genome.prompt_id,
        session_id="sess_2",
        input_packet_id="pkt_in_2",
        output_packet_id="pkt_out_2",
    )

    assert isinstance(occ1, ExecutionOccurrenceV1)
    assert isinstance(occ2, ExecutionOccurrenceV1)
    assert occ1.occurrence_id != occ2.occurrence_id
    assert occ1.prompt_id == occ2.prompt_id == genome.prompt_id
    assert registry.total_genome_count() == 1, "Re-execution must not register a new genome"


def test_f_genome_03_derived_fields_rederived_mismatch_refused() -> None:
    """F-GENOME-03: Supplying wrong generation or protected_spans raises DERIVED_FIELD_MISMATCH."""
    from operating_system.adapters.prompt_civ.record import (
        PromptGenomeV1,
    )

    # Parent has generation 3, so child must be 4
    with pytest.raises(ValueError, match="DERIVED_FIELD_MISMATCH"):
        PromptGenomeV1.create_verified(
            source_packet_refs=[{"packet_id": "pkt_child", "sha256": "sha_child"}],
            domain_model={"domain": "core.math"},
            parents=[{"parent_id": "parent_gen_3", "generation": 3}],
            declared_generation=2,  # Supplying wrong generation (2 instead of 4)
        )


def test_f_lineage_01_edges_exist_only_for_witnessed_causal_relations() -> None:
    """F-LINEAGE-01: Lineage edges require witnessed causal relation (DirectMutation, Repair, Retry).

    Matching task objectives alone does not create an inheritance edge.
    """
    from operating_system.adapters.prompt_civ.genealogy import (
        LineageGraphV1,
        RelationshipType,
    )

    graph = LineageGraphV1()

    # Attempt to create edge based purely on task objective matching
    with pytest.raises(ValueError, match="CAUSAL_WITNESS_REQUIRED"):
        graph.add_edge(
            parent_id="genome_task_a_run1",
            child_id="genome_task_a_run2",
            relationship="TASK_OBJECTIVE_MATCH",  # Non-causal!
            witness_receipt=None,
        )

    from pciv.domain.causal_witness import seal_causal_witness

    # Legitimate causal relationship with a sealed witness succeeds
    graph.add_edge(
        parent_id="genome_task_a_run1",
        child_id="genome_task_a_mutated",
        relationship=RelationshipType.DIRECT_MUTATION,
        witness_receipt=seal_causal_witness(
            {
                "parent_id": "genome_task_a_run1",
                "child_id": "genome_task_a_mutated",
                "edge": "mutation_operator_witness_01",
            }
        ),
    )
    assert graph.has_inheritance_edge("genome_task_a_run1", "genome_task_a_mutated") is True


def test_f_domain_01_hard_domain_eligibility_requires_admitted_local_placement() -> None:
    """F-DOMAIN-01: hard_domain_eligible requires DomainPlacementV1 with disposition=ADMITTED_LOCAL.

    Taxonomy recognition or PROPOSED status alone is excluded.
    """
    from operating_system.adapters.prompt_civ.domain import (
        DomainPlacementV1,
        hard_domain_eligible,
    )

    # 1. Recognized taxonomy but status PROPOSED (unadmitted)
    unadmitted_placement = DomainPlacementV1(
        placement_id="place_01",
        content_digest="sha256:prompt_bytes",
        domain_assignment="core.math.integral",
        read_scope=["core.math.integral"],
        disposition="INDEXED_UNREAD",
    )
    assert hard_domain_eligible(unadmitted_placement, "core.math.integral") is False

    # 2. Admitted local placement with matching read_scope
    admitted_placement = DomainPlacementV1(
        placement_id="place_02",
        content_digest="sha256:prompt_bytes",
        domain_assignment="core.math.integral",
        read_scope=["core.math.integral"],
        disposition="ADMITTED_LOCAL",
    )
    assert hard_domain_eligible(admitted_placement, "core.math.integral") is True


def test_f_bio_03_protected_spans_are_immutable() -> None:
    """F-BIO-03: Any mutation attempting to edit bytes within protected_spans is refused."""
    from operating_system.adapters.prompt_civ.forge import (
        PromptMutationEngineV1,
    )
    from operating_system.adapters.prompt_civ.record import (
        ProtectedSpanV1,
    )

    engine = PromptMutationEngineV1()
    protected_spans = [
        ProtectedSpanV1(name="system_framing", start_byte=0, end_byte=100),
        ProtectedSpanV1(name="authority_effect_fence", start_byte=101, end_byte=200),
    ]

    # Mutation touches byte 50 (inside system_framing)
    with pytest.raises(PermissionError, match="PROTECTED_SPAN_MUTATION_REFUSED"):
        engine.apply_mutation(
            original_bytes=b"x" * 500,
            protected_spans=protected_spans,
            edit_start_byte=50,
            edit_end_byte=80,
            replacement_bytes=b"malicious system override",
        )


def test_f_bio_04_reference_trail_evaporation_ages_per_contribution() -> None:
    """F-BIO-04: Reference evaporation ages each use on its own (281/256 at epoch 100, NOT 101)."""
    from operating_system.adapters.prompt_civ.matching import (
        ReferenceTrailEvaporationCalculatorV1,
    )

    calc = ReferenceTrailEvaporationCalculatorV1(half_life_epochs=10)

    # 100 uses at epoch 0
    uses = [(0, 100)]  # (epoch, count)

    # At epoch 100: elapsed = 100 -> 10 half-lives -> decay = (1/2)^10 = 1/1024
    # Weight = 100 / 1024 = 25/256
    weight_epoch_100_prior = calc.calculate_weight(uses, current_epoch=100)
    assert weight_epoch_100_prior == Fraction(25, 256)

    # 1 new use at epoch 100: new contribution weight is 1 * (1/2)^0 = 1
    # Total weight = 1 + 25/256 = 281/256
    uses_with_new = [(0, 100), (100, 1)]
    weight_epoch_100_after = calc.calculate_weight(uses_with_new, current_epoch=100)
    assert weight_epoch_100_after == Fraction(281, 256)
    assert weight_epoch_100_after != 101, "Rejuvenation bug: weight must NOT reset to 101"


def test_f_bio_05_population_policy_reserves_largest_remainder_allocation() -> None:
    """F-BIO-05: Ecological reserves use largest-remainder allocation (6/3/1 at N=10; sums to N)."""
    from operating_system.adapters.prompt_civ.forge import (
        PopulationPolicyV1,
    )

    policy = PopulationPolicyV1()

    # Tested caps from §8: 1, 2, 3, 7, 10, 13, 19, 21
    test_caps = [1, 2, 3, 7, 10, 13, 19, 21]

    for cap in test_caps:
        alloc = policy.allocate_reserves(cap)
        assert sum(alloc.values()) == cap, f"Reserves must sum to exactly {cap}"

    # Exact worked example at N = 10: Front 6, Unmeasured 3, Baseline 1
    alloc_10 = policy.allocate_reserves(10)
    assert alloc_10["Front"] == 6
    assert alloc_10["Unmeasured"] == 3
    assert alloc_10["Baseline"] == 1


def test_f_select_01_pareto_front_selection_no_composite_scalar() -> None:
    """F-SELECT-01: Candidate prompts partitioned into non-dominated Pareto fronts with lexicographic tiebreak."""
    from operating_system.adapters.prompt_civ.fitness import (
        ParetoFrontSelectorV1,
    )

    selector = ParetoFrontSelectorV1()
    candidates = [
        {"id": "p1", "metrics": {"correctness": Fraction(4, 5), "cost": 10}},
        {"id": "p2", "metrics": {"correctness": Fraction(3, 5), "cost": 5}},
        {"id": "p3", "metrics": {"correctness": Fraction(2, 5), "cost": 20}},  # Dominated by p1 and p2
    ]

    fronts = selector.partition_fronts(candidates)
    assert len(fronts[0]) == 2  # p1 and p2 are mutually non-dominating
    assert {c["id"] for c in fronts[0]} == {"p1", "p2"}
    assert fronts[1][0]["id"] == "p3"


def test_f_select_02_exploration_quota_for_unmeasured_prompts() -> None:
    """F-SELECT-02: Unmeasured prompts receive exploration quota so mature lineages do not lock them out."""
    from operating_system.adapters.prompt_civ.matching import (
        PrecedentMatcherV1,
    )

    matcher = PrecedentMatcherV1(exploration_quota_slots=1)
    candidates = [
        {"id": "mature_1", "maturity": "Evaluated", "pareto_front": 0},
        {"id": "mature_2", "maturity": "Evaluated", "pareto_front": 0},
        {"id": "new_unmeasured", "maturity": "Unmeasured", "pareto_front": None},
    ]

    matched = matcher.select_precedents(candidates, count=2)
    selected_ids = [m["id"] for m in matched]
    assert "new_unmeasured" in selected_ids, "Unmeasured prompt must be allocated an exploration slot"


def test_f_select_03_obligation_binding_exact_verifier_receipt() -> None:
    """F-SELECT-03: Verifier receipt counts toward success ONLY if obligation_id matches task obligation."""
    from operating_system.adapters.prompt_civ.fitness import (
        PromptFitnessCalculatorV1,
    )

    calculator = PromptFitnessCalculatorV1()

    # Verified receipt for Task B (PageRank)
    receipt_task_b = {
        "obligation_id": "obligation_pagerank_spectral_v2",
        "verifier_status": "VERIFIED_EXACT",
    }

    # Attempting to score reliability for Task A (Integral solving)
    credit = calculator.extract_obligation_success_credit(
        target_obligation_id="obligation_integral_riemann_v1",
        verifier_receipt=receipt_task_b,
    )
    assert credit == 0, "Receipt from obligation B cannot count toward success for obligation A"


def test_f_immune_09_no_horizon_reset_relay() -> None:
    """F-IMMUNE-09: Inherited antibody preserves original acquisition_id and 10-hop ceiling.

    Child cannot re-originate backward propagation.
    """
    from operating_system.adapters.prompt_civ.immunity import (
        ImmunityPropagationEngineV1,
    )

    engine = ImmunityPropagationEngineV1(max_backward_hops=10)

    # Origin at Gen 0
    acq = {
        "acquisition_id": "acq_orig_01",
        "origin_prompt_id": "prompt_root",
        "acquired_generation": 0,
    }

    # Child at hop 8 inherits antibody
    # Child attempts to backpropagate to its neighbors pretending it is the origin
    with pytest.raises(ValueError, match="HORIZON_RESET_PROHIBITED"):
        engine.propagate_backward(
            acquisition=acq,
            current_prompt_id="prompt_hop_8",
            pretend_as_new_origin=True,
        )


def test_f_immune_10_distance_is_shortest_path_in_inheritance_edge_hops() -> None:
    """F-IMMUNE-10: Multi-parent DAG distance is shortest inheritance-edge hops, NOT generation subtraction."""
    from operating_system.adapters.prompt_civ.immunity import (
        DAGHopDistanceCalculatorV1,
    )

    calc = DAGHopDistanceCalculatorV1()
    # Node C has parents A (Gen 1) and B (Gen 5). Generation of C is 6.
    # Edge A->C is 1 hop. Generation difference is 6 - 1 = 5.
    graph_edges = [
        ("A", "C"),  # 1 hop
        ("A", "B1"), ("B1", "B2"), ("B2", "B3"), ("B3", "B4"), ("B4", "B"), ("B", "C"),  # 6 hops
    ]

    hops = calc.calculate_shortest_hop_distance(graph_edges, start="A", target="C")
    assert hops == 1, "Distance must be 1 hop, not generation difference 5"


def test_f_immune_11_stale_armed_caches_invalidated_upon_revocation() -> None:
    """F-IMMUNE-11: Serving cached repertoire after Suspend or Revoke is disarmed before execution."""
    from operating_system.adapters.prompt_civ.immunity import (
        ArmedRepertoireManagerV1,
    )

    manager = ArmedRepertoireManagerV1()
    manager.arm_antibody("prompt_1", "ab_rule_v1")

    # Invalidate / revoke rule v1
    manager.record_custody_event(rule_id="ab_rule_v1", new_custody="Revoked", ledger_revision=10)

    # Repertoire view at next ledger revision
    armed = manager.get_armed_repertoire("prompt_1", ledger_revision=11)
    assert "ab_rule_v1" not in armed, "Revoked antibody must be disarmed from armed repertoire"


def test_f_res_06_validity_or_emptiness_alone_earns_no_success_credit() -> None:
    """F-RES-06: Valid syntax or empty outputs earn no success credit in fitness; valid is not correct."""
    from operating_system.adapters.prompt_civ.fitness import (
        PromptFitnessCalculatorV1,
    )

    calc = PromptFitnessCalculatorV1()
    empty_valid_packet = {
        "syntax_valid": True,
        "payload": {},
        "is_empty": True,
    }

    metrics = calc.compute_execution_metrics(empty_valid_packet)
    assert metrics.success_credit == 0
    assert metrics.is_empty_or_syntax_only is True


def test_f_res_07_custody_invalidation_is_global_across_all_bindings() -> None:
    """F-RES-07: Suspending or revoking an antibody disarms every binding of that rule version."""
    from operating_system.adapters.prompt_civ.immunity import (
        GlobalCustodyRegistryV1,
    )

    registry = GlobalCustodyRegistryV1()
    registry.bind_antibody("prompt_ancestor_P4", "ab_rule_v1")
    registry.bind_antibody("prompt_origin_P14", "ab_rule_v1")
    registry.bind_antibody("prompt_descendant_P20", "ab_rule_v1")
    registry.bind_antibody("prompt_unrelated_P99", "ab_rule_v1")

    # Revoke ab_rule_v1
    registry.revoke_rule_version("ab_rule_v1")

    for pid in ("prompt_ancestor_P4", "prompt_origin_P14", "prompt_descendant_P20", "prompt_unrelated_P99"):
        assert registry.is_armed(pid, "ab_rule_v1") is False, f"{pid} must be disarmed globally"


def test_f_res_09_comparative_claims_need_holdout_and_multiplicity_correction() -> None:
    """F-RES-09: Emitting comparative benefit claims without holdout split or multiplicity correction is refused."""
    from operating_system.adapters.prompt_civ.fitness import (
        ComparativeClaimAuditorV1,
    )

    auditor = ComparativeClaimAuditorV1()

    # Attempt to emit comparative superiority claim without holdout split
    with pytest.raises(ValueError, match="COMPARATIVE_CLAIM_HOLDOUT_REQUIRED"):
        auditor.evaluate_claim(
            claim_type="COMPARATIVE_BENEFIT",
            has_held_out_split=False,
            multiplicity_correction=None,
        )


def test_f_res_11_taint_moves_forward_under_host_bound_policy() -> None:
    """F-RES-11: Lineage taint moves forward along causal graph under host-bound TaintPolicyV1 (default OR)."""
    from operating_system.adapters.prompt_civ.immunity import (
        LineageTaintEngineV1,
        TaintPolicyV1,
    )

    engine = LineageTaintEngineV1(policy=TaintPolicyV1(rule="OR"))

    # Child C has Parent P1 (tainted) and Parent P2 (clean)
    engine.mark_tainted("P1")
    engine.propagate_taint([("P1", "C"), ("P2", "C")])

    assert engine.is_tainted("C") is True, "Under OR policy, child with tainted parent must be tainted"
