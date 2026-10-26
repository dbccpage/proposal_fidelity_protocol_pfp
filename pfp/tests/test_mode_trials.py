"""Local mode trials for pilots 0000001 through 0000025.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
import yaml

from omega_engine_pfp.domain.types import PilotSpec, SeedPrompt
from omega_engine_pfp.infrastructure.model_loading import load_yaml_model
from omega_engine_woland.tests.pilots.replay_runners._paths import pilots_root, repository_root
from omega_engine_woland.tests.pilots.replay_runners.mode_capsules.execute import (
    build_trials,
    digests_match,
    write_trials,
)
from omega_engine_woland.tests.pilots.replay_runners.mode_capsules.live_dispatch import (
    PAID_MODEL,
    host_answer_matches,
    models_for,
    public_messages,
    session_cap_microusd,
)

PILOTS = pilots_root(Path(__file__))


def _retired_tripwire(*args, **kwargs):
    pytest.fail("retired live entrypoint touched filesystem, credentials, pricing or transport")


class _RetiredRootTripwire:
    __truediv__ = _retired_tripwire


@pytest.mark.parametrize("entrypoint", ["retarget_specs", "dispatch_pilots", "main"])
def test_retired_mode_live_entrypoints_refuse_before_side_effects(monkeypatch, entrypoint):
    from omega_engine_woland.tests.pilots.replay_runners.mode_capsules import live_dispatch

    for name in ("resolve_credential", "fetch_paid_pricing", "openrouter_transport", "_write"):
        monkeypatch.setattr(live_dispatch, name, _retired_tripwire, raising=False)
    monkeypatch.setattr(live_dispatch, "PILOTS", _RetiredRootTripwire())
    call = getattr(live_dispatch, entrypoint)
    expected_error = SystemExit if entrypoint == "main" else RuntimeError
    with pytest.raises(expected_error, match="RETIRED_MODE_CAMPAIGN"):
        call() if entrypoint == "main" else call(_RetiredRootTripwire())


def test_retired_dossier_live_callable_refuses_before_side_effects(monkeypatch):
    from omega_engine_woland.tests.pilots.replay_runners.dossier_capsules import run

    for name in ("environment", "pricing", "openrouter_transport", "write_once", "SqliteBudgetLedger"):
        monkeypatch.setattr(run, name, _retired_tripwire, raising=False)
    monkeypatch.setattr(run, "PILOTS", _RetiredRootTripwire())
    with pytest.raises(ValueError, match="RETIRED_DOSSIER_CAMPAIGN"):
        run.live({}, "fixture", 1, 1)


@pytest.mark.parametrize("session", ["primary", "free_followup"])
def test_retired_dossier_cli_live_refuses_before_historical_plan(monkeypatch, session):
    from omega_engine_woland.tests.pilots.replay_runners.dossier_capsules import run

    monkeypatch.setattr("sys.argv", ["dossier-capsules", "--live", "--session", session])
    for name in ("prepare", "historical_plan", "live", "replay"):
        monkeypatch.setattr(run, name, _retired_tripwire)
    with pytest.raises(SystemExit) as refusal:
        run.main()
    assert refusal.value.code == 2


def test_retired_mode_runner_source_snapshot_is_hash_bound():
    root = repository_root(Path(__file__))
    manifest_path = (
        root
        / "omega_engine_pfp/tests/pilot_0000001/misc/retired_mode_trials_runner_v1/manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "retained_exact_bytes_before_relocation"
    for row in manifest["files"]:
        assert hashlib.sha256((root / row["preserved_path"]).read_bytes()).hexdigest() == row["sha256"]


def test_every_trial_holds_its_claims_and_states_its_limit():
    trials = build_trials()
    assert [trial["pilot_index"] for trial in trials] == list(range(1, 26))
    assert trials[0]["mode_id"] == 2
    assert trials[1]["mode_id"] == 3
    assert trials[18]["mode_id"] == 20
    for trial in trials:
        assert trial["provider_calls"] == 0
        assert trial["target_spend_usd"] == 0.0
        assert digests_match(trial["packet"])
        assert trial["execution_limit"]
        assert trial["advantages"] and trial["disadvantages"]
        assert all(item["claim_held"] is True for item in trial["variations"])
        winning = [item for item in trial["variations"] if item["role"] == "winning"]
        if trial["winning_condition_executed"]:
            assert any(item["status"] == "ACCEPTED" for item in winning)
        else:
            assert any(item["role"] == "limit" for item in trial["variations"])
            assert not winning


def test_mode_limits_stay_inside_what_ran():
    by_index = {trial["pilot_index"]: trial for trial in build_trials()}
    mode_03 = by_index[2]
    assert mode_03["winning_condition_executed"] is False
    assert any(item["evidence"].get("logit_hook_called") is False for item in mode_03["variations"])
    mode_09 = by_index[8]
    assert mode_09["winning_condition_executed"] is False
    assert "lake build was not run" in mode_09["execution_limit"]
    mode_18 = by_index[17]
    assert mode_18["winning_condition_executed"] is False
    assert mode_18["answer"]["mub6_resolved"] is False
    mode_02 = by_index[1]
    lie = next(item for item in mode_02["variations"] if item["variation_id"] == "resealed_wrong_answer")
    assert lie["evidence"]["digest_only_status"] == "ACCEPTED"
    assert lie["evidence"]["oracle_status"] == "REJECTED"


def test_written_packets_match_a_fresh_run_and_do_not_touch_later_pilots(tmp_path, monkeypatch):
    from omega_engine_woland.tests.pilots.replay_runners.mode_capsules import execute

    copied_pilots = tmp_path / "pilots"
    shutil.copytree(PILOTS, copied_pilots)
    relocated = repository_root(PILOTS) / "omega_engine_pfp" / "tests"
    for index in range(6):
        name = f"pilot_{index:07d}"
        if not (copied_pilots / name).exists():
            shutil.copytree(relocated / name, copied_pilots / name)
    monkeypatch.setattr(execute, "PILOTS", copied_pilots)
    monkeypatch.setattr(f"{__name__}.PILOTS", copied_pilots)
    trials = build_trials()
    capsule_indexes = {1, 2, 3, 4}
    write_trials([trial for trial in trials if trial["pilot_index"] not in capsule_indexes])
    for trial in trials:
        folder = PILOTS / trial["pilot_id"]
        if trial["pilot_index"] in capsule_indexes:
            capsule = folder / "tests" / "test_00"
            packet_path = capsule / "packet.yaml"
            execution_path = capsule / "mode_trial_execution.yaml"
            plan_path = capsule / "testplan_mode_trial_v0.yaml"
        else:
            packet_path = folder / "packet.yaml"
            execution_path = folder / "results" / "execution.yaml"
            plan_path = folder / "testplan.yaml"
        packet_text = packet_path.read_text(encoding="utf-8")
        assert "&id" not in packet_text
        packet = yaml.safe_load(packet_text)
        assert digests_match(packet)
        execution = yaml.safe_load(execution_path.read_text(encoding="utf-8"))
        assert execution["provider_calls"] == 0
        assert [item["variation_id"] for item in execution["variations"]] == [
            item["variation_id"] for item in trial["variations"]
        ]
        seed = load_yaml_model(SeedPrompt, folder / "seed.yaml")
        assert seed.pilot_id == trial["pilot_id"]
        assert seed.task_family == trial["task_family"]
        spec = load_yaml_model(PilotSpec, folder / "spec.yaml")
        assert spec.pilot_id == trial["pilot_id"]
        raw = yaml.safe_load((folder / "spec.yaml").read_text(encoding="utf-8"))
        plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
        assert raw["test_plan"]["path"] == "testplan.yaml"
        assert plan["mode_id"] == trial["mode_id"]
        assert raw["coordinates"]["mode"] == trial["mode_coordinate"]
        assert f"{raw['coordinates']['target_spend_usd']:.4f}" == "0.0010"
        assert raw["models"] == models_for(raw["coordinates"]["model_id"])
        assert raw["models"][1] == PAID_MODEL
        if trial["pilot_index"] in capsule_indexes:
            assert raw["responses"]["directory"] == "misc"
            assert (folder / "tests" / "test_49").is_dir()
        else:
            assert raw["test_plan"]["mode_id"] == trial["mode_id"]
        assert "\r" not in (folder / "spec.yaml").read_text(encoding="utf-8")
    kept = yaml.safe_load((PILOTS / "pilot_0000022" / "spec.yaml").read_text(encoding="utf-8"))
    assert kept["coordinates"]["mode"] == "mode_01"
    assert kept["coordinates"]["representation_rewrite"] == "ebnf_wire_v1"
    staged = yaml.safe_load((PILOTS / "pilot_0000020" / "spec.yaml").read_text(encoding="utf-8"))
    assert staged["coordinates"]["stage_count"] == 2
    assert staged["coordinates"]["single_shot"] is False
    antibody = yaml.safe_load((PILOTS / "pilot_0000003" / "spec.yaml").read_text(encoding="utf-8"))
    assert antibody["coordinates"]["antibody_active"] is True
    assert antibody["coordinates"]["antibody_ids"] == ["ab_invented_edge"]
    assert not (PILOTS / "pilot_0000026" / "packet.yaml").exists()
    assert not (PILOTS / "pilot_0000000" / "packet.yaml").exists()
    write_trials()
    reread = (PILOTS / "pilot_0000001" / "spec.yaml").read_text(encoding="utf-8")
    readme = (PILOTS / "pilot_0000001" / "README.md").read_text(encoding="utf-8")
    assert reread.count("test_plan:") == 1
    assert reread.count("\nmodels:\n") == 1
    assert readme.count("## 3. Mode trial") == 1
    for pilot_index in range(5, 11):
        later_readme = (PILOTS / f"pilot_{pilot_index:07d}" / "README.md").read_text(encoding="utf-8")
        assert later_readme.count("## 4. Dimension probes") == 1
    untouched = (PILOTS / "pilot_0000000" / "spec.yaml").read_text(encoding="utf-8")
    assert "deepseek/deepseek-v4.1-flash" not in untouched


def test_live_model_list_and_budget_stay_narrow():
    assert models_for("meta-llama/llama-3.1-8b-instruct:free") == [
        "meta-llama/llama-3.1-8b-instruct:free",
        PAID_MODEL,
    ]
    try:
        models_for("openai/gpt-4o-mini")
    except ValueError:
        refused = True
    else:
        refused = False
    assert refused
    system, user = public_messages("Report the edge count.", {"edge_count": 4})
    assert "expected_outcome" not in system + user
    assert '{"edge_count":4}' not in user
    try:
        public_messages('{"expected_outcome": {"answer": 1}}', {"answer": 1})
    except ValueError as error:
        assert str(error) == "ANSWER_BEARING_PUBLIC_PROMPT"
    else:
        raise AssertionError("answer-bearing prompt was accepted")
    assert session_cap_microusd([200, 200]) == 1_000
    assert session_cap_microusd([200] * 25) == 10_000


def test_wrapped_json_matches_the_declared_oracle_and_a_partial_does_not():
    oracle = {
        "observed_tallies": {"C1": 0, "C2": 0, "C3": 0},
        "all_green": True,
        "raw_global_defect_I": 6,
        "visibility_gap_lambda": 6,
        "recovery_modulus_exists": False,
    }
    assert host_answer_matches({"answer": oracle}, oracle)
    assert host_answer_matches(3, 3)
    assert not host_answer_matches({"answer": {"raw_global_defect_I": 6}}, oracle)
    assert not host_answer_matches({"answer": 4}, 3)
