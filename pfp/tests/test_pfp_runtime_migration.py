"""Reexecute saved replies with separately checked native identities; no provider dispatch."""

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from pfp.infrastructure import challenge_live as live
from adversary.tests.pilots.challenge_suite.catalog import ROOT

EVIDENCE = ROOT / "adversary/tests/pilots/evidence/demo004_pfp_learning/live"


@pytest.mark.parametrize(
    "name",
    [
        pytest.param(
            "c021_dev_baseline_v3",
            marks=pytest.mark.skipif(
                not os.environ.get("CORE_SYMBOL_GAME_HOST"),
                reason="Explicit native host binary required",
            ),
        ),
        "c039_dev_typed_witness_v3",
        "c050_dev_typed_witness_v3",
        "c055_dev_typed_witness_v5",
    ],
)
def test_saved_spk_proposals_in_new_synthetic_bound_turns(name, tmp_path, monkeypatch):
    """Old completion text is fixture input; new PFP wires are not old live replay."""
    from pfp.tests.test_challenge_accounted_boundary import fixture_gateway

    original = EVIDENCE / name
    config = json.loads((original / "config.json").read_bytes())
    stages = sorted(original.glob("stage_*"))
    retained = {p: p.read_bytes() for p in [original / "config.json"] + [
        stage / leaf for stage in stages for leaf in ("request.json", "provider_response.json", "receipt.json")]}
    proposals = [json.loads(json.loads((stage / "provider_response.json").read_bytes())[
        "choices"][0]["message"]["content"]) for stage in stages]
    gateway, provider = fixture_gateway(tmp_path, proposals)
    output = tmp_path / "new_synthetic_bound_run"
    records = live.live_run(config["row"], output, "vendor/model", config["arm"],
        gateway=gateway, max_output_tokens=256, max_provider_calls=4)
    assert len(records) == len(provider.calls)
    for number, receipt in enumerate(records, 1):
        actual = live.isolated(dict(kind="LLM", row=config["row"],
            raw_reply=json.dumps(proposals[number - 1])), timeout=30)
        assert receipt["result"] == actual
        assert receipt["model"] == "vendor/model"
        assert receipt["cost_microusd"] == 1  # Explicit synthetic accounting, never the old bill.
        stage = output / f"stage_{number}"
        assert (stage / "request.json").read_bytes() != (stages[number - 1] / "request.json").read_bytes()
    assert live.replay_live(output) == len(provider.calls)
    assert len(provider.calls) == len(records)
    recorded = json.loads((output / "config.json").read_bytes())
    assert recorded["schema"] == live.SCHEMA and "authorization" not in recorded
    for relative in live.RUNTIME_SOURCES:
        assert (output / "source_snapshot" / relative).read_bytes() == (ROOT / relative).read_bytes()
    assert all(path.read_bytes() == raw for path, raw in retained.items())


def test_older_record_requires_its_captured_runtime():
    # This earlier run used a different rendered contract. Preserve its sources;
    # replaying it directly through today's runtime must refuse source drift.
    with pytest.raises(ValueError, match="RUNTIME_SOURCE_DRIFT"):
        live.replay_live(EVIDENCE / "c011_development_typed_v2")


def test_missing_runtime_source_refuses_before_replay(tmp_path, monkeypatch):
    source_root = tmp_path / "source_root"
    source_root.mkdir()
    output = tmp_path / "run"
    output.mkdir()
    (output / "config.json").write_text(
        json.dumps({"sources": {"retired_owner/checker.py": "0" * 64}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(live, "ROOT", source_root)
    monkeypatch.setattr(
        live, "replay_stages", lambda *args, **kwargs: pytest.fail("Replay must not run")
    )
    with pytest.raises(ValueError, match="^RUNTIME_SOURCE_DRIFT$"):
        live.replay_live(output)


@pytest.mark.parametrize("changed", ["task", "template", "case"])
def test_consumed_prompt_inputs_are_captured_and_drift_refuses_before_replay(
    tmp_path, monkeypatch, changed
):
    from adversary.tests.pilots.challenge_suite import catalog

    root = tmp_path / "sources"
    challenge = root / "c005_fixture"
    challenge.mkdir(parents=True)
    paths = {
        "task": challenge / "TASK.md",
        "template": root / "template.yaml",
        "case": challenge / "cases.json",
    }
    for key, path in paths.items():
        path.write_text(key, encoding="utf-8")
    row = dict(challenge="C005", challenge_path="c005_fixture", source="c005_fixture/cases.json")
    monkeypatch.setattr(catalog, "ROOT", root)
    monkeypatch.setattr(catalog, "TEMPLATE", paths["template"])
    monkeypatch.setattr(live, "ROOT", root)
    monkeypatch.setattr(live, "RUNTIME_SOURCES", ())
    monkeypatch.setattr(live, "source_bindings", lambda challenge: {})
    from pfp.tests.test_pilot_matrix_pfp import make_gateway
    from adversary.domain.providers.types import CandidateRequest

    gateway, provider = make_gateway(tmp_path, model="fixture", max_output_tokens=256)
    def prepared(row, arm, feedback, config, stage):
        request = CandidateRequest("unit custody fixture", "no provider dispatch")
        turn = SimpleNamespace(binding={"task_id": "fixture", "attempt_id": f"fixture:{stage}"})
        return request, request, turn, {}
    monkeypatch.setattr(live, "_prepared", prepared)
    monkeypatch.setattr(live, "complete_pilot_turn", lambda *a, **k: dict(
        ok=False, stop=True, content=None, usage={}, pfp=None, provider_wire=None,
        attempt_state=None, error="UNIT_NO_DISPATCH", request={}))
    output = tmp_path / "run"
    records = live.live_run(row, output, "fixture", "baseline", gateway=gateway,
        max_output_tokens=256, max_provider_calls=4)
    assert len(records) == 1 and not provider.calls
    config = json.loads((output / "config.json").read_bytes())
    assert set(config["sources"]) == {p.relative_to(root).as_posix() for p in paths.values()}
    for path in paths.values():
        name = path.relative_to(root).as_posix()
        assert (output / "source_snapshot" / name).read_bytes() == path.read_bytes()
    assert live.replay_live(output) == 1  # Current no-dispatch observation remains source-bound.
    paths[changed].write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="^RUNTIME_SOURCE_DRIFT$"):
        live.replay_live(output)
    assert not provider.calls


def test_c005_saved_request_judgments_and_stops_replay_at_recorded_revision(tmp_path):
    from adversary.tests.pilots.challenge_suite.replay_snapshots import replay

    evidence = EVIDENCE.parent
    record = json.loads((evidence / "frozen_replay_v4.json").read_bytes())
    original = EVIDENCE / "c005_dev_typed_witness_v5"
    before = {p.relative_to(original): p.read_bytes() for p in original.rglob("*") if p.is_file()}
    supplied = os.environ.get("PFP_HISTORICAL_REPLAY_CHECKOUT")
    checkout = Path(supplied).resolve() if supplied else tmp_path / "historical_checkout"
    if not supplied:
        subprocess.run(
            ["git", "-C", str(ROOT), "worktree", "add", "--detach", str(checkout), record["head"]],
            check=True,
            capture_output=True,
        )
    try:
        head = subprocess.check_output(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
        ).strip()
        assert head == record["head"]
        result = replay(checkout, evidence, tmp_path / "replay.json", (original.name,))
        assert result["status"] == "PASS", result["runs"]
        assert result["provider_calls"] == 0
        assert len(result["runs"]) == 1
        actual = result["runs"][0]
        recorded = next(row for row in record["runs"] if row["run"] == original.name)
        assert actual["config_sha256"] == recorded["config_sha256"]
        assert json.loads(actual["stdout"])["replayed_stages"] == 2
        assert (
            subprocess.check_output(
                ["git", "-C", str(checkout), "status", "--porcelain"], text=True
            )
            == ""
        )
        assert {
            p.relative_to(original): p.read_bytes() for p in original.rglob("*") if p.is_file()
        } == before
    finally:
        if not supplied:
            # Only remove the new task-owned worktree; a dirty tree is retained by Git.
            assert checkout.resolve().is_relative_to(tmp_path.resolve())
            subprocess.run(
                ["git", "-C", str(ROOT), "worktree", "remove", str(checkout)], check=True
            )
