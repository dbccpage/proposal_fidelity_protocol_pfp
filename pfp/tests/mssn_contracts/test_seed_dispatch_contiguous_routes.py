"""Finite manual witnesses and no-tool routing controls; no all-seed sweep."""

from copy import deepcopy

import pytest

from omega_engine_pfp.infrastructure.pilot_runners import seed_advanced_checks as advanced
from omega_engine_pfp.infrastructure.pilot_runners import seed_checks as checks
from omega_engine_pfp.infrastructure.pilot_runners import seed_core_checks as core


class RouteStop(RuntimeError):
    """Stop a selected delegate before native, Lean or mathematical work."""


@pytest.mark.parametrize("seed,payload", [
    ("DEMO_01", {"raw": "<>", "admitted_data": [], "admitted_forms": [],
                 "admitted_instances": [], "replay_packets": ["<>"],
                 "profile": "mss0_ground_boundary"}),
    ("DEMO_02", {"old_language": ["<>"], "new_language": ["<>", "<a>"],
                 "inclusion": {"<>": "<>"}, "down_map": {"<>": "<>", "<a>": "NON_DESCENT"}}),
    ("DEMO-N02", {"pair_decoded": ["a", "b"], "edge_decoded": {"source": "a", "target": "b"},
                  "reports": [0, 0], "tagged_reports": [[0, 0], [0, 1]],
                  "endpoint_support": ["a", "b"], "occurrence_counts": [1, 2, 3]}),
    ("DEMO_19", {"historical_residual": "1", "current_residual": "0",
                 "historical_bound": "1", "current_bound": "1",
                 "historical_accepted": False, "current_accepted": True}),
    ("DEMO-Q20", {"conjugate": ["3/5", "-4/5"], "squared_modulus": "1",
                  "inverse": ["3/5", "-4/5"], "product": ["1", "0"],
                  "zero_inverse": "REFUSED", "invalid_scalar": "REFUSED"}),
])
def test_handwritten_finite_packets_and_missing_field_refusal(seed, payload):
    original = deepcopy(payload)
    assert checks.check(seed, payload) == original
    assert payload == original
    mutation = deepcopy(payload)
    mutation.pop(next(iter(mutation)))
    retained = deepcopy(mutation)
    with pytest.raises(checks.SeedCheckFailure, match="MISSING_OR_EXTRA_FIELDS"):
        checks.check(seed, mutation)
    assert mutation == retained


@pytest.mark.parametrize("bad", [True, 1.0, "1"])
def test_n02_integer_occurrences_do_not_accept_equivalent_non_integer_types(bad):
    payload = {"pair_decoded": ["a", "b"], "edge_decoded": {"source": "a", "target": "b"},
               "reports": [0, 0], "tagged_reports": [[0, 0], [0, 1]],
               "endpoint_support": ["a", "b"], "occurrence_counts": [bad, 2, 3]}
    original = deepcopy(payload)
    with pytest.raises(checks.SeedCheckFailure, match="WRONG_VALUE_OR_TYPE"):
        checks.check("DEMO-N02", payload)
    assert payload == original


@pytest.mark.parametrize("bad", [0, 1, "True", 1.0])
def test_dual_context_boolean_field_retains_exact_boolean_type(bad):
    payload = {"historical_residual": "1", "current_residual": "0", "historical_bound": "1",
               "current_bound": "1", "historical_accepted": False, "current_accepted": bad}
    original = deepcopy(payload)
    with pytest.raises(checks.SeedCheckFailure, match="WRONG_VALUE_OR_TYPE"):
        checks.check("DEMO_19", payload)
    assert payload == original


@pytest.mark.parametrize("selector", [True, 1, 1.0])
def test_direct_mss_selector_keeps_existing_permissive_equality(selector):
    result = checks.mss_expected(selector)
    assert result["raw"] == "<>"
    assert result["admitted_data"] == []


@pytest.mark.parametrize("selector", [False, -1, 7, 13, 51])
def test_direct_mss_unsupported_selector_keeps_dictionary_key_error(selector):
    with pytest.raises(KeyError) as error:
        checks.mss_expected(selector)
    assert error.value.args == (selector,)


@pytest.mark.parametrize("selector", ["1", []])
def test_direct_mss_selector_keeps_existing_type_error(selector):
    with pytest.raises(TypeError, match="unhashable|not supported"):
        checks.mss_expected(selector)


@pytest.mark.parametrize("number,reason", [
    (14, "WEIGHTED_HODGE_RECONSTRUCTION_ADJOINTS"),
    (23, "TWO_CYCLE_PRIMAL_DUAL_OPTIMUM"),
])
def test_direct_unavailable_obligations_keep_their_original_reason(number, reason):
    with pytest.raises(checks.SeedCheckFailure, match="^CHECKER_UNAVAILABLE: " + reason + "$"):
        checks.mss_expected(number)


@pytest.mark.parametrize("seed,reason", [
    ("DEMO-N08", "UNKNOWN_SEED"),
    ("DEMO-N15", "POLICY_ATTACHMENT_REPLAY_UNAVAILABLE: actual permitted attachment event required"),
    ("DEMO-Q22", "LOCAL_CHANNEL_WITNESS_REQUIRED: submit and check exact Kraus completeness and transported marginals"),
])
def test_direct_review_keeps_candidate_only_obligations(seed, reason):
    with pytest.raises(checks.SeedCheckFailure, match="^" + reason + "$"):
        checks.review_expected(seed)


def test_public_guards_keep_unknown_id_before_candidate_type_refusal():
    with pytest.raises(checks.SeedCheckFailure, match="^UNKNOWN_SEED$"):
        checks.check("MISSING", None)
    with pytest.raises(checks.SeedCheckFailure, match="^CANDIDATE_NOT_OBJECT$"):
        checks.check("DEMO_01", None)


@pytest.mark.parametrize("seed", ["DEMO-N00", "DEMO-N01", "DEMO-N12"])
def test_native_review_route_stops_before_external_work(monkeypatch, seed):
    calls = []

    def stop(actual):
        calls.append(actual)
        raise RouteStop("native route only")

    monkeypatch.setattr(core, "native_expected", stop)
    with pytest.raises(RouteStop, match="^native route only$"):
        checks.review_expected(seed)
    assert calls == [seed]


@pytest.mark.parametrize("number", [3, 11, 16])
def test_core_mss_route_preserves_argument_and_exception(monkeypatch, number):
    calls = []

    def stop(actual):
        calls.append(actual)
        raise RouteStop("core route only")

    monkeypatch.setattr(core, "core_expected", stop)
    with pytest.raises(RouteStop, match="^core route only$"):
        checks.mss_expected(number)
    assert calls == [number]


@pytest.mark.parametrize("number", [20, 27, 28, 31, 48, 49, 50])
def test_advanced_expected_route_stops_before_symbolic_or_lean_work(monkeypatch, number):
    calls = []

    def stop(actual):
        calls.append(actual)
        raise RouteStop("advanced expected only")

    monkeypatch.setattr(advanced, "advanced_expected", stop)
    with pytest.raises(RouteStop, match="^advanced expected only$"):
        checks.mss_expected(number)
    assert calls == [number]


@pytest.mark.parametrize("number", [27, 28, 31, 48, 49, 50])
def test_other_advanced_public_ids_use_expected_not_advanced_check(monkeypatch, number):
    calls = []

    def expected(actual):
        calls.append(("expected", actual))
        raise RouteStop("generic advanced tail")

    def check_route(actual, payload):
        calls.append(("check", actual, payload))
        raise RouteStop("unexpected special route")

    monkeypatch.setattr(advanced, "advanced_expected", expected)
    monkeypatch.setattr(advanced, "advanced_check", check_route)
    with pytest.raises(RouteStop, match="^generic advanced tail$"):
        checks.check(f"DEMO_{number:02d}", {})
    assert calls == [("expected", number)]


def test_only_demo20_uses_advanced_check_before_external_work(monkeypatch):
    payload = {"unchanged": []}
    calls = []

    def stop(number, actual):
        calls.append((number, actual))
        raise RouteStop("special20 route only")

    monkeypatch.setattr(advanced, "advanced_check", stop)
    with pytest.raises(RouteStop, match="^special20 route only$"):
        checks.check("DEMO_20", payload)
    assert len(calls) == 1 and calls[0][0] == 20 and calls[0][1] is payload


@pytest.mark.parametrize("seed,delegate", [("DEMO-Q22", "channel_check"), ("DEMO_14", "hodge_check")])
def test_candidate_only_core_routes_preserve_payload_identity(monkeypatch, seed, delegate):
    payload = {"unchanged": []}
    calls = []

    def stop(actual):
        calls.append(actual)
        raise RouteStop("candidate route only")

    monkeypatch.setattr(core, delegate, stop)
    with pytest.raises(RouteStop, match="^candidate route only$"):
        checks.check(seed, payload)
    assert len(calls) == 1 and calls[0] is payload


def test_n15_retains_two_attachment_calls_and_selected_none_is_not_a_miss(monkeypatch):
    calls = []

    def attachment():
        calls.append("attachment")
        return {"manual_marker": 1}

    monkeypatch.setattr(checks, "attachment_expected", attachment)
    assert checks.check("DEMO-N15", {"manual_marker": 1}) == {"manual_marker": 1}
    assert calls == ["attachment", "attachment"]
    monkeypatch.setattr(core, "core_expected", lambda number: None)
    assert checks.mss_expected(3) is None
    monkeypatch.setattr(core, "native_expected", lambda seed: None)
    assert checks.review_expected("DEMO-N00") is None
    monkeypatch.setattr(core, "channel_check", lambda payload: None)
    assert checks.check("DEMO-Q22", {}) is None


@pytest.mark.parametrize("seed,payload,primal", [
    ("DEMO-N08", {"potential": [0, 0, 0], "dual": [1, 1, 1], "after_face": {
        "d0": [[-1, 1, 0], [0, -1, 1], [1, 0, -1]], "cochain": [1, 1, 1],
        "face_boundary": [1, 1, 1], "potential": [0, 0, 0], "dual": [1, 1, 1]}}, "3"),
    ("DEMO_13", {"potential": [0, 2, 4], "dual": [-1, 1, -1], "d1_cochain": [-1],
        "classification": "NONCLOSED_NOT_H1_CLASS", "repair_claim": "OPTIMAL_NONZERO_RESIDUAL_NOT_EXACT_REPAIR"}, "1"),
    ("DEMO_23", {"potential": [0] * 5, "dual": [1, 1, 1, 5, 5, 5],
        "cycles": [[1, 1, 1, 0, 0, 0], [0, 0, 0, 1, 1, 1]], "pairings": [1, 2],
        "zero_repair": "IMPOSSIBLE_NONZERO_CYCLE_PAIRINGS"}, "11"),
])
def test_manual_primal_dual_witnesses_and_bool_mutation(seed, payload, primal):
    original = deepcopy(payload)
    result = checks.check(seed, payload)
    computed = result["before"] if seed == "DEMO-N08" else result
    assert computed["primal_value"] == computed["dual_value"] == primal
    assert payload == original
    mutation = deepcopy(payload)
    mutation["dual"][0] = True
    retained = deepcopy(mutation)
    with pytest.raises(checks.SeedCheckFailure, match="^NON_EXACT_RATIONAL$"):
        checks.check(seed, mutation)
    assert mutation == retained


def test_local34_stays_outside_advanced_delegation_and_q21_aliases_survive(monkeypatch):
    def stop(number):
        raise RouteStop(f"advanced route {number}")

    monkeypatch.setattr(advanced, "advanced_expected", stop)
    result = checks.mss_expected(34)
    assert result["coefficient_profile"] == "F2"
    assert result["global_sections"] == result["global_support"] == []
    first, second = checks.review_expected("DEMO-Q21"), checks.review_expected("DEMO-Q21")
    assert first["weights"][0] is first["weights"][1]
    assert first["weights"] is not second["weights"]
