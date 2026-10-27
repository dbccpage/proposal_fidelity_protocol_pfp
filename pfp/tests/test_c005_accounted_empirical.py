"""C005 empirical routing controls, with actual accounted local fixtures only."""

import base64
import importlib
import json
from dataclasses import asdict, replace
from types import SimpleNamespace

import pytest

from operations.domain.rop.result import Ok
from pfp.infrastructure.synthesis_matrix import RunnerRefusal
from pfp.tests.test_pilot_matrix_pfp import make_gateway

PREFIX = "pilots.llm_mechanism.c005_hosted_decode_controls"
SCHEMA = importlib.import_module(PREFIX + ".empirical_001_runner")
BIAS = importlib.import_module(PREFIX + ".empirical_002_runner")
MODULES = (SCHEMA, BIAS)


def cases():
    original = SCHEMA.get_hidden_base_cases()
    return [original[0], original[50]]


def answer(case):
    if case["kind"] == "consistency":
        return {"verdict": case["expected_verdict"], "certificate": case["expected_certificate"]}
    return {
        "status": "SOLVED",
        "repaired": case["expected_repaired"],
        "weighted_l1": case["expected_weighted_l1"],
    }


def execute(module, case, client, **kwargs):
    args = [case, client, "vendor/model"]
    if module is BIAS:
        args.append({123: 5, "456": -100})
    args.append(SCHEMA.BudgetController())
    return (
        module.execute_single_case if module is SCHEMA else module.execute_single_case_logit_bias
    )(*args, **kwargs)


def run(module, **kwargs):
    if module is BIAS:
        kwargs.setdefault("bias_map", {"123": 5})
    return (
        module.run_test_001_empirical_sweep
        if module is SCHEMA
        else module.run_test_002_empirical_sweep
    )(model="vendor/model", **kwargs)


@pytest.mark.parametrize("module", MODULES)
def test_raw_client_refused_without_dispatch(module):
    called = []
    raw = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **kwargs: called.append(kwargs))
        )
    )
    trace = execute(module, cases()[0], raw)
    assert trace.stop and trace.error_message == "PFP_ACCOUNTED_GATEWAY_REQUIRED"
    assert not called and not trace.is_correct and trace.cost_usd == 0


@pytest.mark.parametrize("module", MODULES)
@pytest.mark.parametrize("index", [0, 1])
def test_original_prompt_payload_and_judge_positive_negative(module, index, tmp_path):
    case = cases()[index]
    gateway, provider = make_gateway(tmp_path, answer=answer(case), max_output_tokens=96)
    trace = execute(module, case, gateway)
    assert trace.is_parseable and trace.is_schema_valid and trace.is_correct
    assert trace.exchange["pfp"]["failure_class"] == "NONE"
    assert base64.b64decode(trace.exchange["provider_wire"]["raw_reply_base64"]) == provider.raw
    payload = trace.exchange["request"]
    assert payload["max_tokens"] == 96 and payload["temperature"] == 0.0
    if module is SCHEMA:
        descriptor = payload["response_format"]["json_schema"]
        expected = SCHEMA.CONSISTENCY_JSON_SCHEMA if index == 0 else SCHEMA.CYCLE_REPAIR_JSON_SCHEMA
        actual = dict(descriptor["schema"]["properties"]["answer"])
        actual.pop("$id", None)
        assert actual == expected["schema"] and descriptor["name"] == expected["name"]
    else:
        assert "response_format" not in payload
        assert payload["logit_bias"] == {"123": 5, "456": -100}
        assert trace.control_provenance["provider_honored"] is None
    prompt = json.loads(provider.calls[0].user)["input"]["prompt"]
    assert prompt == trace.prompt and "expected_" not in prompt and case["case_id"] not in prompt
    wrong = answer(case)
    if index == 0:
        wrong["certificate"] = {"n0": "100", "n1": "100"}
    else:
        wrong["weighted_l1"] = "999"
    bad, _ = make_gateway(
        tmp_path, answer=wrong, max_output_tokens=96, accounting_name="bad.sqlite3"
    )
    rejected = execute(module, case, bad)
    assert rejected.is_schema_valid and not rejected.is_correct


def test_strict_schema_failure_is_observed_json_and_never_reaches_judge(tmp_path, monkeypatch):
    gateway, _ = make_gateway(tmp_path, answer={"verdict": "CONSISTENT"}, max_output_tokens=96)
    monkeypatch.setattr(
        SCHEMA, "verify_consistency_certificate", lambda *a: pytest.fail("invalid judge input")
    )
    trace = execute(SCHEMA, cases()[0], gateway)
    assert trace.is_parseable and not trace.is_schema_valid and not trace.is_correct
    assert not trace.judge_eligible and trace.exchange["error"].startswith("PFP_")


@pytest.mark.parametrize("module", MODULES)
def test_unknown_cost_stops_outer_cases_and_preserves_wire(module, tmp_path):
    gateway, provider = make_gateway(
        tmp_path, answer=answer(cases()[0]), cost=None, max_output_tokens=96
    )
    result = run(module, gateway=gateway, cases=cases(), max_cases=2)
    assert len(provider.calls) == 1 and result["total_cases"] == 1
    assert result["planned_cases"] == 2 and result["actual_concurrency"] == 1
    assert result["financial_accounting"]["total_billed_cost_usd"] is None
    assert result["financial_accounting"]["known_cost_subtotal_usd"] == 0
    assert result["stop_reason"] == "CompletedCostUnknown"
    assert (
        base64.b64decode(result["case_traces"][0]["exchange"]["provider_wire"]["raw_reply_base64"])
        == provider.raw
    )


def test_wrong_binding_cannot_reach_original_judge(tmp_path, monkeypatch):
    gateway, provider = make_gateway(
        tmp_path, raw_content='{"task_id":"wrong","answer":{}}', max_output_tokens=96
    )
    monkeypatch.setattr(
        SCHEMA, "verify_consistency_certificate", lambda *a: pytest.fail("unbound judge input")
    )
    trace = execute(SCHEMA, cases()[0], gateway)
    assert not trace.judge_eligible and not trace.is_correct
    assert base64.b64decode(trace.exchange["provider_wire"]["raw_reply_base64"]) == provider.raw


def test_lower_legacy_budget_and_explicit_call_cap_refuse_before_output(tmp_path):
    gateway, provider = make_gateway(tmp_path, max_output_tokens=96)
    output = tmp_path / "new-run"
    with pytest.raises(RunnerRefusal, match="LEGACY_BUDGET_CEILING_CONFLICT"):
        run(
            SCHEMA,
            gateway=gateway,
            budget_ctrl=SCHEMA.BudgetController(ceiling_usd=0.001),
            output_dir=output,
        )
    with pytest.raises(RunnerRefusal, match="PFP_CALL_ALLOWANCE_CONFLICT"):
        run(SCHEMA, gateway=gateway, max_provider_calls=1, output_dir=output)
    assert not output.exists() and not provider.calls


def test_dry_fixture_and_new_output_protection(tmp_path):
    output = tmp_path / "new-run"
    result = run(SCHEMA, dry_run=True, cases=cases(), max_cases=2, output_dir=output)
    assert result["evidence_grade"] == "HOST_REFERENCE_SELF_CONSISTENCY"
    assert result["performance_metrics"]["verified_correct_count"] == 2
    accounting = json.loads((output / "accounting.json").read_bytes())
    assert accounting["total_calls"] == 0 and accounting["attempted_cases"] == 2
    summary = json.loads((output / "summary.json").read_bytes())
    assert summary["cost_per_verified_success_usd"] == 0 and summary["mean_latency_sec"] == 0
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    with pytest.raises(RunnerRefusal, match="OUTPUT_DIR_EXISTS"):
        run(SCHEMA, dry_run=True, output_dir=output)
    assert {p.name: p.read_bytes() for p in output.iterdir()} == before


def test_no_implicit_tokenizer_download_or_fabricated_bias_map():
    with pytest.raises(RunnerRefusal, match="EXPLICIT_BIAS_OR_LOCAL_TOKENIZER_REQUIRED"):
        BIAS.run_test_002_empirical_sweep(dry_run=True, max_cases=1)


def test_pairing_requires_complete_compatible_unique_actual_traces(tmp_path):
    case = cases()[0]
    gateway, _ = make_gateway(tmp_path, answer=answer(case), max_output_tokens=96)
    baseline = asdict(execute(SCHEMA, case, gateway))
    current = asdict(execute(BIAS, case, gateway))
    paired = BIAS._paired_analysis([baseline], [current])
    assert paired["status"] == "AVAILABLE" and paired["paired_total"] == 1
    assert paired["correctness_mcnemar_exact_p_value"] == 1.0
    assert BIAS._paired_analysis(None, [current])["correctness_mcnemar_exact_p_value"] is None
    for supplied in (
        [baseline, baseline],
        [{**baseline, "model": "wrong"}],
        [{**baseline, "input_sha256": "wrong"}],
        [{**baseline, "case_sha256": "wrong"}],
        [{**baseline, "is_correct": False}],
        [],
    ):
        analysis = BIAS._paired_analysis(supplied, [current])
        assert analysis["status"] == "UNAVAILABLE"
        assert analysis["correctness_statistically_significant"] is None


BENCHMARKS = ("benchmark_3arm_scratchpad", "benchmark_arm4_hybrid")


def benchmark(name, **kwargs):
    module = importlib.import_module(PREFIX + "." + name)
    run = module.run_3arm_benchmark if name == BENCHMARKS[0] else module.run_hybrid_benchmark
    return run(model="vendor/model", **kwargs)


def benchmark_gateway(tmp_path, *, wrong_certificate=False, wrong_canary=False, **kwargs):
    """Exercise the real PFP/ledger with a schema-aware local provider fixture."""
    payload = {}
    gateway, provider = make_gateway(tmp_path, answer=payload, max_output_tokens=512, **kwargs)
    original_send = provider.complete_result
    case = cases()[0]
    provider.raw_replies = []

    def send(request, **options):
        shape = json.loads(request.user)["answer_schema"]["properties"]
        payload.clear()
        payload.update(answer(case))
        if wrong_certificate:
            payload["certificate"] = {"n0": "100", "n1": "100"}
        if "scratchpad_tree_potentials" in shape:
            payload.update(scratchpad_tree_potentials=case["expected_certificate"], chord_validations=[])
        if "chord_evaluations" in shape:
            payload["chord_evaluations"] = []
        if "canary_check" in shape:
            payload.update(
                canary_check=dict(canary_edge="fixture", canary_expected_residual="0",
                    canary_actual_residual="999" if wrong_canary else "0", canary_passed=True),
                scratchpad_potentials=case["expected_certificate"], chord_residuals=[],
            )
        result = original_send(request, **options)
        provider.raw_replies.append(provider.raw)
        # Distinct wrapper fixtures must not reuse the direct fixture's provider
        # generation identity when they share a real accounting ledger.
        return Ok(replace(result.value, candidate=replace(result.value.candidate,
            generation_id="benchmark-" + result.value.candidate.generation_id)))

    provider.complete_result = send
    return gateway, provider


@pytest.mark.parametrize("name", BENCHMARKS)
def test_benchmark_accounted_schema_binding_and_original_judge(name, tmp_path):
    gateway, provider = benchmark_gateway(tmp_path)
    report = benchmark(name, gateway=gateway, max_tokens=512, cases=[cases()[0]], max_cases=1)
    rows = [row for records in report["case_details"].values() for row in records]
    assert len(rows) == len(provider.calls) == (3 if name == BENCHMARKS[0] else 2)
    assert all(row["correct"] and row["parseable"] for row in rows)
    assert report["stop_reason"] is None and report["terminal_verdict"] is None
    assert report["verdict_status"] == "NOT_ADJUDICATED"
    attempts = []
    for row, request, raw in zip(rows, provider.calls, provider.raw_replies):
        prepared = json.loads(request.user)
        attempts.append(prepared["attempt_id"])
        exchange = row["exchange"]
        assert exchange["pfp"]["failure_class"] == "NONE"
        assert base64.b64decode(exchange["provider_wire"]["raw_reply_base64"]) == raw
        descriptor = exchange["request"]["response_format"]["json_schema"]
        embedded = dict(descriptor["schema"]["properties"]["answer"])
        embedded.pop("$id", None)
        assert embedded == prepared["answer_schema"]
        assert exchange["request"]["max_tokens"] == 512
        assert "expected_certificate" not in prepared["input"]["prompt"]
    assert len(set(attempts)) == len(attempts)


@pytest.mark.parametrize("name", BENCHMARKS)
def test_benchmark_original_certificate_rejects_plausible_wrong_answer(name, tmp_path):
    gateway, _ = benchmark_gateway(tmp_path, wrong_certificate=True)
    report = benchmark(name, gateway=gateway, max_tokens=512, cases=[cases()[0]], max_cases=1)
    rows = [row for records in report["case_details"].values() for row in records]
    assert all(row["parseable"] and not row["correct"] for row in rows)
    assert all(row["exchange"]["pfp"]["failure_class"] == "NONE" for row in rows)


def test_hybrid_canary_remains_a_deciding_negative_control(tmp_path):
    gateway, _ = benchmark_gateway(tmp_path, wrong_canary=True)
    report = benchmark(BENCHMARKS[1], gateway=gateway, cases=[cases()[0]], max_cases=1)
    assert report["case_details"]["arm2_records"][0]["correct"]
    canary = report["case_details"]["arm4_records"][0]
    assert canary["parseable"] and not canary["correct"] and not canary["canary_detected"]


@pytest.mark.parametrize("name", BENCHMARKS)
def test_benchmark_unknown_cost_stops_later_arms_and_pairs(name, tmp_path):
    gateway, provider = benchmark_gateway(tmp_path, cost=None)
    report = benchmark(name, gateway=gateway, max_tokens=512, max_cases=2)
    rows = [row for records in report["case_details"].values() for row in records]
    assert len(provider.calls) == len(rows) == 1
    assert report["stop_reason"] == "CompletedCostUnknown"
    assert report["total_billed_spend_usd"] is None and rows[0]["cost"] is None
    assert base64.b64decode(rows[0]["exchange"]["provider_wire"]["raw_reply_base64"]) == provider.raw
    assert all(value["p_value"] is None for value in report["statistical_tests"].values())


@pytest.mark.parametrize("name", BENCHMARKS)
def test_benchmark_raw_client_and_missing_policy_refuse_before_output(name, tmp_path):
    calls = []
    raw = SimpleNamespace(complete_result=lambda *args, **kwargs: calls.append(args))
    output = tmp_path / "not-created"
    for options in ({}, {"gateway": raw, "max_tokens": 512}):
        with pytest.raises(RunnerRefusal, match="PFP_ACCOUNTED_GATEWAY_REQUIRED"):
            benchmark(name, output_dir=output, **options)
    assert not calls and not output.exists()


@pytest.mark.parametrize("name", BENCHMARKS)
def test_benchmark_dry_fixture_cannot_overwrite_output(name, tmp_path):
    output = tmp_path / "host-fixture"
    report = benchmark(name, dry_run=True, output_dir=output, max_cases=2)
    assert report["evidence_grade"] == "HOST_REFERENCE_SELF_CONSISTENCY"
    assert report["total_billed_spend_usd"] == 0
    assert report["stop_reason"] is None
    assert all(row["correct"] for records in report["case_details"].values() for row in records)
    before = {path.name: path.read_bytes() for path in output.iterdir()}
    assert before
    summary = json.loads(before["summary.json"])
    assert summary["evidence_grade"] == report["evidence_grade"]
    assert summary["verdict_status"] == "NOT_ADJUDICATED" and summary["terminal_verdict"] is None
    assert summary["stop_reason"] is None and summary["summary"] == report["summary"]
    assert summary["model"] == report["model"] and summary["total_spend_usd"] == 0
    with pytest.raises(RunnerRefusal, match="OUTPUT_DIR_EXISTS"):
        benchmark(name, dry_run=True, output_dir=output)
    assert before == {path.name: path.read_bytes() for path in output.iterdir()}


@pytest.mark.parametrize("name", BENCHMARKS)
def test_benchmark_ambiguous_transport_cannot_turn_into_free_failure(name, tmp_path):
    gateway, provider = benchmark_gateway(tmp_path)
    attempted = []

    def timeout(*args, **kwargs):
        attempted.append(True)
        raise TimeoutError("local transport outcome unknown")

    provider.complete_result = timeout
    report = benchmark(name, gateway=gateway, max_tokens=512, max_cases=2)
    rows = [row for records in report["case_details"].values() for row in records]
    assert len(attempted) == len(rows) == 1
    assert report["stop_reason"] and report["total_billed_spend_usd"] is None
    assert rows[0]["cost"] is None and not rows[0]["correct"]


def test_three_arm_original_bounds_share_the_same_call_allowance(tmp_path):
    direct, p1 = make_gateway(tmp_path, max_output_tokens=256, max_calls=2, answer=answer(cases()[0]))
    scratch, p2 = benchmark_gateway(tmp_path, max_calls=2)
    report = benchmark(BENCHMARKS[0], gateways={256: direct, 512: scratch},
        max_provider_calls=2, cases=[cases()[0]], max_cases=1)
    assert len(p1.calls) == len(p2.calls) == 1
    assert report["stop_reason"] == "CALL_ALLOWANCE_EXHAUSTED"
    first = report["case_details"]["arm1_records"][0]
    second = report["case_details"]["arm2_records"][0]
    assert first["exchange"]["request"]["max_tokens"] == 256
    assert second["exchange"]["request"]["max_tokens"] == 512
    assert first["correct"] and second["correct"]


def test_three_arm_separate_ledgers_refuse_before_dispatch(tmp_path):
    direct, p1 = make_gateway(tmp_path, max_output_tokens=256)
    scratch, p2 = benchmark_gateway(tmp_path, accounting_name="separate.sqlite3")
    with pytest.raises(RunnerRefusal, match="PFP_SHARED_ACCOUNTING_REQUIRED"):
        benchmark(BENCHMARKS[0], gateways={256: direct, 512: scratch})
    assert not p1.calls and not p2.calls


@pytest.mark.parametrize("name", BENCHMARKS)
def test_benchmark_unbound_reply_never_reaches_original_judge(name, tmp_path, monkeypatch):
    module = importlib.import_module(PREFIX + "." + name)
    monkeypatch.setattr(module, "verify_consistency_certificate",
        lambda *args: pytest.fail("unbound reply reached original judge"))
    gateway, provider = benchmark_gateway(tmp_path, raw_content='{"task_id":"wrong","answer":{}}')
    report = benchmark(name, gateway=gateway, max_tokens=512, cases=[cases()[0]], max_cases=1)
    rows = [row for records in report["case_details"].values() for row in records]
    assert all(not row["correct"] for row in rows)
    assert all(row["exchange"]["pfp"]["failure_class"] != "NONE" for row in rows)
    assert len(provider.calls) == len(rows)
