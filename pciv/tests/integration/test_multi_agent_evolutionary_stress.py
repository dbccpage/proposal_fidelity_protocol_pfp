"""Actual fixture-bout feedback and exact retained-checker replay. AuthorityEffect: None."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pciv.infrastructure.cas import ContentAddressedStorageV1
from pciv.scripts.run_evolutionary_stress_50gen import (
    CORE,
    replay_observation,
    run_stress_test,
)


def test_multi_agent_evolutionary_stress_50_generations(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CORE_INTELLIGENCE_ROOT", str(tmp_path))
    output = tmp_path / "stress"
    summary = run_stress_test(50, output, seed=17)
    assert summary["total_bouts_executed"] == 150
    assert summary["total_generations"] == 50
    assert summary["openrouter_live_calls"] == 0
    assert summary["openrouter_cost_usd"] == "0.00"
    assert summary["efficacy"] == "NOT_MEASURED"
    assert summary["checked_candidates"] > 0
    assert summary["rejected_candidates"] > 0
    assert 0 < summary["learning_updates"] <= 150
    cas = ContentAddressedStorageV1(output / "cas")
    previous = {}
    for row in summary["rounds"]:
        parent = cas.retrieve(row["parent_genome_sha256"])
        child = cas.retrieve(row["child_genome_sha256"])
        assert parent.startswith(CORE) and child.startswith(CORE)
        if row["agent"] in previous:
            assert row["parent_genome_sha256"] == previous[row["agent"]]
        previous[row["agent"]] = row["child_genome_sha256"]
        if row["new_hints"]:
            assert "REJECTED" in row["checker_verdicts"]
            assert row["child_genome_sha256"] != row["parent_genome_sha256"]
        else:
            assert row["child_genome_sha256"] == row["parent_genome_sha256"]
    receipts = list((output / "_adversary").rglob("receipt.json"))
    assert len(receipts) == 150
    for receipt_path in receipts:
        receipt = json.loads(receipt_path.read_bytes())
        assert receipt["authority_effect"] == "None"
        assert receipt["status"] != "AUTHORIZED"


def test_fixture_replay_preserves_genome_feedback_and_rejects_changed_bytes(tmp_path, monkeypatch):
    monkeypatch.setenv("CORE_INTELLIGENCE_ROOT", str(tmp_path))
    first = run_stress_test(2, tmp_path / "first", seed=23)
    replay = run_stress_test(2, tmp_path / "replay", seed=23)
    assert first["replay_sha256"] == replay["replay_sha256"]
    assert first["observations"]
    for observation in first["observations"]:
        assert replay_observation(observation)
        assert observation["parent_genome_sha256"] in observation["objective"]
    changed = {**first["observations"][0], "candidate_hex": b"{}".hex()}
    assert not replay_observation(changed)


@pytest.mark.parametrize("generations", [0, -1, 51, True])
def test_invalid_generation_limit_refuses_without_writing(tmp_path, generations):
    output = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="generations"):
        run_stress_test(generations, output)
    assert not output.exists()
