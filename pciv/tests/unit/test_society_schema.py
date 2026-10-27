"""Tests for PromptSocietyV1 and PromptCivilizationV1 normative data models (NF-01).

AuthorityEffect: None.
Zero-Float Law: Uses exact rational arithmetic (fractions.Fraction).
"""

from fractions import Fraction
import pytest

from pciv.domain.society import (
    AggregateFitnessVectorV1,
    MigrationPolicyV1,
    PromptCivilizationV1,
    PromptSocietyV1,
)


def test_aggregate_fitness_vector_pareto_conservation() -> None:
    active = AggregateFitnessVectorV1(
        accuracy_rational="4/5",
        cost_rational="10/1",
        robustness_rational="9/10",
    )
    assert active.accuracy == Fraction(4, 5)
    assert active.cost == Fraction(10, 1)
    assert active.robustness == Fraction(9, 10)

    # Candidate with lower cost (strictly better on cost, equal on others) -> pareto replaces
    better_cost = AggregateFitnessVectorV1(
        accuracy_rational="4/5",
        cost_rational="8/1",
        robustness_rational="9/10",
    )
    assert better_cost.weakly_dominates(active) is True
    assert better_cost.strictly_dominates_any(active) is True
    assert better_cost.pareto_replaces(active) is True

    # Candidate with worse accuracy (3/5 < 4/5) -> does not replace even if cheaper
    cheaper_but_worse_acc = AggregateFitnessVectorV1(
        accuracy_rational="3/5",
        cost_rational="5/1",
        robustness_rational="9/10",
    )
    assert cheaper_but_worse_acc.weakly_dominates(active) is False
    assert cheaper_but_worse_acc.pareto_replaces(active) is False

    # Identical vector -> does not strictly dominate any coordinate -> does not replace
    identical = AggregateFitnessVectorV1(
        accuracy_rational="4/5",
        cost_rational="10/1",
        robustness_rational="9/10",
    )
    assert identical.weakly_dominates(active) is True
    assert identical.strictly_dominates_any(active) is False
    assert identical.pareto_replaces(active) is False


def test_aggregate_fitness_vector_validation_errors() -> None:
    with pytest.raises(ValueError, match="ACCURACY_OUT_OF_BOUNDS_0_1"):
        AggregateFitnessVectorV1("6/5", "10/1", "1/2")

    with pytest.raises(ValueError, match="COST_CANNOT_BE_NEGATIVE"):
        AggregateFitnessVectorV1("1/2", "-5/1", "1/2")

    with pytest.raises(ValueError, match="ROBUSTNESS_OUT_OF_BOUNDS_0_1"):
        AggregateFitnessVectorV1("1/2", "5/1", "11/10")

    with pytest.raises(ValueError, match="INVALID_RATIONAL_FORMAT"):
        AggregateFitnessVectorV1("0.8", "5/1", "1/2")


def test_migration_policy_bounded_migration_law() -> None:
    policy = MigrationPolicyV1(
        max_incoming_per_epoch=5,
        taxonomic_admissibility=("core.math.*", "core.physics"),
    )
    # Admitted exact match within quota
    assert policy.is_migration_allowed("core.physics", 3, 100) is True
    # Admitted prefix match within quota
    assert policy.is_migration_allowed("core.math.integral", 4, 100) is True
    # Inadmissible domain
    assert policy.is_migration_allowed("core.biology", 2, 100) is False
    # Exceeds quota (6 > 5)
    assert policy.is_migration_allowed("core.physics", 6, 100) is False
    # Negative or zero incoming
    assert policy.is_migration_allowed("core.physics", 0, 100) is False
    # A stem wildcard does not match a longer label, and an exact label grants no child.
    assert policy.is_migration_allowed("core.mathematics", 1, 100) is False
    assert policy.is_migration_allowed("core.physics.quantum", 1, 100) is False


def test_prompt_society_normative_digest() -> None:
    soc = PromptSocietyV1(
        society_id="sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        domain_protocol="core.math.integral:v1",
        family_ids=("fam_alpha", "fam_beta"),
        aggregate_fitness_vector=AggregateFitnessVectorV1("4/5", "10/1", "9/10"),
        migration_policy=MigrationPolicyV1(5, ("core.math.*",)),
        created_utc="2026-10-09T00:00:00Z",
    )
    digest = soc.canonical_digest()
    assert digest.startswith("sha256:")
    assert len(digest) == 71


def test_prompt_civilization_budget_solvency_law() -> None:
    civ = PromptCivilizationV1(
        civilization_id="sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        society_ids=("soc_1", "soc_2"),
        global_immune_registry="oeeis:registry:v1",
        reservation_budget_pool=50_000,
        governance_epoch=0,
        created_utc="2026-10-09T00:00:00Z",
        authority_effect="None",
    )
    assert civ.check_budget_solvency(40_000) is True
    assert civ.check_budget_solvency(50_000) is True

    with pytest.raises(PermissionError, match="BUDGET_OVERDRAFT_REFUSED"):
        civ.check_budget_solvency(50_001)

    with pytest.raises(ValueError, match="AUTHORITY_EFFECT_MUST_BE_NONE"):
        PromptCivilizationV1(
            civilization_id="sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            society_ids=(),
            global_immune_registry="oeeis:registry:v1",
            reservation_budget_pool=1000,
            governance_epoch=0,
            created_utc="2026-10-09T00:00:00Z",
            authority_effect="SovereignAuthorization",
        )
