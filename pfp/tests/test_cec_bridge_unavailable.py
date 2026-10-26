"""Unconfigured CEC bridges cannot turn caller assertions into metrics."""

import pytest

from omega_engine_pfp.infrastructure.adapters.cec_bridge_adapter import (
    CecBridgeAdapter,
)


@pytest.mark.parametrize(
    "context",
    [{}, {"passed": True, "metric_score": 1.0}, {"witness": "unverified"}],
)
def test_unconfigured_bridge_never_certifies_caller_context(context):
    before = dict(context)
    result = CecBridgeAdapter().evaluate_metric("target_01", context)

    assert result["status"] == "REFUSED"
    assert result["refusal_code"] == "CEC_EVALUATOR_UNAVAILABLE"
    assert result["metric_score"] is None
    assert result["authority_effect"] == "None"
    assert result["target_id"] == "target_01"
    assert "passed" not in result
    assert context == before
