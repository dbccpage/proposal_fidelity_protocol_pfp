"""Public prompt assembly binds current identity without mutating stage sources."""

import json
import subprocess
import sys
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator, ValidationError

from omega_engine_pfp.controllers.pfp_controller import PfpController
from omega_engine_pfp.domain.prompts.prompts import PromptPacket
from omega_engine_pfp.infrastructure.storage import PfpFileSystemStorageAdapter
from omega_engine_pfp.use_cases.assemble_prompt import AssemblePromptUseCase


def test_stage_one_schema_accepts_original_witness_only_for_bound_demo():
    packet = PfpController().assemble_prompt("demo_001", 1, {"seed": "Finite task"}).unwrap()
    witness = dict(
        derived_under_policy="SPK-001", demo_id="demo_001", stage=1,
        authority_effect="None", should_continue=True,
        admission_proposal=dict(status="admit", grammar="finite JSON",
            equality_test="exact bytes", coefficient_profile="declared by task",
            missing_declarations=[], reason="Syntactic proposal; host checking remains required"),
    )
    checker = Draft202012Validator(packet.response_schema)
    checker.validate(witness)
    for wrong_id in ("demo_000", "DEMO_ID_BOUND_BY_HOST"):
        with pytest.raises(ValidationError):
            checker.validate(dict(witness, demo_id=wrong_id))
    with pytest.raises(ValidationError):
        checker.validate({key: value for key, value in witness.items() if key != "admission_proposal"})


@pytest.mark.parametrize("stage", (1, 2, 3, 4, 6, 11))
def test_each_model_stage_binds_copy_and_preserves_all_other_contract_fields(stage):
    storage = PfpFileSystemStorageAdapter()
    source = storage.load_stage_file(stage)
    original = deepcopy(source.response_schema)
    template = storage.load_prompt_template("default_template")
    cached = SimpleNamespace(load_stage_file=lambda _: source, load_prompt_template=lambda _: template)
    use_case = AssemblePromptUseCase(cached)
    first = use_case.assemble("demo_alpha", stage, {"seed": "Task A"}).unwrap()
    second = use_case.assemble("demo_beta", stage, {"seed": "Task B"}).unwrap()
    expected = deepcopy(original)
    expected["properties"]["demo_id"]["const"] = "demo_alpha"
    assert first.response_schema == expected
    assert second.response_schema["properties"]["demo_id"]["const"] == "demo_beta"
    assert source.response_schema == original
    first.response_schema["required"].clear()
    assert second.response_schema["required"] == original["required"]
    assert source.response_schema == original


@pytest.mark.parametrize("stage", (0, 5, 7, 8, 9, 10))
def test_non_model_stage_does_not_load_or_bind_model_schema(stage):
    storage = PfpFileSystemStorageAdapter()
    template = storage.load_prompt_template("default_template")
    def reject_stage_load(_):
        pytest.fail("Stage 0 and the host-only stages must not load a model schema")
    use_case = AssemblePromptUseCase(SimpleNamespace(
        load_stage_file=reject_stage_load, load_prompt_template=lambda _: template,
    ))
    packet = use_case.assemble("demo_000", stage, {"seed": "Task"}).unwrap()
    assert packet.response_schema == {}


@pytest.mark.parametrize("json_output", (False, True))
def test_actual_assemble_cli_exposes_real_packet_and_hashes(tmp_path, json_output):
    seed = {"seed": "private assembly sentinel Ω"}
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(seed), encoding="utf-8")
    command = [sys.executable, "-B", "-m", "omega_engine_pfp.entrypoints.cli.pfp",
        "assemble", "--demo-id", "demo_001", "--stage", "1", "--seed-json", str(seed_path)]
    if json_output:
        command.append("--json")
    result = subprocess.run(command, capture_output=True, text=True,
        cwd=Path(__file__).resolve().parents[2], timeout=30)
    assert result.returncode == 0, result.stderr
    expected = PfpController().assemble_prompt("demo_001", 1, seed).unwrap()
    if json_output:
        packet = PromptPacket.model_validate_json(result.stdout)
        assert packet == expected
        assert packet.system_sha256 == sha256(packet.system.encode("utf-8")).hexdigest()
        assert packet.user_sha256 == sha256(packet.user.encode("utf-8")).hexdigest()
        assert packet.schema_sha256 == sha256(str(packet.response_schema).encode("utf-8")).hexdigest()
        assert seed["seed"] in packet.user
    else:
        assert "demo_001" in result.stdout and "stage 1" in result.stdout
        assert "private assembly sentinel" not in result.stdout
        assert expected.system_sha256 in result.stdout
        assert expected.user_sha256 in result.stdout
        assert expected.schema_sha256 in result.stdout
        assert "Envelope" not in result.stdout


def test_existing_invalid_stage_refusal_is_preserved():
    result = PfpController().assemble_prompt("demo_000", 12, {})
    assert result.is_err
    assert result.unwrap_err().code.value == "UNKNOWN_STAGE"
