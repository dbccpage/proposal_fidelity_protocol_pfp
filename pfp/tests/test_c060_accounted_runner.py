"""C060 keeps its original judges while live proposals use accounted PFP."""

import ast
import base64
from dataclasses import replace
from hashlib import sha256
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

import pytest

from pfp.infrastructure import synthesis_matrix
from pfp.tests.test_pilot_matrix_pfp import make_gateway


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "c060_self_verifying_checker_synthesis"
SOURCE = ROOT / (PACKAGE.replace(".", "/") + "/run_c060_matrix.py")
MODEL = "meta-llama/llama-3.1-8b-instruct"


def runner():
    return importlib.import_module(PACKAGE + ".run_c060_matrix")


@pytest.mark.parametrize("module", [False, True])
def test_help_outside_checkout_needs_no_credentials_or_legacy_aliases(tmp_path, module):
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    environment.pop("PYTHONPATH", None)
    environment.pop("OPENROUTER_API_KEY", None)
    if module:
        environment["PYTHONPATH"] = str(ROOT)
    arguments = ["-m", PACKAGE + ".run_c060_matrix"] if module else [str(SOURCE)]
    result = subprocess.run(
        [sys.executable, "-B", *arguments, "--help"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "--max-estimated-cost-microusd" in result.stdout
    assert not list(tmp_path.iterdir())


def test_original_model_case_prompt_and_extract_source_segments_are_unchanged():
    source = SOURCE.read_text(encoding="utf-8")
    expected = {
        "MODELS": "cea1adedc3ba9bbc5d6b887846dd6a05ee9f5e1d513190209204df7dd8f0a271",
        "SYSTEM_PROMPT": "e7e478220468ed5143b29dd9dff8cc283596a78ed8d6c445dd60ccf3e2092f82",
        "TEST_CASES": "962b2052af55304a5dc83bc8288936773e572c86ae5f578ed3e9a59fc8a0f169",
        "extract_json": "403fe45f3b28b15f1c578da9be3b05844fcdbb5879e9776b978412d18c686ef2",
    }
    observed = {}
    for node in ast.parse(source).body:
        name = (
            node.name
            if isinstance(node, ast.FunctionDef)
            else (
                node.targets[0].id
                if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                else None
            )
        )
        if name in expected:
            observed[name] = sha256(ast.get_source_segment(source, node).encode()).hexdigest()
    assert observed == expected


def test_legacy_query_without_accounting_refuses_before_transport(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", lambda *_a, **_k: pytest.fail("raw fallback"))
    result = runner().query_openrouter("unused", MODEL, runner().TEST_CASES[0])
    assert not result["success"] and result["stop"]
    assert result["error"] == "PFP_ACCOUNTED_GATEWAY_REQUIRED"
    assert result["raw_text"] == "" and result["usage"] == {}


def test_query_retains_actual_bound_answer_and_exact_wire(tmp_path):
    gateway, provider = make_gateway(
        tmp_path, model=MODEL, answer={"verdict": "ACCEPT", "code": None}
    )
    result = runner().query_openrouter(
        "unused",
        MODEL,
        runner().TEST_CASES[0],
        gateway=gateway,
        max_tokens=256,
        task_id="public-checker-task",
        attempt_id="query-0",
    )
    assert result["success"] and result["pfp"]["schema_valid"]
    assert json.loads(result["raw_text"]) == {"verdict": "ACCEPT", "code": None}
    assert result["attempt_state"] == "CompletedSettled"
    assert base64.b64decode(result["provider_wire"]["raw_reply_base64"]) == provider.raw
    assert all(
        secret not in provider.calls[0].user
        for secret in (runner().TEST_CASES[0]["case_id"], "expected_verdict", "expected_code")
    )


@pytest.mark.parametrize(
    "raw",
    ["not JSON", '{"task_id":"wrong","attempt_id":"wrong","input_sha256":"wrong","answer":{}}'],
)
def test_malformed_or_wrong_binding_is_not_a_reasoning_answer(tmp_path, raw):
    gateway, provider = make_gateway(tmp_path, model=MODEL, raw_content=raw)
    result = runner().query_openrouter(
        "unused", MODEL, runner().TEST_CASES[0], gateway=gateway, max_tokens=256
    )
    assert not result["success"] and not result["stop"] and result["raw_text"] == ""
    assert result["error"].startswith("PFP_") and result["pfp"]
    assert base64.b64decode(result["provider_wire"]["raw_reply_base64"]) == provider.raw


@pytest.mark.parametrize(
    "answer,expected",
    [
        ({"verdict": "ACCEPT", "code": None}, "ACCEPTED"),
        ({"verdict": "REJECT", "code": "SCHEMA"}, "REJECTED"),
    ],
)
def test_original_dual_judges_accept_or_reject_actual_bound_witness(tmp_path, answer, expected):
    gateway, _provider = make_gateway(tmp_path, model=MODEL, answer=answer)
    plan = replace(runner().spec(), cases=runner().TEST_CASES[:1], max_tokens=256)
    output = tmp_path / "run"
    summary = synthesis_matrix.run_matrix(
        plan, output, gateways={MODEL: gateway}, model_ids=[MODEL], pause_s=0
    )
    assert summary["models"][MODEL]["counts"][expected] == 1
    row = json.loads(next(output.glob("records_*.jsonl")).read_text())
    assert len(row["checkers"]) == 2
    assert all(check["ok"] is (expected == "ACCEPTED") for check in row["checkers"])


def test_unknown_cost_stops_remaining_models_and_cases(tmp_path):
    first, provider = make_gateway(tmp_path, model=MODEL, cost=None)
    other_model = runner().MODELS[0]["id"]
    second, other = make_gateway(tmp_path, model=other_model)
    plan = replace(
        runner().spec(),
        models=[{"id": MODEL}, {"id": other_model}],
        cases=runner().TEST_CASES[:2],
        max_tokens=256,
    )
    summary = synthesis_matrix.run_matrix(
        plan, tmp_path / "run", gateways={MODEL: first, other_model: second}, pause_s=0
    )
    assert len(provider.calls) == 1 and other.calls == [] and summary["attempted"] == 1
    assert summary["stop_reason"] == "CompletedCostUnknown"


def test_main_delegates_bounded_cli_and_never_overwrites_old_output(tmp_path, monkeypatch):
    created = []

    def factory(models, **policy):
        created.append((models, policy))
        gateway, _provider = make_gateway(
            tmp_path,
            model=MODEL,
            max_calls=policy["max_calls"],
            max_output_tokens=policy["max_output_tokens"],
            answer={"verdict": "ACCEPT", "code": None},
        )
        return {MODEL: gateway}

    monkeypatch.setattr(synthesis_matrix, "make_pilot_gateways", factory)
    output = tmp_path / "new-run"
    args = [
        "--output-dir",
        str(output),
        "--model",
        MODEL,
        "--case-limit",
        "1",
        "--max-output-tokens",
        "256",
        "--max-provider-calls",
        "1",
        "--max-estimated-cost-microusd",
        "50000",
    ]
    assert runner().main(args) == 0
    assert len(created) == 1 and created[0][0] == [MODEL]
    before = {path.name: path.read_bytes() for path in output.iterdir()}
    assert runner().main(args) == 2
    assert {path.name: path.read_bytes() for path in output.iterdir()} == before
