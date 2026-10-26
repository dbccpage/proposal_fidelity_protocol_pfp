"""Comprehensive unit tests for Prompt Civilization & Lamarckian Evolution (Levels 00–10).

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest
from prompt_civilization_core import (
    EcologicalReserve,
    Genotype,
    Individual,
    IslandEcology,
    LamarckianEngine,
    LineageDAG,
    LineagePageRank,
    LineageTaintTracker,
    MutationForge,
    ParetoSelector,
    Phenotype,
    PrecedentMemory,
    PromptCivilizationEventLog,
)


def _make_sample_individual(
    ind_id: int, gen: int, parents=(), delta="", latency=10.0, cost=100, score=0.8
) -> Individual:
    gt = Genotype(id=ind_id, template=f"Template {ind_id}", parameter_count=2, token_length=5)
    pt = Phenotype(
        latency_ms=latency, token_cost=cost, correctness_score=score, reflection_delta=delta
    )
    return Individual(id=ind_id, generation=gen, genotype=gt, phenotype=pt, parent_ids=parents)


def test_level_00_substrate_and_packaging():
    ind = _make_sample_individual(1, 0)
    assert ind.id == 1
    assert ind.generation == 0
    assert ind.genotype.token_length == 5
    assert len(ind.genotype.digest()) == 64
    assert ind.phenotype.correctness_score == 0.8
    assert ind.tainted is False


def test_level_01_lineage_dag_and_causal_descent():
    dag = LineageDAG()
    root = _make_sample_individual(1, 0)
    child1 = _make_sample_individual(2, 1, parents=(1,))
    child2 = _make_sample_individual(3, 1, parents=(1,))
    grandchild = _make_sample_individual(4, 2, parents=(2, 3))

    for node in (root, child1, child2, grandchild):
        dag.add_individual(node)

    assert dag.is_acyclic() is True
    assert dag.get_ancestors(4) == {1, 2, 3}
    assert dag.get_descendants(1) == {2, 3, 4}
    assert dag.causal_depth(1) == 0
    assert dag.causal_depth(4) == 2

    # Verify causal ordering enforcement
    with pytest.raises(ValueError, match="Causal violation"):
        invalid_child = _make_sample_individual(5, 0, parents=(4,))
        dag.add_individual(invalid_child)


def test_level_02_mutation_forge():
    forge = MutationForge(seed=123)
    parent_gt = Genotype(
        id=10, template="Answer in Python precisely", parameter_count=1, token_length=4
    )

    # Point mutation
    mut = forge.point_mutate(parent_gt, ("Python", "Rust"))
    assert "Rust" in mut.template
    assert mut.id != parent_gt.id

    # Crossover
    other_gt = Genotype(
        id=11, template="Provide exact types only", parameter_count=1, token_length=4
    )
    cross = forge.crossover(parent_gt, other_gt, split_ratio=0.5)
    assert cross.token_length > 0
    assert cross.id != parent_gt.id

    # Structural expansion
    expanded = forge.structural_expansion(parent_gt, "Check edge conditions.")
    assert "## Clause" in expanded.template
    assert expanded.parameter_count == parent_gt.parameter_count + 1


def test_level_03_lamarckian_retro_inheritance():
    engine = LamarckianEngine()
    ind = _make_sample_individual(1, 0, delta="Enforce non-negative integer bounds")
    adapted = engine.retro_inherit(ind)

    assert adapted.generation == ind.generation + 1
    assert adapted.parent_ids == (ind.id,)
    assert "Enforce non-negative integer bounds" in adapted.genotype.template
    assert adapted.phenotype.correctness_score > ind.phenotype.correctness_score

    # Empty delta identity retraction
    ind_empty = _make_sample_individual(2, 0, delta="")
    adapted_empty = engine.retro_inherit(ind_empty)
    assert adapted_empty.genotype == ind_empty.genotype


def test_level_04_pareto_selection():
    selector = ParetoSelector()
    # ind1 is superior in all objectives
    ind1 = _make_sample_individual(1, 0, latency=5.0, cost=50, score=0.95)
    # ind2 is strictly dominated by ind1
    ind2 = _make_sample_individual(2, 0, latency=10.0, cost=100, score=0.80)
    # ind3 trades off lower cost for lower correctness (non-dominated relative to ind1)
    ind3 = _make_sample_individual(3, 0, latency=4.0, cost=40, score=0.90)

    assert selector.dominates(ind1.phenotype, ind2.phenotype) is True
    assert selector.dominates(ind1.phenotype, ind3.phenotype) is False

    population = [ind1, ind2, ind3]
    front = selector.extract_pareto_front(population)
    front_ids = {ind.id for ind in front}
    assert front_ids == {1, 3}


def test_level_05_inverse_lineage_pagerank():
    dag = LineageDAG()
    root = _make_sample_individual(1, 0)
    c1 = _make_sample_individual(2, 1, parents=(1,))
    c2 = _make_sample_individual(3, 1, parents=(1,))
    gc = _make_sample_individual(4, 2, parents=(2,))

    for node in (root, c1, c2, gc):
        dag.add_individual(node)

    ranker = LineagePageRank(damping=0.85)
    ranks = ranker.compute_ranks(dag)

    assert len(ranks) == 4
    # Root ancestor has highest authority due to multiple surviving downstream branches
    assert ranks[1] > ranks[4]
    assert pytest.approx(sum(ranks.values()), rel=1e-4) == 1.0


def test_level_06_precedent_retrieval_and_evaporation():
    memory = PrecedentMemory(decay_rate=0.5)
    ind = _make_sample_individual(1, 0)
    memory.record_precedent("bug_fix_pattern", ind, initial_score=1.0)

    assert memory.retrieve("bug_fix_pattern") == ind
    # Step decay reduces score
    memory.step_decay()
    assert memory.entries["bug_fix_pattern"][1] < 1.0


def test_level_07_ecological_reserves():
    reserve = EcologicalReserve(capacity_k=2)
    ind1 = _make_sample_individual(1, 0, latency=5.0, cost=50, score=0.95)
    ind2 = _make_sample_individual(2, 0, latency=10.0, cost=100, score=0.80)
    ind3 = _make_sample_individual(3, 0, latency=4.0, cost=40, score=0.90)

    pruned = reserve.prune_population([ind1, ind2, ind3])
    assert len(pruned) == 2
    # The two non-dominated Pareto front members are preserved
    pruned_ids = {ind.id for ind in pruned}
    assert 1 in pruned_ids


def test_level_08_lineage_taint_and_invalidation():
    dag = LineageDAG()
    root = _make_sample_individual(1, 0)
    c1 = _make_sample_individual(2, 1, parents=(1,))
    c2 = _make_sample_individual(3, 1, parents=(1,))
    gc1 = _make_sample_individual(4, 2, parents=(2,))

    for node in (root, c1, c2, gc1):
        dag.add_individual(node)

    tracker = LineageTaintTracker(dag)
    affected = tracker.mark_tainted(2)

    assert affected == {2, 4}
    assert tracker.is_quarantined(2) is True
    assert tracker.is_quarantined(4) is True
    assert tracker.is_quarantined(3) is False  # sibling branch uncorrupted


def test_level_09_durable_event_log():
    log = PromptCivilizationEventLog()
    log.append_event("INDIVIDUAL_CREATED", {"id": 1, "gen": 0})
    log.append_event("MUTATION_APPLIED", {"parent": 1, "child": 2})

    assert len(log.events) == 2
    assert log.verify_integrity() is True

    # Tampering with record invalidates audit check
    log.events[0]["data"]["id"] = 999
    assert log.verify_integrity() is False


def test_level_10_island_ecology():
    ecology = IslandEcology(island_names=["IslandA", "IslandB"], capacity_per_island=5)
    ind = _make_sample_individual(1, 0)
    ecology.populate("IslandA", ind)

    assert len(ecology.islands["IslandA"]) == 1
    assert len(ecology.islands["IslandB"]) == 0

    migrated = ecology.migrate("IslandA", "IslandB", 1)
    assert migrated is True
    assert len(ecology.islands["IslandA"]) == 0
    assert len(ecology.islands["IslandB"]) == 1
