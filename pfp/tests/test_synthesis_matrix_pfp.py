"""Synthesis pilots retain their judges while all actual replies pass PFP/accounting."""

import base64
import json

import pytest

from omega_engine_pfp.infrastructure import synthesis_matrix as runner
from omega_engine_pfp.tests.test_pilot_matrix_pfp import make_gateway


MODEL = "vendor/model"


def spec(*, checkers=None, models=None, cases=None, max_tokens=256):
    return runner.MatrixSpec("public-challenge", "Solve the public problem.", "Return its value.",
        cases if cases is not None else [dict(case_id="private_label", n=2, expected=2)],
        checkers if checkers is not None else [("original", lambda case, answer:
            (answer.get("value") == case["expected"], "original comparison"))],
        models if models is not None else [dict(id=MODEL)], max_tokens=max_tokens)


def test_legacy_direct_sender_refuses_without_network(monkeypatch):
    sent = []
    def forbidden(*args, **kwargs):
        sent.append(args)
        raise AssertionError("raw transport reached")
    monkeypatch.setattr("urllib.request.urlopen", forbidden)
    exchange = runner.call_model("unused", MODEL, "system", "user", max_tokens=256, title="pilot")
    assert not exchange.ok and exchange.error == "PFP_ACCOUNTED_GATEWAY_REQUIRED"
    assert not sent


def test_success_still_runs_original_judge_and_keeps_private_labels_out(tmp_path):
    gateway, provider = make_gateway(tmp_path, answer=dict(case_id="case_01", value=2))
    out = tmp_path / "run"
    summary = runner.run_matrix(spec(), out, "", gateways={MODEL: gateway}, pause_s=0)
    assert summary["models"][MODEL]["accepted"] == 1
    prepared = provider.calls[0].user
    assert "private_label" not in prepared and '"expected"' not in prepared
    record = json.loads(next(out.glob("records_*.jsonl")).read_text())
    assert record["checkers"][0]["message"] == "original comparison"
    assert record["pfp"]["evidence_grade"] == "UNVERIFIED"
    assert base64.b64decode(record["provider_wire"]["raw_reply_base64"]) == provider.raw
    assert record["attempt_state"] == "CompletedSettled"


def test_bound_wrong_answer_is_scored_by_original_judge(tmp_path):
    gateway, _ = make_gateway(tmp_path, answer=dict(case_id="case_01", value=99))
    summary = runner.run_matrix(spec(), tmp_path / "run", "", gateways={MODEL: gateway}, pause_s=0)
    assert summary["models"][MODEL]["counts"]["REJECTED"] == 1


def test_malformed_pfp_reply_never_reaches_original_judge(tmp_path):
    gateway, _ = make_gateway(tmp_path, raw_content="not JSON")
    judged = []
    summary = runner.run_matrix(spec(checkers=[("guard", lambda *a: judged.append(a))]),
        tmp_path / "run", "", gateways={MODEL: gateway}, pause_s=0)
    assert not judged and summary["models"][MODEL]["counts"]["INFRA_ERROR"] == 1
    assert summary["models"][MODEL]["scored"] == 0


def test_unknown_cost_stops_all_cases_and_models(tmp_path):
    first, p1 = make_gateway(tmp_path, cost=None)
    second, p2 = make_gateway(tmp_path, model="vendor/other")
    planned = spec(models=[dict(id=MODEL), dict(id="vendor/other")],
        cases=[dict(case_id="private_1", n=2, expected=2), dict(case_id="private_2", n=3, expected=3)])
    out = tmp_path / "run"
    summary = runner.run_matrix(planned, out, "", gateways={MODEL: first, "vendor/other": second}, pause_s=0)
    assert len(p1.calls) == 1 and not p2.calls
    assert summary["stop_reason"] == "CompletedCostUnknown"
    assert summary["attempted"] == 1 and summary["planned"] == 4
    record = json.loads(next(out.glob("records_*.jsonl")).read_text())
    assert record["usage"]["cost"] is None
    assert base64.b64decode(record["provider_wire"]["raw_reply_base64"]) == p1.raw


def test_shared_call_allowance_does_not_restart_for_next_model(tmp_path):
    first, p1 = make_gateway(tmp_path, max_calls=1)
    second, p2 = make_gateway(tmp_path, model="vendor/other", max_calls=1)
    summary = runner.run_matrix(spec(models=[dict(id=MODEL), dict(id="vendor/other")]),
        tmp_path / "run", "", gateways={MODEL: first, "vendor/other": second}, pause_s=0)
    assert len(p1.calls) == 1 and not p2.calls
    assert summary["stop_reason"] == "CALL_ALLOWANCE_EXHAUSTED"


def test_without_accounted_policy_refuses_before_creating_outputs(tmp_path):
    with pytest.raises(runner.RunnerRefusal, match="PFP_ACCOUNTED_GATEWAY_REQUIRED"):
        runner.run_matrix(spec(), tmp_path / "run", "not-a-credential", pause_s=0)
    assert not (tmp_path / "run").exists()


def test_original_output_cap_not_silently_lowered(tmp_path):
    gateway, provider = make_gateway(tmp_path)
    with pytest.raises(runner.RunnerRefusal, match="PFP_OUTPUT_BOUND_MISMATCH"):
        runner.run_matrix(spec(max_tokens=4096), tmp_path / "run", "", gateways={MODEL: gateway})
    assert not provider.calls and not (tmp_path / "run").exists()


def test_empty_checker_list_never_becomes_acceptance(tmp_path):
    gateway, provider = make_gateway(tmp_path)
    with pytest.raises(runner.RunnerRefusal, match="CHECKER_REQUIRED"):
        runner.run_matrix(spec(checkers=[]), tmp_path / "run", "", gateways={MODEL: gateway})
    assert not provider.calls


def test_cli_exposes_explicit_bounded_selection(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(runner, "run_matrix", lambda plan, *a, **k: seen.append((plan, k)) or {})
    planned = spec(max_tokens=4096, cases=[dict(case_id="a"), dict(case_id="b")])
    assert runner.main(planned, ["--output-dir", str(tmp_path / "run"), "--model", MODEL,
        "--max-estimated-cost-microusd", "10000", "--max-provider-calls", "1",
        "--max-output-tokens", "256", "--case-limit", "1"]) == 0
    assert seen[0][0].max_tokens == 256 and len(seen[0][0].cases) == 1
    assert seen[0][1]["max_estimated_cost_microusd"] == 10000

def test_original_c052_command_runs_outside_pytest_import_aliases():
    import subprocess
    import sys
    completed = subprocess.run([sys.executable, "-B", "-m",
        "omega_engine_pfp.tests.pilots.c052_maxflow_mincut_certificates.run_c052_matrix",
        "--help"], capture_output=True, text=True, timeout=20)
    assert completed.returncode == 0, completed.stderr
    assert "--max-estimated-cost-microusd" in completed.stdout
