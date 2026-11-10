"""C005 live retirement and explicit historical fixture controls. No provider sends."""

import pytest

from .client import GovernedClient, PfpLiveRouteRequired
from .controls import ControlKind, get_control_config


@pytest.mark.parametrize("has_credential", [False, True])
def test_legacy_live_client_refuses_before_mock_or_provider(monkeypatch, has_credential):
    import sys
    from types import SimpleNamespace

    if has_credential:
        monkeypatch.setenv("OPENROUTER_API_KEY", "not-a-real-key")
    else:
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    provider_constructions = []

    def forbidden_provider(**kwargs):
        provider_constructions.append(kwargs)
        raise AssertionError("Legacy C005 must not construct a provider")

    _missing_module = object()
    _previous_module = sys.modules.get("openai", _missing_module)
    try:
        sys.modules["openai"] = SimpleNamespace(OpenAI=forbidden_provider)
        client = GovernedClient()
        with pytest.raises(PfpLiveRouteRequired, match="PFP_LIVE_ROUTE_REQUIRED"):
            client.complete("fixture question", get_control_config(ControlKind.NONE))
        assert provider_constructions == []
        assert client.call_history == []
        assert client.budget_controller.call_count == 0
        assert client.budget_controller.total_billed_usd == 0
    finally:
        if _previous_module is _missing_module:
            sys.modules.pop("openai", None)
        else:
            sys.modules["openai"] = _previous_module


def test_legacy_private_live_entrypoint_also_refuses_before_provider(monkeypatch):
    import sys
    from types import SimpleNamespace

    def forbidden_provider(**kwargs):
        raise AssertionError("Retired live entrypoint constructed a provider")

    _missing_module = object()
    _previous_module = sys.modules.get("openai", _missing_module)
    try:
        sys.modules["openai"] = SimpleNamespace(OpenAI=forbidden_provider)
        client = GovernedClient(mock_mode=True)
        with pytest.raises(PfpLiveRouteRequired, match="PFP_LIVE_ROUTE_REQUIRED"):
            client._execute_real(
                "fixture question", get_control_config(ControlKind.NONE), 64, 0.0, 0.0
            )
        assert client.call_history == []
    finally:
        if _previous_module is _missing_module:
            sys.modules.pop("openai", None)
        else:
            sys.modules["openai"] = _previous_module


@pytest.mark.parametrize("mock_mode", [False, None, "true", 1])
def test_mock_entrypoint_requires_explicit_true(mock_mode):
    client = GovernedClient(mock_mode=mock_mode)
    with pytest.raises(PfpLiveRouteRequired, match="PFP_LIVE_ROUTE_REQUIRED"):
        client._execute_mock("fixture question", get_control_config(ControlKind.NONE), 64, 0.0)
    assert client.call_history == []
    assert client.budget_controller.call_count == 0


@pytest.mark.parametrize("has_credential", [False, True])
def test_explicit_mock_fixture_keeps_content_and_labels(monkeypatch, has_credential):
    if has_credential:
        monkeypatch.setenv("OPENROUTER_API_KEY", "not-a-real-key")
    else:
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    client = GovernedClient(mock_mode=True)
    client.set_mock_response("fixture question", '{"fixture":true}')
    receipt = client.complete("fixture question", get_control_config(ControlKind.NONE))
    assert receipt.content == '{"fixture":true}'
    assert receipt.provider == "mock"
    assert receipt.raw_response == {"mock": True}
    assert receipt.generation_id == "mock-gen-1"
    assert receipt.cost_usd == 0.00005  # Retained synthetic fixture accounting.
    assert client.call_history == [receipt]
    assert client.budget_controller.call_count == 1


@pytest.mark.parametrize(
    "case, reply, expected_status, expected_refusal",
    [
        (
            {"kind": "consistency", "prompt": "fixture", "edges": [["a", "b", 2]]},
            '{"verdict":"CONSISTENT","certificate":{"a":"0","b":"2"}}',
            "CONSISTENT",
            None,
        ),
        (
            {"kind": "consistency", "prompt": "fixture", "edges": [["a", "b", 2]]},
            '{"verdict":"CONSISTENT","certificate":{"a":"0","b":"3"}}',
            "UNKNOWN",
            "FALSE_WITNESS",
        ),
        (
            {
                "kind": "cycle_repair",
                "prompt": "fixture",
                "edges": [["a", "b", 2], ["b", "c", 2], ["c", "a", 2]],
                "weights": [1, 2, 3],
            },
            '{"status":"SOLVED","repaired":["-4","2","2"],"weighted_l1":"6"}',
            "SOLVED",
            None,
        ),
        (
            {
                "kind": "cycle_repair",
                "prompt": "fixture",
                "edges": [["a", "b", 2], ["b", "c", 2], ["c", "a", 2]],
                "weights": [1, 2, 3],
            },
            '{"status":"SOLVED","repaired":["2","2","-4"],"weighted_l1":"18"}',
            "UNKNOWN",
            "SUBOPTIMAL_OR_INVALID_REPAIR",
        ),
    ],
)
def test_explicit_fixture_still_uses_real_task_checker(
    case, reply, expected_status, expected_refusal
):
    from .solve import solve_c005_case

    client = GovernedClient(mock_mode=True)
    client.set_mock_response("fixture", reply)
    result = solve_c005_case(case, client, ControlKind.NONE)
    assert result.status == expected_status
    assert result.refusal == expected_refusal
    assert client.call_history[0].provider == "mock"
    assert client.call_history[0].raw_response == {"mock": True}


def test_legacy_solver_does_not_turn_route_refusal_into_fixture_success(monkeypatch):
    from .solve import solve_c005_case

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    client = GovernedClient()
    result = solve_c005_case(
        {"kind": "consistency", "prompt": "fixture", "edges": [["a", "b", 2]]},
        client,
        ControlKind.NONE,
    )
    assert result.status == "UNKNOWN"
    assert result.refusal == "PROVIDER_REFUSAL_OR_INCOMPLETE"
    assert "PFP_LIVE_ROUTE_REQUIRED" in result.payload["error"]
    assert result.cost_usd is None
    assert client.call_history == []
    assert client.budget_controller.call_count == 0
