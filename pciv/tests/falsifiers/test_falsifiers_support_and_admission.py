"""Falsifier and specification tests for Part D: Support Policies, Fixtures, and Admission Boundaries.

Covers:
- F-SUPPORT-01: Support count is independent of observation ingestion order.
- F-SUPPORT-02: Non-transitive overlap case yields maximum independent set = 2.
- F-SUPPORT-03: Support is feasible without relabelling (keys derived by host from receipts).
- F-SUPPORT-04: Support calculation is monotone (adding observation never lowers support).
- F-PHARM-01: Duplicate collapse: replays of the same event yield support = 1.
- F-PHARM-02: Parser-bug phantom IDs permanently retired.
- F-PHARM-03: Fixture validation failure makes binding non-effective immediately.
- F-PHARM-04: Descent follows declared inheritance edges only.
- F-FIX-01: Fixture polarity map requires explicit declaration per producer.
- F-FIX-02: Validation failure proposes retirement (RetirementProposalV1); custody unchanged.
- F-RES-05: Inherited or propagated references are never observations.
"""

from __future__ import annotations

import pytest


def test_f_support_01_support_is_independent_of_ingestion_order() -> None:
    """F-SUPPORT-01: Support count and promotion decision are invariant under permutation of observations."""
    from omega_engine_epistemic_immune_system.use_cases.provisional_promotion import (
        ObservationSupportPolicyV1,
        RawObservationV1,
    )

    policy = ObservationSupportPolicyV1()

    # Three observations with independent host-bound correlation keys
    obs1 = RawObservationV1(
        occurrence_id="occ_1",
        generating_model_id="model_claude_3_5",
        scaffold_digest="scaffold_sha_1",
        precedent_set_digest="precedent_sha_1",
        inheritance_root="lineage_root_1",
    )
    obs2 = RawObservationV1(
        occurrence_id="occ_2",
        generating_model_id="model_gpt_4o",
        scaffold_digest="scaffold_sha_2",
        precedent_set_digest="precedent_sha_2",
        inheritance_root="lineage_root_2",
    )
    obs3 = RawObservationV1(
        occurrence_id="occ_3",
        generating_model_id="model_gemini_pro",
        scaffold_digest="scaffold_sha_3",
        precedent_set_digest="precedent_sha_3",
        inheritance_root="lineage_root_3",
    )

    order_a = [obs1, obs2, obs3]
    order_b = [obs3, obs1, obs2]
    order_c = [obs2, obs3, obs1]

    support_a = policy.compute_support(order_a)
    support_b = policy.compute_support(order_b)
    support_c = policy.compute_support(order_c)

    assert support_a.support_count == 3
    assert support_a.support_count == support_b.support_count == support_c.support_count
    assert support_a.eligible_for_provisional is True


def test_f_support_02_non_transitive_overlap_case() -> None:
    """F-SUPPORT-02: A-B correlated, B-C correlated, A-C not correlated -> support = 2."""
    from omega_engine_epistemic_immune_system.use_cases.provisional_promotion import (
        ObservationSupportPolicyV1,
        RawObservationV1,
    )

    policy = ObservationSupportPolicyV1()

    # A shares model with B; B shares scaffold with C; A and C share nothing
    obs_a = RawObservationV1(
        occurrence_id="occ_a",
        generating_model_id="model_shared_ab",
        scaffold_digest="scaffold_unique_a",
        precedent_set_digest="precedent_unique_a",
        inheritance_root="lineage_unique_a",
    )
    obs_b = RawObservationV1(
        occurrence_id="occ_b",
        generating_model_id="model_shared_ab",  # Shares with A
        scaffold_digest="scaffold_shared_bc",   # Shares with C
        precedent_set_digest="precedent_unique_b",
        inheritance_root="lineage_unique_b",
    )
    obs_c = RawObservationV1(
        occurrence_id="occ_c",
        generating_model_id="model_unique_c",
        scaffold_digest="scaffold_shared_bc",   # Shares with B
        precedent_set_digest="precedent_unique_c",
        inheritance_root="lineage_unique_c",
    )

    result = policy.compute_support([obs_a, obs_b, obs_c])
    # The maximum independent set of graph (A-B-C) is {A, C}, which has size 2.
    assert result.support_count == 2
    assert result.eligible_for_provisional is False, "Support 2 does not meet threshold 3"


def test_f_support_03_support_is_feasible_without_relabelling() -> None:
    """F-SUPPORT-03: Renaming caller-supplied fields does not increase support.

    Correlation keys are host-bound from sealed receipts.
    """
    from omega_engine_epistemic_immune_system.use_cases.provisional_promotion import (
        ObservationSupportPolicyV1,
        RawObservationV1,
    )

    policy = ObservationSupportPolicyV1()

    # Two observations derived from the same sealed receipt
    obs_base = RawObservationV1(
        occurrence_id="occ_orig",
        generating_model_id="model_1",
        scaffold_digest="scaffold_1",
        precedent_set_digest="prec_1",
        inheritance_root="root_1",
    )
    # Caller attempts to fake independence by changing arbitrary string metadata
    obs_relabeled = RawObservationV1(
        occurrence_id="occ_relabeled_fake",
        generating_model_id="model_1",  # Host derives real model key
        scaffold_digest="scaffold_1",   # Host derives real scaffold key
        precedent_set_digest="prec_1",
        inheritance_root="root_1",
    )

    result = policy.compute_support([obs_base, obs_relabeled])
    assert result.support_count == 1, "Relabelled identical receipt keys must not increase support"


def test_f_support_04_support_is_monotone() -> None:
    """F-SUPPORT-04: Adding an observation never lowers support."""
    from omega_engine_epistemic_immune_system.use_cases.provisional_promotion import (
        ObservationSupportPolicyV1,
        RawObservationV1,
    )

    policy = ObservationSupportPolicyV1()

    obs_a = RawObservationV1("occ_a", "m1", "s1", "p1", "r1")
    obs_c = RawObservationV1("occ_c", "m2", "s2", "p2", "r2")
    initial_support = policy.compute_support([obs_a, obs_c]).support_count
    assert initial_support == 2

    # Add bridging observation B (correlated with both A and C)
    obs_b_bridging = RawObservationV1("occ_b", "m1", "s2", "p3", "r3")
    new_support = policy.compute_support([obs_a, obs_c, obs_b_bridging]).support_count

    assert new_support >= initial_support, "Adding observations must be monotone (never decrease support)"


def test_f_pharm_01_duplicate_collapse_replays_count_as_one() -> None:
    """F-PHARM-01: Ten replays of one defect yield support = 1 and do not promote."""
    from omega_engine_epistemic_immune_system.use_cases.provisional_promotion import (
        ObservationSupportPolicyV1,
        RawObservationV1,
    )

    policy = ObservationSupportPolicyV1()

    # 10 replays of the same event (same input-packet root and occurrence)
    replays = [
        RawObservationV1(
            occurrence_id="occ_single_defect",
            generating_model_id="model_fixed",
            scaffold_digest="scaffold_fixed",
            precedent_set_digest="precedent_fixed",
            inheritance_root="root_fixed",
        )
        for _ in range(10)
    ]

    result = policy.compute_support(replays)
    assert result.support_count == 1
    assert result.eligible_for_provisional is False


def test_f_pharm_02_parser_bug_phantoms_permanently_retired() -> None:
    """F-PHARM-02: Farming any of the three parser-bug phantom IDs is skipped with typed reason."""
    from omega_engine_woland.stage.domain.immune.models import Antibody

    retired_phantom_ids = [
        "ab_syntax_error_e033d14a",
        "ab_syntax_error_4cb62bc5",
        "ab_syntax_error_bb7045c0",
    ]

    for phantom_id in retired_phantom_ids:
        with pytest.raises(ValueError, match="PARSER_BUG_PHANTOM_RETIRED"):
            Antibody.farm(
                antibody_id=phantom_id,
                defect_description="Spurious syntax error from parser bug",
            )


def test_f_pharm_03_fixture_validation_failure_makes_binding_non_effective() -> None:
    """F-PHARM-03: When must_match fails or must_not_match fires, binding is non-effective immediately."""
    from omega_engine_epistemic_immune_system.domain.external_admission import (
        FixtureValidationEngineV1,
        OperationalBindingV1,
    )

    engine = FixtureValidationEngineV1()
    binding = OperationalBindingV1(
        antibody_id="ab_001",
        rule_digest="sha256:rule_bytes",
        must_match_fixture=b"{\"trigger\": \"flaw\"}",
        must_not_match_fixture=b"{\"clean\": \"ok\"}",
    )

    # 1. Healthy validation
    assert engine.validate_binding(binding, mock_detector_matches=[True, False]).is_effective is True

    # 2. must_match fails (detector does not match triggering defect)
    failing_match = engine.validate_binding(binding, mock_detector_matches=[False, False])
    assert failing_match.is_effective is False
    assert failing_match.failure_kind == "MUST_MATCH_FIXTURE_FAILED"

    # 3. must_not_match fires (detector matches clean control)
    firing_control = engine.validate_binding(binding, mock_detector_matches=[True, True])
    assert firing_control.is_effective is False
    assert firing_control.failure_kind == "MUST_NOT_MATCH_FIXTURE_FIRED"


def test_f_pharm_04_descent_follows_declared_inheritance_edges_only() -> None:
    """F-PHARM-04: Traversing reference edges or objective matches as descent is refused."""
    from omega_engine_operating_system.adapters.prompt_civ.genealogy import (
        LineageGraphV1,
        RelationshipType,
    )

    graph = LineageGraphV1()
    graph.add_edge("parent_prompt", "child_prompt", relationship=RelationshipType.RETRIEVED_PRECEDENT)

    # Reference edge is not an inheritance edge; attempting to derive descent raises
    with pytest.raises(ValueError, match="DESCENT_REQUIRES_INHERITANCE_EDGE"):
        graph.derive_descent_path("parent_prompt", "child_prompt")


def test_f_fix_01_fixture_polarity_map_explicit_declaration() -> None:
    """F-FIX-01: Producers require explicit FixturePolarityMapV1; unmapped raises FIXTURE_POLARITY_UNDECLARED."""
    from omega_engine_epistemic_immune_system.domain.external_admission import (
        FixturePolarityMapV1,
        FixturePolarityResolverV1,
    )

    resolver = FixturePolarityResolverV1()

    # the city mapping: negative_fixture is triggering defect (must_match), positive is repaired (must_not_match)
    woland_map = FixturePolarityMapV1(
        producer="omega_engine_woland.stage.domain.immune.seeder",
        schema_version="1.0",
        must_match_field="negative_fixture",
        must_not_match_field="positive_fixture",
    )
    resolver.register_map(woland_map)

    # Resolving registered producer works
    polarity = resolver.resolve_polarity(
        producer="omega_engine_woland.stage.domain.immune.seeder",
        schema_version="1.0",
    )
    assert polarity.must_match_field == "negative_fixture"
    assert polarity.must_not_match_field == "positive_fixture"

    # Unmapped producer raises FIXTURE_POLARITY_UNDECLARED
    with pytest.raises(LookupError, match="FIXTURE_POLARITY_UNDECLARED"):
        resolver.resolve_polarity(producer="unknown_third_party_producer", schema_version="2.0")


def test_f_fix_02_validation_failure_proposes_retirement_custody_unchanged() -> None:
    """F-FIX-02: Fixture validation failure emits RetirementProposalV1; custody remains unchanged."""
    from omega_engine_epistemic_immune_system.domain.external_admission import (
        FixtureValidationEngineV1,
        OperationalBindingV1,
        RetirementProposalV1,
    )

    engine = FixtureValidationEngineV1()
    binding = OperationalBindingV1(
        antibody_id="ab_failing_fixture",
        rule_digest="sha256:rule_bytes",
        custody="HumanAdmitted",
        must_match_fixture=b"defect",
        must_not_match_fixture=b"clean",
    )

    # Validation fails on clean fixture
    proposal = engine.handle_validation_failure(binding, failure_kind="MUST_NOT_MATCH_FIXTURE_FIRED")

    assert isinstance(proposal, RetirementProposalV1)
    assert proposal.antibody_id == "ab_failing_fixture"
    # Custody remains HumanAdmitted until external epoch decision
    assert binding.custody == "HumanAdmitted", "Custody must not change before external decision"


def test_f_res_05_propagated_references_are_never_observations() -> None:
    """F-RES-05: Propagated or inherited antibody references cannot count toward support."""
    from omega_engine_epistemic_immune_system.use_cases.provisional_promotion import (
        ObservationSupportPolicyV1,
        RawObservationV1,
    )

    policy = ObservationSupportPolicyV1()

    # Propagated reference item
    inherited_ref = RawObservationV1(
        occurrence_id="occ_inherited",
        generating_model_id="model_inherited",
        scaffold_digest="scaffold_inherited",
        precedent_set_digest="prec_inherited",
        inheritance_root="root_inherited",
        is_propagated_reference=True,  # Propagated reference!
    )

    with pytest.raises(ValueError, match="PROPAGATED_REFERENCE_CANNOT_BE_OBSERVATION"):
        policy.register_observation(inherited_ref)
