"""Candidate checks must consume the actual finite witness. AuthorityEffect: None."""

from copy import deepcopy

import pytest

from omega_engine_pfp.infrastructure.pilot_runners.mssn_checks import evaluate_seed_response


def test_n02_missing_reports_are_not_filled_by_the_host():
    candidate = {
        "pair_decoded": "pair(a, b)", "edge_decoded": "edge(a -> b)",
        "distinct_meanings": True, "edge_separates_constant_q": False,
        "tagged_report_separates": True, "endpoint_support_count": 2,
    }
    assert not evaluate_seed_response("DEMO-N02", candidate).passed


def test_n08_self_reported_feasibility_is_not_a_dual_certificate():
    candidate = {
        "primal_value": 3, "dual_value": 3, "dual_feasible": True,
        "infeasible_test_rejected": True, "face_addition_retains_phi1": True,
        "potential": [0, 0, 0], "dual": [3, 0, 0],
    }
    assert not evaluate_seed_response("DEMO-N08", candidate).passed


def test_q23_missing_gram_matrix_cannot_be_certified_by_a_flag():
    candidate = {
        "h_gram_is_2_i2": True, "h_gram_scalar": 2,
        "c_is_scaled_unitary": False, "distorted_weights": ["1/3", "2/3"],
        "requires_field_extension": True, "required_extension_field": "Q(sqrt(2), i)",
    }
    assert not evaluate_seed_response("DEMO-Q23", candidate).passed


@pytest.mark.parametrize("seed", ["DEMO-N07", "DEMO-N14", "DEMO-Q20", "DEMO_07"])
def test_registered_seed_requires_a_structured_answer(seed):
    result = evaluate_seed_response(seed, {"passed": True})
    assert not result.passed
    assert "No Stage 5 host evaluator" not in " ".join(result.failure_reasons)


def test_every_seed_has_an_explicit_check_or_unavailable_obligation():
    from omega_engine_pfp.infrastructure.pilot_runner import load_seed_catalog

    for spec in load_seed_catalog().demos:
        result = evaluate_seed_response(spec.id, {})
        assert not result.passed
        assert "No Stage 5 host evaluator" not in " ".join(result.failure_reasons)


def test_exact_cochain_primal_dual_control_and_tampering():
    candidate = {"potential": [0, 0, 0], "dual": [1, 1, 1], "after_face": {
        "d0":[[-1,1,0],[0,-1,1],[1,0,-1]], "cochain":[1,1,1],
        "face_boundary":[1,1,1],"potential":[0,0,0],"dual":[1,1,1]}}
    result = evaluate_seed_response("DEMO-N08", candidate)
    assert result.passed, result.failure_reasons
    assert result.computed_evidence["before"]["primal_value"] == "3"
    assert result.computed_evidence["before"]["dual_value"] == "3"
    for bad in ([3, 0, 0], [True, 1, 1], [1.0, 1, 1]):
        mutation = deepcopy(candidate)
        mutation["dual"] = bad
        assert not evaluate_seed_response("DEMO-N08", mutation).passed


def test_same_vector_different_problem_is_checked_in_its_context():
    good = {
        "historical_residual": "1", "current_residual": "0",
        "historical_bound": "1", "current_bound": "1",
        "historical_accepted": False, "current_accepted": True,
    }
    assert evaluate_seed_response("DEMO_19", good).passed
    good["current_accepted"] = False
    assert not evaluate_seed_response("DEMO_19", good).passed
