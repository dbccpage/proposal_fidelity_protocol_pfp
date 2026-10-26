"""Independent lift/learning ingress must never upgrade a malformed packet."""

import json

import pytest

from omega_engine_woland.tests.pilots.relational_spacetime.typed_signals import build_prompt
from omega_engine_woland.tests.pilots.relational_spacetime.typed_signals import ingress
from omega_engine_woland.tests.pilots.relational_spacetime.typed_signals import limits_for
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import BY_ID
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import proposal_body
from omega_engine_woland.tests.pilots.relational_spacetime.finite_checks import evaluate
from omega_engine_woland.tests.pilots.relational_spacetime.finite_fixtures import fixture_payload


def test_side_channel_preserves_packet_refusal():
    pilot = next(iter(BY_ID))
    packet = fixture_payload(pilot, "fixture")
    body = proposal_body(packet)
    packet["requested_lifts"] = [{"id": "EXACT_RATIONAL", "reason": "exact arithmetic"}]
    packet["learning"] = body.pop("learning")
    content = json.dumps(packet)
    assert evaluate(pilot, "fixture", content)[0]["schema_status"] == "REFUSED"
    lifts, learning, _ = ingress(pilot, content)
    assert lifts[0]["json_pointer"] == "/requested_lifts/0"
    assert learning[0]["json_pointer"] == "/learning/0"


@pytest.mark.parametrize(
    "content",
    [
        '{"derived_under_policy":"SPK-001","learning":[}',
        '{"derived_under_policy":"SPK-001","derived_under_policy":"SPK-001"}',
        "{}",
    ],
)
def test_no_json_or_stamp_repair(content):
    assert ingress(next(iter(BY_ID)), content) == ([], [], None)


def test_invalid_side_items_are_not_coerced():
    content = json.dumps(
        dict(
            derived_under_policy="SPK-001",
            learning=[dict(kind="rule", text=True, failure_or_gain="x")],
            requested_lifts=[dict(id=True, reason="x")],
        )
    )
    lifts, learning, _ = ingress(next(iter(BY_ID)), content)
    assert lifts == learning == []


@pytest.mark.parametrize("pilot", list(BY_ID))
def test_original_seed_preserved(pilot):
    prompt = build_prompt(pilot, 1)
    assert prompt["original_seed"] == BY_ID[pilot]["text"]
    assert json.loads(prompt["user_prompt"])["original_seed"] == prompt["original_seed"]
    assert "summary" in prompt["response_schema"]["required"]
    assert "process_integrity" in prompt["response_schema"]["required"]


def test_prior_failed_run_consumes_budget():
    with pytest.raises(ValueError, match="LOOP_LIMIT"):
        limits_for("pilot_0000199")
