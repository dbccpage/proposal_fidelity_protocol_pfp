"""Live demo 3 records proposer bytes and does not certificate unparsed text."""

from __future__ import annotations

import json
import sys
import urllib.request

import pytest

from omega_engine_pfp.domain.demos import DemoRefusal
from omega_engine_pfp.infrastructure.adapters.mssn_scenarios.protocol import (
    FIXTURES,
    run_live_arm,
)
from omega_engine_pfp.infrastructure.demos.execution import run

SENTINEL = "sk-or-demo3-live-sentinel-not-a-real-key"
STUB_TEXT = "LIVE_PROVIDER_BYTES_not_a_move_batch"
MODEL = "openai/gpt-4o-mini"


def _payload() -> bytes:
    body = {
        "id": "chatcmpl_demo3_stub",
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


def test_unparsed_proposer_text_does_not_certificate():
    """Garbage proposer text stops the arm before the host applies a witness."""
    seen: list[str] = []

    def propose(prompt: str) -> str:
        seen.append(prompt)
        return "this is not a move batch"

    row = run_live_arm("gauge_even_triangle", "P", propose, max_turns=2)
    witness = json.dumps(FIXTURES["gauge_even_triangle"]["valid_witness"])
    assert len(seen) == 1
    assert witness not in seen[0]
    assert row["final_exit"] is None
    assert row["final_exit"] != "SCOPED_CERTIFICATE"
    assert row["step_count"] == 0
    assert row["provider_calls"] == 1
    assert row["turns"][0]["host_decision"] == "UNPARSED_MODEL_MOVES"
    assert row["turns"][0]["parsed_moves"] == 0


def test_non_protocol_live_stays_refused(tmp_path):
    """Exact checkers stay offline. Live transport is refused before any output directory."""
    target = tmp_path / "sign-gauge-live"
    with pytest.raises(DemoRefusal) as caught:
        run("demo_2", target, live=True, model=MODEL)
    assert caught.value.code == "LIVE_SCENARIO_NOT_SUPPORTED"
    assert not target.exists()


def test_offline_demo_3_stays_scripted(tmp_path):
    """The catalog path without --live still runs the scripted host matrix."""
    receipt = run("demo_3", tmp_path / "scripted")
    result = receipt["result"]
    assert result["status"] == "CHECKED"
    assert receipt["transport"] == "fixture"
    assert "scripted" in result["scope"]
    assert "provider_response" not in result
    assert result["matrix"]["schema"] == "symbol-game-demo3-experiment/matrix-receipt-v1"


def test_live_demo_3_records_provider_bytes(tmp_path, monkeypatch):
    """An unsettled/unbound reply stays recorded and stops before later arms."""
    _require_windows()
    monkeypatch.setenv("OPENROUTER_API_KEY", SENTINEL)
    monkeypatch.setattr("omega_engine_pfp.infrastructure.estimated_gateway.snapshot_pricing",
        lambda *a, **k: {"catalog_sha256": "fixture", "row": {"id": MODEL,
            "pricing": {"prompt": "0.000000001", "completion": "0.000000001"}}})
    calls = {"n": 0}

    def urlopen(_request, timeout=0):
        calls["n"] += 1
        assert timeout is not None
        return _Body(_payload())

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    output = tmp_path / "demo3-live"
    receipt = run("demo_3", output, live=True, model=MODEL, max_output_tokens=256,
        max_provider_calls=1, max_estimated_cost_microusd=4000)
    raw = (output / "receipt.json").read_bytes()
    assert SENTINEL.encode("utf-8") not in raw
    result = receipt["result"]
    assert calls["n"] == 1
    assert result["status"] == "TYPED_REFUSAL"
    assert result["scenario_id"] == "demo_3"
    assert result["provider"] == "openrouter"
    assert result["model"] == MODEL
    assert STUB_TEXT in result["provider_response"]
    assert "matrix" not in result
    assert result["pfp"]["checked_turns"] == 0
    assert result["pfp"]["total_reported_cost_usd"] is None
