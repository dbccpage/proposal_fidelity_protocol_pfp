"""
Unit tests for the 100-Trial Chordal Projection Fuzz Repair Benchmark
(Paper 032 Section 7.2). Reference: Paper 032 (PO-032), claim PO032-C44.
"""

import random
from fractions import Fraction

from chordal_fuzz_repair_benchmark import (
    build_2_tree,
    run_chordal_fuzz_benchmark,
    run_trial,
)
from l1_symbol_game_governor import ConstraintGraph


def test_2_tree_structure_edge_count_and_chordality():
    """A 2-tree on n vertices is connected, irreflexive, with 2n-3 edges."""
    for n in range(5, 11):
        graph = build_2_tree(n, random.Random(n))
        assert isinstance(graph, ConstraintGraph)
        assert len(graph.vertices) == n
        assert len(graph.edges) == 2 * n - 3          # defining count of a 2-tree
        assert all(e.u != e.v for e in graph.edges)   # irreflexivity
        assert len(graph.connected_components()) == 1  # connected
        assert len(graph.edges) - n + 1 == n - 2       # cycle rank


def test_single_projection_cut_reaches_exact_zero_defect():
    """A single relational CUT drives a genuine defect to exact rational zero."""
    for seed in (0, 1, 7, 13, 42, 99):
        r = run_trial(seed, with_governor=False)
        assert r.defect_present is True         # a real holonomy defect existed
        assert Fraction(r.phi1_before) > 0
        assert Fraction(r.phi1_after) == 0      # exact rational zero, no epsilon
        assert r.single_cut is True


def test_governor_admits_projection_replacement_as_exact_repair():
    """The governor's monotonic-descent gate admits the CUT as ExactRepair."""
    r = run_trial(3, with_governor=True)
    assert r.governor_admitted is True
    assert r.governor_status == "ExactRepair"
    assert Fraction(r.phi1_after) == 0


def test_full_100_trial_convergence():
    """All 100 deterministic trials converge to zero defect after one CUT."""
    summary = run_chordal_fuzz_benchmark(n_trials=100, with_governor=False)
    assert summary["n_trials"] == 100
    assert summary["convergence_rate"] == 1.0
    assert summary["atomic_projection_replacement_rate"] == 1.0
    assert summary["trials_with_defect"] == 100
    assert summary["vertex_range"] == [5, 10]


def test_governor_agreement_on_small_sample():
    """On a small sample the governor and the LP solver agree and all repair."""
    summary = run_chordal_fuzz_benchmark(n_trials=6, with_governor=True)
    assert summary["governor_all_exact_repair"] is True
    assert summary["convergence_rate"] == 1.0
