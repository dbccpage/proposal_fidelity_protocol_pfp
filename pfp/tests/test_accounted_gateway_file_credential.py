"""The accounted OpenRouter factory does not treat a checkout file as ambient authority.

AuthorityEffect: None.
"""

from __future__ import annotations

import os

import pytest

from omega_engine_pfp.domain.demos import DemoRefusal
from omega_engine_pfp.infrastructure.demos.execution import Proposals, _annotate_live_result, _scrub
from omega_engine_pfp.infrastructure.estimated_gateway import create_accounted_openrouter_gateway
from omega_engine_woland.domain.providers.types import ProviderConfigError
from omega_engine_woland.infrastructure.providers import credential_source


class _FakeTransport:
    def __init__(self) -> None:
        self.seen = None

    def observe_key(self, value: str) -> None:
        self.seen = value


def _env(path, secret: str) -> None:
    path.write_text(f"OPENROUTER_API_KEY={secret}\n", encoding="utf-8")


def _factory(tmp_path, monkeypatch, *, explicit=None, discovery="off"):
    checkout = tmp_path / "checkout.env"
    _env(checkout, "checkout-secret")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OMEGA_CREDENTIAL_DISCOVERY", discovery)
    monkeypatch.setattr(
        credential_source,
        "env_file_candidates",
        lambda start=None: [("env_file:checkout", checkout)],
    )
    fake = _FakeTransport()
    gateway = create_accounted_openrouter_gateway(
        "vendor/model",
        16,
        env_file=explicit,
        allow_unbounded_cost=True,
        transport=fake,
    )
    return fake, gateway


def test_discovery_off_ignores_checkout_env(tmp_path, monkeypatch):
    with pytest.raises(ProviderConfigError, match="OPENROUTER_KEY_MISSING"):
        _factory(tmp_path, monkeypatch)
    assert os.environ.get("OPENROUTER_API_KEY") is None


def test_explicit_file_wins_and_disclosure_is_redacted(tmp_path, monkeypatch):
    explicit = tmp_path / "selected.env"
    _env(explicit, "explicit-secret")
    fake, gateway = _factory(tmp_path, monkeypatch, explicit=explicit, discovery="on")
    assert fake.seen == "explicit-secret"
    assert gateway.credential_disclosure == "[REDACTED]"
    stored = {key: value for key, value in vars(gateway).items() if key != "transport"}
    assert "explicit-secret" not in repr(stored)
    assert "checkout-secret" not in repr(stored)
    assert os.environ.get("OPENROUTER_API_KEY") is None


def test_file_secret_is_scrubbed_without_entering_the_process_environment(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert _scrub("saw explicit-secret here", "explicit-secret") == "saw [REDACTED] here"
    annotated = _annotate_live_result(
        {"status": "FAILED", "code": "NO", "detail": "explicit-secret leaked"},
        scenario_id="s",
        model="m",
        transcript=[{"response": "explicit-secret"}],
        secrets=("explicit-secret",),
    )
    assert annotated["detail"] == "[REDACTED] leaked"
    assert annotated["provider_response"] == "[REDACTED]"
    assert os.environ.get("OPENROUTER_API_KEY") is None


def test_live_transcript_redacts_a_file_sourced_key_in_the_error(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    secret = "file-sourced-key-not-in-environ"

    def fake_turn(gateway, request, **kwargs):
        return {
            "ok": False,
            "content": f"body {secret}",
            "error": f"provider said {secret}",
            "stop": True,
            "provider_wire": None,
            "attempt_state": "Failed",
            "usage": {},
            "pfp": None,
        }

    monkeypatch.setattr(
        "omega_engine_pfp.infrastructure.pilot_matrix.complete_pilot_turn",
        fake_turn,
    )

    class Gateway:
        def action(self, attempt_id):
            raise KeyError(attempt_id)

    proposals = Proposals(
        Gateway(),
        live=True,
        model="m",
        max_output_tokens=8,
        max_provider_calls=1,
        secrets=(secret,),
    )
    with pytest.raises(DemoRefusal):
        proposals.propose("prompt", "")
    stored = proposals.transcript[0]
    assert stored["response"] == "body [REDACTED]"
    assert stored["error"] == "provider said [REDACTED]"
    assert secret not in str(proposals.transcript)
    assert os.environ.get("OPENROUTER_API_KEY") is None
