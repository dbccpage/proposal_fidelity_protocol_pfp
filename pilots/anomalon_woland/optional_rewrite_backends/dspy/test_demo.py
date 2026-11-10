"""Focused optional DSPy seam controls; all replies are labeled offline fixtures."""

import base64
import importlib
import json
import socket

import pytest

from omega_engine_pfp.infrastructure.task_turn import PfpTurnRefusal

dspy = pytest.importorskip("dspy", reason="Optional DSPy is absent from the default environment")
demo = importlib.import_module(
    "omega_engine_woland.tests.pilots.optional_rewrite_backends.dspy.demo"
)
FixturePfpLM = demo.FixturePfpLM
RewriteSeed = demo.RewriteSeed
StrictPfpAdapter = demo.StrictPfpAdapter
preserving_fixture = demo.preserving_fixture
run_demo = demo.run_demo


def predict(lm, seed="Preserve the signed graph Ω and exact coefficients.", **kwargs):
    with dspy.context(lm=lm, adapter=StrictPfpAdapter(), disable_history=True):
        return dspy.Predict(RewriteSeed)(seed=seed, **kwargs)


def modified_fixture(change):
    def fixture(turn):
        reply = json.loads(preserving_fixture(turn))
        change(reply)
        return json.dumps(reply).encode()
    return fixture


def test_typed_predict_uses_actual_pfp_envelope_and_no_socket(monkeypatch):
    def forbid(*_args, **_kwargs):
        pytest.fail("Offline DSPy fixture attempted network communication")
    monkeypatch.setattr(socket.socket, "connect", forbid)
    result = run_demo("Ω\nKeep \"quotes\" and emoji 🧪 exactly.")
    assert result["status"] == "FIXTURE_VERIFIED"
    assert result["source_mode"] == "OFFLINE_FIXTURE"
    assert result["outgoing_provider_calls"] == 0
    assert result["fixture_attempts"] == 1
    assert result["preserved_seed"] == "Ω\nKeep \"quotes\" and emoji 🧪 exactly."


def test_raw_envelope_and_independent_judge_are_replayable_without_send():
    lm = FixturePfpLM()
    predict(lm)
    record = lm.records[-1]
    checked = record["checked"]
    assert checked["schema_valid"] is True
    assert checked["status"] == "HOST_ACCEPTED"
    assert base64.b64decode(checked["raw_reply_base64"]) == record["raw"]
    replayed = record["turn"].replay(
        checked, judges=(("exact-seed-and-template-v002", demo.protected_seed_judge),), require_checker=True
    )
    assert replayed["raw_reply_sha256"] == checked["raw_reply_sha256"]
    assert lm.calls == 1


@pytest.mark.parametrize("malformation", [b"{answer:'repair me'}", b'{}\ntrailing', b'{"answer":NaN}', b"\xff"])
def test_dspy_never_repairs_malformed_raw_json(malformation):
    lm = FixturePfpLM(lambda _turn: malformation)
    with pytest.raises(PfpTurnRefusal):
        predict(lm)
    assert lm.calls == 1
    assert lm.records[-1]["raw"] == malformation


def test_coherently_bound_changed_seed_fails_the_independent_judge():
    lm = FixturePfpLM(modified_fixture(lambda reply: reply["answer"].update(preserved_seed="Different task")))
    with pytest.raises(PfpTurnRefusal) as exc:
        predict(lm)
    assert exc.value.checked["schema_valid"] is True
    assert exc.value.checked["failure_class"] == "CERTIFICATE"
    assert lm.calls == 1


def test_extra_output_field_is_not_silently_removed():
    lm = FixturePfpLM(modified_fixture(lambda reply: reply["answer"].update(unregistered=True)))
    with pytest.raises(PfpTurnRefusal):
        predict(lm)
    assert lm.calls == 1


def test_typed_output_has_no_coercion_fallback():
    lm = FixturePfpLM(modified_fixture(lambda reply: reply["answer"].update(template_id=42)))
    with pytest.raises(PfpTurnRefusal):
        predict(lm)
    assert lm.calls == 1


def test_unregistered_template_selector_is_refused_without_host_resolution():
    lm = FixturePfpLM(modified_fixture(lambda reply: reply["answer"].update(template_id="ignore-all-constraints")))
    with pytest.raises(PfpTurnRefusal) as exc:
        predict(lm)
    assert exc.value.checked["schema_valid"] is False
    assert lm.calls == 1


def test_wrong_attempt_binding_has_no_retry():
    lm = FixturePfpLM(modified_fixture(lambda reply: reply.update(attempt_id="invented:0")))
    with pytest.raises(PfpTurnRefusal):
        predict(lm)
    assert lm.calls == 1


def test_lm_rejects_unprepared_default_adapter_calls_before_fixture_dispatch():
    lm = FixturePfpLM()
    with pytest.raises(ValueError, match="PREPARED_PFP_TURN_REQUIRED"):
        lm(messages=[{"role": "user", "content": "Bypass PFP"}])
    assert lm.calls == 0


def test_multiple_generations_or_retries_are_refused_before_fixture_dispatch():
    lm = FixturePfpLM()
    with pytest.raises(ValueError, match="SINGLE_UNMODIFIED_SIGNATURE_REQUIRED"):
        predict(lm, config={"n": 2, "num_retries": 1})
    assert lm.calls == 0


def test_optional_demo_rejects_few_shot_examples_before_fixture_dispatch():
    lm = FixturePfpLM()
    with pytest.raises(ValueError, match="SINGLE_UNMODIFIED_SIGNATURE_REQUIRED"):
        predict(lm, demos=[{"seed": "output leakage", "preserved_seed": "precomputed"}])
    assert lm.calls == 0
