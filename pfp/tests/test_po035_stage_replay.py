"""Historical v1 recipe serialization, safe lifts and current pure replay."""

import json

from omega_engine_woland.tests.pilots.relational_spacetime import typed_signals as adaptive
from omega_engine_woland.tests.pilots.relational_spacetime import baseline as campaign
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import proposal_body
from omega_engine_woland.tests.pilots.relational_spacetime.finite_fixtures import fixture_payload
from omega_engine_pfp.infrastructure.adapters import pfp_derivation as adapter
from omega_engine_pfp.tests._po035_historical import historical_derivation
from omega_engine_pfp.use_cases.pfp_derivation_loops import run_derivation_loops


def test_real_host_stages_replay_with_provider_key_order(tmp_path, monkeypatch):
    pilot = "pilot_0000200"
    calls = []
    monkeypatch.setattr(
        campaign, "capsule", lambda pilot, loop, stage, **kwargs: tmp_path / "capsules" / str(loop) / stage
    )

    def send(model, request, maximum, timeout):
        prompt_id = json.loads(request.user)["prompt_id"]
        packet = fixture_payload(pilot, prompt_id)
        proposal_body(packet)["requested_lifts"] = [
            {"id": "EXACT_RATIONAL", "reason": "exact witness arithmetic"}
        ]
        calls.append(packet)
        return json.dumps(
            dict(
                id=f"fixture-{len(calls)}",
                model=model,
                usage=dict(prompt_tokens=20, completion_tokens=20, total_tokens=40, cost=0),
                choices=[dict(message=dict(content=json.dumps(packet)), finish_reason="stop")],
            )
        ).encode()

    monkeypatch.setattr(historical_derivation, "dispatch_deadline", send)
    port = historical_derivation.PfpDerivationAdapter(
        pilot=pilot,
        folder=tmp_path / "run",
        campaign="fixture",
        model="fixture",
        pricing_sha256="fixture",
        sources={},
        prompt_builder=adaptive.build_prompt,
        observer=adaptive.observe,
    )
    terminal = run_derivation_loops(port)
    assert terminal["completed_loops"] == 5
    assert "EXACT_RATIONAL" in terminal["context"]["granted_lifts"]
    monkeypatch.setattr(
        adapter,
        "dispatch_deadline",
        lambda *args: (_ for _ in ()).throw(AssertionError("offline used transport")),
    )
    assert (
        adapter.replay_run(
            tmp_path / "run", pilot, "fixture", adaptive.build_prompt, adaptive.observe, {}
        )["replayed_calls"]
        == 5
    )
    candidate = json.loads((tmp_path / "run/loop_01/candidate_learning.json").read_bytes())[0]
    assert candidate["admitted"] is False
    assert candidate["json_pointer"] == "/sections/0/rows/0/learning/0"
