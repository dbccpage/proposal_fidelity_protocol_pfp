"""Zero-effect refusal of the disconnected legacy live harness. AuthorityEffect: None."""

from __future__ import annotations

from pathlib import Path

import pytest

from pciv.scripts.run_evolutionary_stress_live import (
    run_live_evolutionary_stress_test,
)


def test_legacy_live_entry_refuses_before_output_or_provider(tmp_path: Path):
    output = tmp_path / "no-live-effects"
    with pytest.raises(RuntimeError, match="LEGACY_LIVE_RUNNER_RETIRED"):
        run_live_evolutionary_stress_test(output_dir=output)
    assert not output.exists()


def test_live_multi_agent_evolutionary_stress_within_cost_and_token_caps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "must-not-be-read")
    output_dir = tmp_path / "live_stress_results"

    # The old explicit live options cannot reactivate the retired path.
    with pytest.raises(RuntimeError, match="LEGACY_LIVE_RUNNER_RETIRED"):
        run_live_evolutionary_stress_test(
            num_generations=2,
            output_dir=output_dir,
            cost_cap_microusd=50_000,
            max_tokens_per_call=64,
            model_name="openai/gpt-4o-mini",
        )

    assert not output_dir.exists()
