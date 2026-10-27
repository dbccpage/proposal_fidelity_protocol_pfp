"""Tests for the PREREG-DA-001 adequacy battery. AuthorityEffect: None."""

from __future__ import annotations

import copy
import random

import pytest

from pfp.use_cases.detector_adequacy import battery, detectors, traces, witness_replay

N = 8


def _traces(family, seed=7):
    rng = random.Random(seed)
    return [family(traces.clean_trace(traces.make_item(rng, i)), rng) for i in range(N)]


def test_upper_bound_matches_rule_of_three_scale():
    assert battery.upper_bound_95(0, 300) == pytest.approx(1 - 0.05 ** (1 / 300), abs=1e-6)
    assert battery.upper_bound_95(300, 300) == 1.0
    assert battery.upper_bound_95(3, 300) > battery.upper_bound_95(0, 300)


@pytest.mark.parametrize("family", list(traces.MUTANT_FAMILIES.values()))
def test_collapsing_tree_extractor_is_green_on_every_mutant(family):
    for trace in _traces(family):
        assert detectors.run_detector("D0_E0_tree", trace).status == detectors.GREEN


@pytest.mark.parametrize("family", list(traces.CLEAN_FAMILIES.values()))
def test_disjoint_triangle_detector_certifies_clean_traces(family):
    for trace in _traces(family):
        assert witness_replay.answer_is_correct(trace)
        assert detectors.run_detector("D2_E1_disjoint_triangles", trace).status == detectors.GREEN


@pytest.mark.parametrize("family", list(traces.MUTANT_FAMILIES.values()))
def test_disjoint_triangle_detector_is_never_green_on_pre_lock_mutants(family):
    for trace in _traces(family):
        assert not witness_replay.answer_is_correct(trace)
        verdict = detectors.run_detector("D2_E1_disjoint_triangles", trace)
        assert verdict.status != detectors.GREEN
        if verdict.status == detectors.RED:
            assert witness_replay.replay_witness(trace, verdict.witness)


def test_citation_graph_extractor_misses_deleted_citations():
    statuses = {detectors.run_detector("D1_E0b_citation_graph", t).status
                for t in _traces(traces.m3_deleted_citation)}
    assert detectors.GREEN in statuses


def test_fabricated_witness_does_not_replay():
    trace = _traces(traces.c0_canonical)[0]
    assert not witness_replay.replay_witness(trace, (("s2", detectors.Fraction(1)),))
    assert not witness_replay.replay_witness(_traces(traces.m1_known_wrong)[0], ())


def test_float_field_is_refused_not_zeroed():
    trace = copy.deepcopy(_traces(traces.c0_canonical)[0])
    step = next(s for s in trace["steps"] if s["id"] == "s2")
    step["output"]["x"] = [float(v.split("/")[0]) for v in step["output"]["x"]]
    verdict = detectors.run_detector("D2_E1_disjoint_triangles", trace)
    assert verdict.status == detectors.NONCERTIFYING
    assert verdict.refusal == "NON_RATIONAL_FIELD"


def test_lock_refuses_unknown_commit():
    problems = battery.verify_lock(detectors.repo_root(), "0" * 40)["problems"]
    assert any(p.endswith("LOCK_COMMIT_MISMATCH") for p in problems)


def test_upper_bound_survives_pooled_sample_sizes():
    assert battery.upper_bound_95(1500, 3000) == pytest.approx(0.515177, abs=1e-5)


def test_judge_rejection_is_recorded_as_not_correct():
    trace = copy.deepcopy(_traces(traces.c0_canonical)[0])
    answer = next(s for s in trace["steps"] if s["kind"] == "answer")
    answer["output"]["x"] = answer["output"]["x"][:-1]
    row = battery._evaluate(trace)
    assert row["answer_correct"] is not True
    assert all(row[name]["status"] != detectors.GREEN for name in ("D2_E1_disjoint_triangles",))


def test_local_detector_misses_drifted_given_copy_and_restricted_misses_upstream():
    from pfp.use_cases.detector_adequacy import heldout, local_detector

    for trace in _traces(heldout.HELDOUT_FAMILIES["H1_drifted_given_copy"]):
        assert local_detector.run_local("D3_local_all", trace).status == detectors.GREEN
    for trace in _traces(traces.m1_known_wrong):
        verdict = local_detector.run_local("D3_local_all", trace)
        assert verdict.status == detectors.RED
        assert witness_replay.replay_witness(trace, verdict.witness)
    for trace in _traces(traces.m4_mutated_tool_output):
        assert local_detector.run_local("D4_local_restricted", trace).status == detectors.GREEN


def test_lggr_adapter_certifies_adequacy_while_flagging_length_mismatch():
    """Stage A finding, moved out of the battery so the production package imports no Adversary."""
    from adversary.infrastructure.lggr_adapter import LggrGluingAdapter

    mutants = {**traces.MUTANT_FAMILIES, **battery.heldout_families()}
    families = {"C0_canonical": ("clean", traces.CLEAN_FAMILIES["C0_canonical"]),
                **{name: ("mutant", fn) for name, fn in mutants.items()}}
    report = battery.lggr_report(battery.run(N, 11, families)["lggr_samples"], LggrGluingAdapter)
    assert report["verdict_counts"].get("NegativeGluingDefect_LocalGreenGlobalRed") == N
    assert report["detector_adequacy_certified"] is True
    assert report["adequacy_failures"] == []
