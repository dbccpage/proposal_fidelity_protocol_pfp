"""Bounded C017 plumbing checks; host fixtures are not model evidence."""

import base64
import importlib
import json
import os
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

import pytest

from pfp.infrastructure.synthesis_matrix import RunnerRefusal
from pfp.tests.test_pilot_matrix_pfp import make_gateway

PREFIX = "c017_nonabelian_lattice_holonomy"
ARM5 = importlib.import_module(PREFIX + ".eval_arm5_hybrid")
ARM6 = importlib.import_module(PREFIX + ".eval_arm6_hierarchical_decimation")
IMMUNE = importlib.import_module(PREFIX + ".eval_epistemic_immune_transfer")
MODULES = (ARM5, ARM6, IMMUNE)
CASE_DIR = Path(IMMUNE.__file__).parent / "judge_packet" / "cases"


def query(module, gateway=None, **kwargs):
    extra = {"budget_guard": IMMUNE.BudgetGuard(0.5)} if module is IMMUNE else {}
    return module.query_model(
        "vendor/model",
        "public task",
        "unused",
        gateway=gateway,
        task_id="c017-public",
        attempt_id="turn-0",
        max_tokens=256,
        **extra,
        **kwargs,
    )


def runner(module, **kwargs):
    fn = (
        module.run_transfer_benchmark
        if module is IMMUNE
        else module.run_arm5_benchmark
        if module is ARM5
        else module.run_arm6_benchmark
    )
    return fn(model="vendor/model", max_tokens=256, **kwargs)


@pytest.mark.parametrize("module", MODULES)
def test_missing_gateway_refuses_before_transport(module):
    answer, meta = query(module)
    assert answer == {} and not meta["ok"] and meta["stop"]
    assert meta["error"] == "PFP_ACCOUNTED_GATEWAY_REQUIRED"
    assert meta["cost"] == 0 and meta["provider_wire"] is None


@pytest.mark.parametrize("module", MODULES)
def test_original_bound_answer_and_negative_reach_original_dual_judges(module, tmp_path):
    case = json.loads((CASE_DIR / "base" / "base_01.json").read_text())
    original, _ = IMMUNE.reference_solve(case)
    gateway, provider = make_gateway(tmp_path, answer=original)
    result = runner(module, gateway=gateway, selected_case="base_01")
    row = result["cases_evaluated"][0]
    row = row["immune_assisted"] if module is IMMUNE else row
    assert row["passed"] and all(v["passed"] for v in row["details"].values())
    meta = row["meta"]
    assert meta["pfp"]["schema_valid"] and meta["pfp"]["failure_class"] == "NONE"
    assert base64.b64decode(meta["provider_wire"]["raw_reply_base64"]) == provider.raw
    assert meta["request"]["temperature"] == (0.1 if module is IMMUNE else 0.05)
    assert meta["request"]["max_tokens"] == 256
    assert "expected" not in json.loads(provider.calls[0].user)["input"]["prompt"]
    bad, _ = make_gateway(
        tmp_path,
        answer={"status": "SOLVED", "verdict": "PURE_GAUGE"},
        accounting_name="negative.sqlite3",
    )
    rejected = runner(module, gateway=bad, selected_case="base_01")["cases_evaluated"][0]
    rejected = rejected["baseline"] if module is IMMUNE else rejected
    assert not rejected["passed"] and rejected["meta"]["ok"]


@pytest.mark.parametrize(
    "raw",
    [
        "not JSON",
        "{}",
        '{"task_id":"wrong","attempt_id":"turn-0","input_sha256":"wrong","answer":{}}',
    ],
)
def test_malformed_or_wrong_binding_is_retained_and_not_judged(tmp_path, monkeypatch, raw):
    gateway, provider = make_gateway(tmp_path, raw_content=raw)
    monkeypatch.setattr(IMMUNE, "evaluate_dual", lambda *args: pytest.fail("unbound judge input"))
    result = IMMUNE.run_transfer_benchmark(
        model="vendor/model", gateway=gateway, max_tokens=256, selected_case="base_01"
    )
    assert not result["cases_evaluated"][0]["baseline"]["passed"]
    meta = result["cases_evaluated"][0]["immune_assisted"]["meta"]
    assert meta["content"] is None and meta["error"].startswith("PFP_")
    assert base64.b64decode(meta["provider_wire"]["raw_reply_base64"]) == provider.raw


def test_unknown_cost_stops_both_arms_and_remaining_cases(tmp_path, monkeypatch):
    gateway, provider = make_gateway(tmp_path, cost=None)
    monkeypatch.setattr(IMMUNE, "evaluate_dual", lambda *args: pytest.fail("unsettled judge input"))
    result = IMMUNE.run_transfer_benchmark(model="vendor/model", gateway=gateway, max_tokens=256)
    assert len(provider.calls) == 1 and len(result["cases_evaluated"]) == 1
    assert result["total_cost_usd"] is None and result["total_cost_known_subtotal_usd"] == 0
    assert result["stop_reason"] == "CompletedCostUnknown"
    assert result["cases_evaluated"][0]["immune_assisted"]["reason"] == "NOT_RUN_AFTER_STOP"


def test_continuing_call_allowance_is_shared_across_paired_arms(tmp_path):
    case = json.loads((CASE_DIR / "poisoned" / "pois_01.json").read_text())
    answer, _ = IMMUNE.reference_solve(case)
    gateway, provider = make_gateway(tmp_path, answer=answer, max_calls=1)
    result = IMMUNE.run_transfer_benchmark(model="vendor/model", gateway=gateway, max_tokens=256)
    assert len(provider.calls) == 1 and len(result["cases_evaluated"]) == 1
    assert result["stop_reason"] == "CALL_ALLOWANCE_EXHAUSTED"
    assert result["total_cost_usd"] == 0.000001


def test_composed_gateway_receives_actual_selected_objective_and_task_id(tmp_path, monkeypatch):
    case = json.loads((CASE_DIR / "base" / "base_01.json").read_text())
    answer, _ = IMMUNE.reference_solve(case)
    captured = {}
    providers = []

    def factory(models, **policy):
        captured.update(models=models, **policy)
        gateway, provider = make_gateway(
            tmp_path,
            answer=answer,
            max_calls=policy["max_calls"],
            max_output_tokens=policy["max_output_tokens"],
        )
        providers.append(provider)
        return {"vendor/model": gateway}

    monkeypatch.setattr(IMMUNE, "make_pilot_gateways", factory)
    result = runner(
        IMMUNE,
        selected_case="base_01",
        max_estimated_cost_microusd=50000,
        max_provider_calls=2,
        output_dir=tmp_path / "new-run",
    )
    expected_objective = {
        "challenge": "C017",
        "max_output_tokens": 256,
        "selected_public_tasks": [
            {
                "case_id": "base_01_s3_open_nonflat",
                "arms": [
                    {"arm": "baseline", "prompt": IMMUNE.build_c017_prompt(case, False)},
                    {"arm": "immune_assisted", "prompt": IMMUNE.build_c017_prompt(case, True)},
                ],
            }
        ],
    }
    objective_sha256 = sha256(
        json.dumps(
            expected_objective, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    assert captured["models"] == ["vendor/model"]
    assert captured["run_id"] == result["task_id"]
    assert result["task_id"].startswith("c017:") and result["task_id"] != "legacy-estimated"
    assert captured["objective_sha256"] == result["objective_sha256"] == objective_sha256
    assert result["objective"] == expected_objective
    assert captured["max_calls"] == 2 and captured["max_estimated_cost_microusd"] == 50000
    assert captured["accounting_path"] == tmp_path / "new-run" / "accounting.sqlite3"
    assert len(providers[0].calls) == 2
    assert all(json.loads(request.user)["task_id"] == result["task_id"]
               for request in providers[0].calls)


def test_lower_legacy_ceiling_refuses_shared_gateway_before_send_or_output(tmp_path):
    gateway, provider = make_gateway(tmp_path)
    output = tmp_path / "new-output"
    with pytest.raises(RunnerRefusal, match="LEGACY_BUDGET_CEILING_CONFLICT"):
        IMMUNE.run_transfer_benchmark(
            model="vendor/model",
            gateway=gateway,
            max_tokens=256,
            budget_ceiling=0.001,
            output_dir=output,
        )
    assert not provider.calls and not output.exists()


@pytest.mark.parametrize(
    "caps, code",
    [
        ({"max_estimated_cost_microusd": 1}, "PFP_COST_ALLOWANCE_CONFLICT"),
        ({"max_provider_calls": 1}, "PFP_CALL_ALLOWANCE_CONFLICT"),
    ],
)
def test_injected_gateway_cannot_exceed_explicit_lower_allowance(tmp_path, caps, code):
    gateway, provider = make_gateway(tmp_path)
    output = tmp_path / "new-output"
    with pytest.raises(RunnerRefusal, match=code):
        runner(ARM5, gateway=gateway, output_dir=output, **caps)
    assert not provider.calls and not output.exists()


def test_nan_legacy_guard_refuses_before_dispatch(tmp_path):
    gateway, provider = make_gateway(tmp_path)
    _, meta = IMMUNE.query_model(
        "vendor/model",
        "public",
        "unused",
        IMMUNE.BudgetGuard(float("nan")),
        gateway=gateway,
        max_tokens=256,
    )
    assert meta["error"] == "INVALID_BUDGET_CEILING" and meta["stop"]
    assert meta["cost"] == 0 and not provider.calls


def test_ambiguous_transport_without_reply_has_unknown_cost_and_stops(tmp_path):
    from operations.domain.rop.result import Err
    from adversary.domain.providers.attempt import ProviderFailure, RetryClass

    gateway, provider = make_gateway(tmp_path)

    def fail_after_reservation(*args, **kwargs):
        provider.calls.append(args)
        return Err(ProviderFailure("TRANSPORT_OUTCOME_UNKNOWN", "fixture", RetryClass.TERMINAL))

    provider.complete_result = fail_after_reservation
    result = runner(IMMUNE, gateway=gateway)
    meta = result["cases_evaluated"][0]["baseline"]["meta"]
    assert len(provider.calls) == 1 and meta["provider_wire"] is None
    assert meta["cost_may_be_incurred"] and result["total_cost_usd"] is None
    assert result["stop_reason"] == "TRANSPORT_OUTCOME_UNKNOWN"


@pytest.mark.parametrize("module", MODULES)
def test_dry_run_is_new_directory_host_fixture_and_never_overwrites(module, tmp_path):
    output = tmp_path / "new-run"
    result = runner(module, dry_run=True, selected_case="base_01", output_dir=output)
    assert result["evidence_grade"] == "HOST_REFERENCE_SELF_CONSISTENCY"
    assert result["total_cost_usd"] == 0.0
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    receipt = next(json.loads(raw) for name, raw in before.items() if "receipt" in name)
    report = next(raw for name, raw in before.items() if "report" in name)
    assert receipt["sha256"] == sha256(report).hexdigest()
    assert receipt["evidence_grade"] == "HOST_REFERENCE_SELF_CONSISTENCY"
    assert receipt["scientific_outcome"] == "HOST_REFERENCE_SELF_CONSISTENCY"
    assert receipt["receipt_id"] and receipt["model"] == "vendor/model"
    assert (
        "immune_pass_rate" in receipt
        if module is IMMUNE
        else ("arm5_pass_rate" in receipt if module is ARM5 else "arm6_pass_rate" in receipt)
    )
    with pytest.raises(RunnerRefusal, match="OUTPUT_DIR_EXISTS"):
        runner(module, dry_run=True, output_dir=output)
    assert {p.name: p.read_bytes() for p in output.iterdir()} == before


def test_public_prompts_do_not_use_private_expected_metadata():
    case = json.loads((CASE_DIR / "base" / "base_01.json").read_text())
    poisoned = {
        **case,
        "id": "PRIVATE_LABEL_SENTINEL",
        "expected_verdict": "PRIVATE_ORACLE_SENTINEL",
    }
    for builder in (
        ARM5.build_c017_arm5_prompt,
        ARM6.build_c017_arm6_prompt,
        IMMUNE.build_c017_prompt,
    ):
        assert builder(case) == builder(poisoned)


@pytest.mark.parametrize("module", MODULES)
def test_direct_help_outside_checkout_is_offline(module, tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        [sys.executable, module.__file__, "--help"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    assert "--max-estimated-cost-microusd" in proc.stdout and "--output-dir" in proc.stdout
