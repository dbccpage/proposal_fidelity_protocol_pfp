"""Live demo receipts bind the provider body and do not store a refusal as success."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from types import SimpleNamespace
from urllib.error import URLError

import pytest

import omega_engine_pfp.entrypoints.cli.demo_commands as demo_commands
from omega_engine_pfp.infrastructure.demos.execution import run
from omega_engine_woland.infrastructure.providers.credential_source import resolve_credential

SENTINEL = "sk-or-live-receipt-sentinel-not-a-real-key"
STUB_TEXT = "LIVE_PROVIDER_BYTES_not_the_fixture_reply"
FIXTURE_REPLY = '{"candidate":"op<<0>>"}'
MODEL = "openai/gpt-4o-mini"
LIVE_BOUNDS = dict(max_output_tokens=256, max_provider_calls=1,
    max_estimated_cost_microusd=4000, max_cost_microusd=None)


@pytest.fixture(autouse=True)
def local_pricing(monkeypatch):
    monkeypatch.setattr("omega_engine_pfp.infrastructure.estimated_gateway.snapshot_pricing",
        lambda *a, **k: {"catalog_sha256": "fixture", "row": {"id": MODEL,
            "pricing": {"prompt": "0.000000001", "completion": "0.000000001"}}})


def _payload() -> bytes:
    body = {
        "id": "chatcmpl_live_stub",
        "object": "chat.completion",
        "model": MODEL,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": STUB_TEXT},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 11, "completion_tokens": 4, "total_tokens": 15},
    }
    return json.dumps(body).encode("utf-8")


class _Body:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            chunk = self._data
            self._data = b""
            return chunk
        chunk = self._data[:size]
        self._data = self._data[size:]
        return chunk

    def __enter__(self) -> _Body:
        return self

    def __exit__(self, *_args: object) -> bool:
        return False


def _require_windows() -> None:
    if sys.platform != "win32":
        pytest.skip("existing live artifact protector requires Windows DPAPI")


def _assert_key_absent(output) -> None:
    raw = (output / "receipt.json").read_bytes()
    assert SENTINEL.encode("utf-8") not in raw


def test_live_openrouter_receipt_is_not_satisfied_by_the_fixture(tmp_path, monkeypatch):
    """A live run keeps the stub body when the socket is used, and refuses when it is not."""
    _require_windows()
    monkeypatch.setenv("OPENROUTER_API_KEY", SENTINEL)
    calls = {"n": 0}

    def urlopen(_request, timeout=0):
        calls["n"] += 1
        assert timeout is not None
        return _Body(_payload())

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    output = tmp_path / "live-stub"
    receipt = run("demo_eis_failure_classes", output, live=True, model=MODEL, **LIVE_BOUNDS)
    _assert_key_absent(output)
    result = receipt["result"]
    assert calls["n"] > 0
    assert result["scenario_id"] == "demo_eis_failure_classes"
    assert result["provider"] == "openrouter"
    assert result["model"] == MODEL
    assert STUB_TEXT in result["provider_response"]
    assert FIXTURE_REPLY not in result["provider_response"]
    assert result["status"] in {"CHECKED", "TYPED_REFUSAL"}
    assert "success" not in result["status"].lower()


def test_transport_refusal_is_not_stored_as_execution_success(tmp_path, monkeypatch):
    """A socket error, or a refusal before the socket, is a typed refusal with a receipt."""
    _require_windows()
    monkeypatch.setenv("OPENROUTER_API_KEY", SENTINEL)
    calls = {"n": 0}

    def urlopen(_request, timeout=0):
        calls["n"] += 1
        assert timeout is not None
        raise URLError("simulated transport refusal")

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    output = tmp_path / "live-refuse"
    receipt = run("demo_eis_failure_classes", output, live=True, model=MODEL, **LIVE_BOUNDS)
    _assert_key_absent(output)
    result = receipt["result"]
    assert calls["n"] > 0
    assert result["status"] == "TYPED_REFUSAL"
    assert result["status"] != "CHECKED"
    assert "OUTCOME_UNKNOWN" in result["code"]
    assert result["provider"] == "openrouter"
    assert result["model"] == MODEL
    assert result["scenario_id"] == "demo_eis_failure_classes"
    assert "success" not in result["status"].lower()


AMBIENT = "sk-or-ambient-sentinel-not-a-real-key"


def _forbid_socket(monkeypatch) -> None:
    def urlopen(_request, timeout=0):
        raise AssertionError("live transport must not open a socket")

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)


@pytest.mark.parametrize(
    "body",
    [
        "OPENROUTER_API_KEY=\n",
        'OPENROUTER_API_KEY=""\n',
        "OPENROUTER_API_KEY=''\n",
        "CHEAP_OPENROUTER_MODEL=openai/gpt-4o-mini\n",
    ],
)
def test_empty_or_omitted_explicit_file_preserves_ambient_key(tmp_path, monkeypatch, body):
    """Canonical resolution falls back to ambient input without changing it."""
    dotenv = tmp_path / "dotenv"
    dotenv.write_text(body, encoding="utf-8")
    monkeypatch.setenv("OPENROUTER_API_KEY", AMBIENT)
    _forbid_socket(monkeypatch)
    resolved = resolve_credential(("OPENROUTER_API_KEY",), explicit_file=dotenv)
    assert resolved.is_ok
    assert resolved.unwrap().value == AMBIENT
    assert resolved.unwrap().source == "environment"
    assert os.environ.get("OPENROUTER_API_KEY") == AMBIENT


def test_unset_key_run_writes_provider_config_refusal(tmp_path, monkeypatch):
    """execution.run records ProviderConfigError when the live key is unset."""
    _require_windows()
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    _forbid_socket(monkeypatch)
    output = tmp_path / "unset-run"
    receipt = run("demo_eis_failure_classes", output, live=True, model=MODEL, **LIVE_BOUNDS)
    result = receipt["result"]
    assert result["status"] == "TYPED_REFUSAL"
    assert result["code"] == "ProviderConfigError"
    assert (output / "receipt.json").is_file()


def test_unset_key_cmd_run_exits_nonzero(tmp_path, monkeypatch):
    """cmd_run writes the same refusal and does not return process success."""
    _require_windows()
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    _forbid_socket(monkeypatch)
    output = tmp_path / "unset-cmd"
    code = demo_commands.cmd_run(
        SimpleNamespace(
            scenario_id="demo_eis_failure_classes",
            output_dir=output,
            live=True,
            model=MODEL,
            env_file=None,
            **LIVE_BOUNDS,
        )
    )
    assert code == 1
    raw = (output / "receipt.json").read_bytes()
    assert AMBIENT.encode("utf-8") not in raw
    result = json.loads(raw)["result"]
    assert result["status"] == "TYPED_REFUSAL"
    assert result["code"] == "ProviderConfigError"
