"""Finite original consistency teaching task and synthetic accounted turns."""

import builtins
import importlib
import ast
import base64
import json
from pathlib import Path
import subprocess

import pytest

from pfp.infrastructure import consistency_teaching as recording
from pfp.tests.demo_004.a_mechanism.consistency_teaching import conditions, host, tasks
from pfp.tests.test_pilot_matrix_pfp import make_gateway


def test_teaching_scene_import_is_offline_and_has_no_retired_bench_dependencies(monkeypatch):
    original = builtins.__import__
    attempted = []

    def checked_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 0 and name.split(".")[0] in {"dotenv", "matplotlib", "conditions", "host", "tasks", "bench"}:
            attempted.append(name)
            raise AssertionError("unexpected optional/retired scene import: " + name)
        return original(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", checked_import)
    module = importlib.import_module(
        "education.documentation.004_oepfp.curriculum.scenes.naked_prompt_launder")
    assert callable(module.record_one) and callable(module.render_mp4)
    assert attempted == []


def test_recovered_original_definitions_and_conditions_are_unchanged():
    pin = "bc42aa0a7156fcdf2122f0c8c43a52268e9eac84"
    for name, current in (("tasks", tasks), ("conditions", conditions), ("host", host)):
        original = subprocess.check_output(["git", "show", f"{pin}:bench/head_to_head/{name}.py"])
        before = ast.parse(original)
        after = ast.parse(Path(current.__file__).read_bytes())
        definitions = (ast.FunctionDef, ast.ClassDef, ast.Assign)
        old = {node.name if isinstance(node, (ast.FunctionDef, ast.ClassDef)) else ast.dump(node.targets[0]):
            ast.dump(node) for node in before.body if isinstance(node, definitions)}
        new = {node.name if isinstance(node, (ast.FunctionDef, ast.ClassDef)) else ast.dump(node.targets[0]):
            ast.dump(node) for node in after.body if isinstance(node, definitions)}
        if name == "host":
            assert new == {"host_verdict": old["host_verdict"]}
        else:
            assert new == old
    easy = tasks.generate_instance(3, 3, True, 1)
    assert easy.claims == {("A", "B"): 7, ("B", "C"): 3, ("A", "C"): 12}
    hard = tasks.generate_instance(8, 14, True, 1)
    assert len(hard.items) == 8 and len(hard.claims) == 14
    assert hard.claims[("A", "G")] == 22
    assert host.host_verdict(easy) == host.host_verdict(hard) == "CONTRADICTION"
    assert host.host_verdict(tasks.generate_instance(8, 14, False, 1)) == "CONSISTENT"


@pytest.mark.parametrize("raw,expected", [
    ("CONSISTENT", "CONSISTENT"), ("INCONSISTENT", "UNKNOWN"),
    ("reasoning\nVERDICT: CONTRADICTION", "CONTRADICTION"),
    ("CONSISTENT or CONTRADICTION", "UNKNOWN"), ("I refuse", "UNKNOWN"),
])
def test_original_verdict_parser_remains_strict(raw, expected):
    assert conditions.parse_verdict(raw) == expected


@pytest.mark.parametrize("style", ["direct", "cot"])
def test_accounted_teaching_preserves_original_prompt_and_decoding(tmp_path, style):
    gateway, provider = make_gateway(tmp_path, answer="Reasoning\nVERDICT: CONTRADICTION",
        max_output_tokens=2048)
    path = tmp_path / "capture.json"
    result = recording.record_one("vendor/model", style=style, gateway=gateway, output_path=path)
    inst = tasks.generate_instance(3, 3, True, 1)
    prompt = conditions._format_problem(inst) + (conditions._COT if style == "cot" else conditions._DIRECT)
    assert result["prompt"] == prompt and result["host_verdict"] == "CONTRADICTION"
    assert result["model_verdict"] == "CONTRADICTION" and result["laundered"] is False
    assert result["stop"] is False and result["pfp_exchange"]["usage"]["cost"] == 0.000001
    assert len(provider.calls) == 1
    submitted = provider.calls[0]
    public = json.loads(submitted.user)
    assert public["input"]["prompt"] == prompt
    assert "ground_truth" not in submitted.user and "host_verdict" not in submitted.user
    assert submitted.decoding.temperature is None and submitted.decoding.response_format is None
    assert result["pfp_exchange"]["request"]["max_tokens"] == 2048
    assert base64.b64decode(result["pfp_exchange"]["provider_wire"]["raw_reply_base64"]) == provider.raw
    assert json.loads(path.read_text(encoding="utf-8")) == result


@pytest.mark.parametrize("raw", ["not-json", "{}",
    '{"task_id":"wrong","attempt_id":"wrong","input_sha256":"wrong","answer":"CONSISTENT"}'])
def test_malformed_or_wrong_binding_is_retained_without_model_verdict(tmp_path, raw):
    gateway, provider = make_gateway(tmp_path, raw_content=raw, max_output_tokens=2048)
    result = recording.record_one("vendor/model", gateway=gateway)
    assert result["stop"] and result["stop_reason"].startswith("PFP_")
    assert result["model_verdict"] == "UNKNOWN" and result["model_raw"] is None
    assert result["evidence_grade"] == "TYPED_REFUSAL" and result["laundered"] is False
    assert base64.b64decode(result["pfp_exchange"]["pfp"]["raw_reply_base64"]).decode() == raw
    assert base64.b64decode(result["pfp_exchange"]["provider_wire"]["raw_reply_base64"]) == provider.raw
    assert len(provider.calls) == 1


@pytest.mark.parametrize("cost", [0.000001, None])
def test_easy_and_hard_share_original_allowance_and_unknown_cost(tmp_path, cost):
    gateway, provider = make_gateway(tmp_path, answer="CONSISTENT", cost=cost,
        max_output_tokens=2048, max_calls=1)
    easy = recording.record_one("vendor/model", gateway=gateway)
    assert easy["stop"] is (cost is None)
    assert easy["laundered"] is (cost is not None)
    assert easy["pfp_exchange"]["usage"]["cost"] == cost
    hard = recording.record_one("vendor/model", 1, "cot", 8, 14, gateway=gateway)
    assert hard["stop"] and hard["model_verdict"] == "UNKNOWN"
    assert hard["stop_reason"] == ("UNRECONCILED_ATTEMPT" if cost is None else "CALL_ALLOWANCE_EXHAUSTED")
    assert len(provider.calls) == 1


def test_existing_output_or_unaccounted_call_refuses_before_send(tmp_path):
    gateway, provider = make_gateway(tmp_path, answer="CONSISTENT", max_output_tokens=2048)
    path = tmp_path / "old.json"
    path.write_bytes(b"historical bytes")
    with pytest.raises(ValueError, match="OUTPUT_ALREADY_EXISTS"):
        recording.record_one("vendor/model", gateway=gateway, output_path=path)
    with pytest.raises(ValueError, match="PFP_ACCOUNTED_GATEWAY_REQUIRED"):
        recording.record_one("vendor/model", output_path=tmp_path / "never.json")
    assert not provider.calls and path.read_bytes() == b"historical bytes"
    assert not (tmp_path / "never.json").exists()


@pytest.mark.parametrize("cost,raw", [(None, None), (0.000001, "not-json")])
def test_cli_reuses_one_gateway_and_stops_before_hard_case(tmp_path, monkeypatch, cost, raw):
    gateway, provider = make_gateway(tmp_path, answer="CONSISTENT", cost=cost,
        raw_content=raw, max_output_tokens=2048)
    composed = []

    def factory(*args, **kwargs):
        composed.append((args, kwargs))
        return gateway

    monkeypatch.setattr(recording, "create_accounted_openrouter_gateway", factory)
    out = tmp_path / "new-recording"
    assert recording.record_main(["--model", "vendor/model", "--output-dir", str(out),
        "--max-provider-calls", "4", "--max-estimated-cost-microusd", "50000"]) == 2
    assert len(composed) == len(provider.calls) == 1
    assert composed[0][0] == ("vendor/model", 2048)
    assert composed[0][1]["max_calls"] == 4
    assert (out / "easy.json").is_file() and not (out / "hard.json").exists()


def test_renderer_existing_output_refuses_before_optional_import(tmp_path, monkeypatch):
    scene = importlib.import_module(
        "education.documentation.004_oepfp.curriculum.scenes.naked_prompt_launder")
    output = tmp_path / "old.mp4"
    output.write_bytes(b"original movie")
    original = builtins.__import__

    def no_renderer(name, *args, **kwargs):
        assert not name.startswith("matplotlib"), "existing output reached optional renderer"
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_renderer)
    with pytest.raises(ValueError, match="OUTPUT_ALREADY_EXISTS"):
        scene.render_mp4({}, output)
    assert output.read_bytes() == b"original movie"
