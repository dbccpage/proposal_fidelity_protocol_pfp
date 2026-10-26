"""Current Paper 008 execution uses bound actual replies and original finite judges."""

import ast
import base64
import hashlib
import importlib
import json
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from omega_engine_pfp.infrastructure.estimated_gateway import EstimatedBudgetGateway
from omega_engine_woland.domain.providers.types import Provider
from omega_engine_woland.infrastructure.providers.gateway import unbudgeted_gateway


def owner():
    return importlib.import_module("omega_engine_pfp.infrastructure.retraction_benchmark")


def gateway(tmp_path, *, fault=None, max_calls=24, answer="VERDICT: CONSISTENT"):
    fixture = SimpleNamespace(calls=[], raw=[])

    def send(provider, model, request):
        fixture.calls.append(request)
        if fault == "transport":
            raise OSError("synthetic outcome unknown")
        binding = json.loads(request.user)
        reply = {key: binding[key] for key in ("task_id", "attempt_id", "input_sha256")}
        reply["answer"] = answer
        if fault == "wrong_binding":
            reply["input_sha256"] = "0" * 64
        content = "not JSON" if fault == "malformed" else json.dumps(reply)
        raw = json.dumps(dict(model=model, id=f"synthetic-{len(fixture.calls)}",
            choices=[dict(message=dict(content=content), finish_reason="stop")],
            usage=dict(prompt_tokens=12, completion_tokens=8,
                       cost=None if fault == "unknown_cost" else 0.000001))).encode()
        fixture.raw.append(raw)
        return raw

    core = unbudgeted_gateway(provider=Provider.OPENROUTER, model="vendor/model",
        transport=send, max_output_tokens=128)
    price = dict(catalog_sha256="synthetic", row=dict(id="vendor/model",
        pricing=dict(prompt="0.000000001", completion="0.000000001")))
    return EstimatedBudgetGateway(core, model="vendor/model", price=price,
        limit_microusd=50000, max_calls=max_calls, accounting_path=tmp_path / "budget.sqlite3"), fixture


def test_actual_bound_reply_reaches_original_parser_and_zero_send_replay(tmp_path):
    module = owner()
    accounted, provider = gateway(tmp_path)
    rows = module.run_benchmark("baseline", "vendor/model", accounted,
        output_dir=tmp_path / "current", task_ids=["retract_01_tree_clean"])
    assert len(rows) == len(provider.calls) == 1 and rows[0].matched_ground_truth
    assert rows[0].status == "HOST_ACCEPTED"
    assert base64.b64decode(rows[0].turn["provider_wire"]["raw_reply_base64"]) == provider.raw[0]
    assert json.loads(provider.calls[0].user)["input"]["prompt"] == rows[0].prompt
    assert "expected_verdict" not in rows[0].prompt
    assert rows[0].turn["request"]["max_tokens"] == 128
    assert rows[0].turn["request"]["temperature"] == 0.0
    assert "response_format" not in rows[0].turn["request"]
    report = module.replay_outputs(tmp_path / "current")
    assert report["replayed"] == 1 and len(provider.calls) == 1


@pytest.mark.parametrize("fault", ["malformed", "wrong_binding", "unknown_cost", "transport"])
def test_unchecked_or_unknown_reply_stops_without_parser_or_fallback(tmp_path, monkeypatch, fault):
    module = owner()
    accounted, provider = gateway(tmp_path, fault=fault)
    monkeypatch.setattr(module, "parse_verdict", lambda _: pytest.fail("unchecked reply reached parser"))
    rows = module.run_conditions(["baseline", "hinted"], model="vendor/model", client=accounted,
        output_dir=tmp_path / "current")
    assert len(rows) == 1 and len(provider.calls) == 1
    assert rows[0].status == "REFUSED" and not rows[0].matched_ground_truth
    summary = json.loads((tmp_path / "current/summary.json").read_text())
    assert not summary["completed"] and len(summary["unattempted"]) == 11
    assert summary["observed_models"] == []
    if fault != "transport":
        assert base64.b64decode(rows[0].turn["provider_wire"]["raw_reply_base64"]) == provider.raw[0]
    if fault in {"unknown_cost", "transport"}:
        assert rows[0].cost_usd is None and summary["total_cost_usd"] is None
        assert summary["known_cost_usd"] == 0 and summary["unknown_cost_count"] == 1
        assert rows[0].provider_attempted and summary["provider_calls"] == 1
    assert module.replay_outputs(tmp_path / "current")["replayed"] == 1


def test_conditions_share_one_continuing_call_allowance(tmp_path):
    module = owner()
    accounted, provider = gateway(tmp_path, max_calls=1)
    rows = module.run_conditions(["baseline", "scratchpad"], model="vendor/model", client=accounted,
        output_dir=tmp_path / "current", task_ids=["retract_01_tree_clean"], max_provider_calls=1)
    assert len(provider.calls) == 1 and len(rows) == 2
    assert rows[-1].status == "REFUSED"
    assert rows[-1].turn["error"] == "CALL_ALLOWANCE_EXHAUSTED"
    assert rows[-1].turn["action_record"] is None and rows[-1].turn["provider_wire"] is None
    assert not rows[-1].provider_attempted and rows[-1].cost_usd == 0.0
    summary = json.loads((tmp_path / "current/summary.json").read_text())
    assert summary["total_cost_usd"] == summary["known_cost_usd"] == 0.000001
    assert summary["unknown_cost_count"] == 0 and summary["provider_calls"] == 1
    assert module.replay_outputs(tmp_path / "current")["replayed"] == 2


def test_explicit_refused_before_dispatch_claim_requires_clean_evidence():
    module = owner()
    turn = dict(provider_wire=None, raw_body=None, usage={}, pfp=None,
        attempt_state=None, ok=False, stop=True, error="MODEL_NOT_ALLOWED",
        action_record=dict(state="refused_before_dispatch", failure_code="MODEL_NOT_ALLOWED",
            provider_attempt_id=None))
    assert module._known_no_dispatch(turn)
    turn["action_record"]["provider_attempt_id"] = "attempted"
    assert not module._known_no_dispatch(turn)
    turn["action_record"]["provider_attempt_id"] = None
    turn["action_record"]["reported_cost_usd"] = 0.000001
    assert not module._known_no_dispatch(turn)


def test_adapter_exception_without_claim_does_not_invent_dispatch_or_zero_cost(tmp_path, monkeypatch):
    module = owner()
    accounted, provider = gateway(tmp_path)

    def fail_before_claim(_):
        raise RuntimeError("synthetic adapter failure")

    monkeypatch.setattr(accounted, "for_action", fail_before_claim)
    rows = module.run_benchmark("baseline", "vendor/model", accounted,
        output_dir=tmp_path / "current", task_ids=["retract_01_tree_clean"])
    assert provider.calls == [] and not rows[0].provider_attempted
    assert rows[0].cost_usd is None and rows[0].turn["action_record"] is None
    summary = json.loads((tmp_path / "current/summary.json").read_text())
    assert summary["provider_calls"] == 0 and summary["unknown_cost_count"] == 1
    assert module.replay_outputs(tmp_path / "current")["replayed"] == 1


def test_output_preflight_does_not_require_python312_path_method(tmp_path, monkeypatch):
    monkeypatch.delattr(Path, "is_junction", raising=False)
    rows = owner().run_benchmark("exact_oracle", output_dir=tmp_path / "current",
        task_ids=["retract_01_tree_clean"])
    assert len(rows) == 1 and rows[0].matched_ground_truth


@pytest.mark.parametrize("mode,attributes", [
    (stat.S_IFDIR, stat.FILE_ATTRIBUTE_REPARSE_POINT), (stat.S_IFLNK, 0)])
def test_output_ancestor_reparse_or_symlink_refuses_before_factory(tmp_path, monkeypatch, mode, attributes):
    module = owner()
    original = Path.lstat

    def lstat(path):
        if path == tmp_path:
            return SimpleNamespace(st_mode=mode, st_file_attributes=attributes)
        return original(path)

    monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(module, "make_pilot_gateways", lambda *a, **k: pytest.fail("factory ran"))
    with pytest.raises(ValueError, match="OUTPUT_ALIAS_REFUSED"):
        module.run_conditions(["baseline"], model="vendor/model", live=True,
            output_dir=tmp_path / "current", max_estimated_cost_microusd=1000)


def test_existing_output_refuses_before_gateway_factory(tmp_path, monkeypatch):
    module = owner()
    output = tmp_path / "history"
    output.mkdir()
    (output / "summary.json").write_bytes(b"historical bytes")
    monkeypatch.setattr(module, "make_pilot_gateways", lambda *a, **k: pytest.fail("factory ran"))
    with pytest.raises(ValueError, match="OUTPUT_DIR_EXISTS"):
        module.run_conditions(["baseline"], model="vendor/model", live=True, output_dir=output,
            max_provider_calls=1, max_estimated_cost_microusd=1000)
    assert (output / "summary.json").read_bytes() == b"historical bytes"


def test_non_string_pfp_answer_never_becomes_reserialized_verdict(tmp_path, monkeypatch):
    module = owner()
    accounted, provider = gateway(tmp_path, answer={"VERDICT": "CONSISTENT"})
    monkeypatch.setattr(module, "parse_verdict", lambda _: pytest.fail("object reached original parser"))
    rows = module.run_benchmark("baseline", "vendor/model", accounted, output_dir=tmp_path / "current")
    assert len(provider.calls) == 1 and rows[0].status == "REFUSED"
    assert rows[0].turn["ok"] and rows[0].raw_content == ""
    assert module.replay_outputs(tmp_path / "current")["replayed"] == 1


def test_all_original_graphs_conditions_and_control_labels(tmp_path, monkeypatch):
    module = owner()
    rows = module.run_conditions(module.CONDITIONS, output_dir=tmp_path / "offline")
    assert len(rows) == 24 and sum(row.matched_ground_truth for row in rows) == 18
    assert all(row.turn is None and not row.provider_attempted for row in rows)
    report = json.loads((tmp_path / "offline/summary.json").read_text())
    assert report["provider_calls"] == 0 and report["observed_models"] == []
    assert report["blind_model_results"] == report["assisted_model_results"] == 0
    assert module.replay_outputs(tmp_path / "offline")["replayed"] == 24
    monkeypatch.setattr(module, "make_pilot_gateways", lambda *a, **k: pytest.fail("oracle created gateway"))
    oracle = module.run_benchmark("exact_oracle", model="requested-live-label", live=True,
        output_dir=tmp_path / "oracle")
    assert len(oracle) == 6 and all(row.matched_ground_truth for row in oracle)
    assert all(row.evidence_grade == "EXACT_ORACLE_CONTROL_NO_MODEL" for row in oracle)


def test_sealed_source_and_copied_original_judges_prompts_are_identical():
    module = owner()
    original = Path(__file__).resolve().parents[2] / (
        "omega_engine_education/documentation/004_oepfp/papers/omega_engine_symbol_game/"
        "008_pfp_mssn_tower_challenges_and_retraction_benchmarks/code/retraction_benchmark_runner.py")
    raw = original.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == module.HISTORICAL_SOURCE_SHA256
    historical, current = raw.decode(), Path(module.__file__).read_text(encoding="utf-8")
    names = {"compute_opcode_base", "GraphInstance", "BENCHMARK_INSTANCES", "exact_host_evaluate",
        "_tree_parents", "_root_path", "inconsistency_witness", "verify_inconsistency_witness",
        "verify_potential", "host_certificate", "detect_stationary_loops", "receipt_digest",
        "format_prompt", "parse_verdict"}

    def selected(source):
        result = {}
        for node in ast.parse(source).body:
            name = getattr(node, "name", None)
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                name = node.target.id
            if name in names:
                result[name] = ast.get_source_segment(source, node)
        return result

    assert selected(historical) == selected(current)
    assert set(selected(current)) == names
    for instance in module.BENCHMARK_INSTANCES:
        certificate = module.host_certificate(instance)
        if certificate["verdict"] == "CONSISTENT":
            assert module.verify_potential(instance, certificate["potential"])
            assert not module.verify_potential(instance, {key: True for key in instance.vertices})
        else:
            witness = certificate["dual_witness_walk"]
            assert module.verify_inconsistency_witness(instance, witness)
            assert not module.verify_inconsistency_witness(instance, witness[:-1])


def _rewrite_row(module, output, change):
    path = output / "receipts.jsonl"
    row = json.loads(path.read_text().splitlines()[0])
    change(row)
    row["digest_sha256"] = module.receipt_digest(row)
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    summary = json.loads((output / "summary.json").read_text())
    summary["receipts_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (output / "summary.json").write_text(json.dumps(summary), encoding="utf-8")


@pytest.mark.parametrize("part", ["raw", "request", "binding", "certificate", "status"])
def test_replay_checks_evidence_beyond_recomputed_container_digests(tmp_path, part):
    module = owner()
    accounted, provider = gateway(tmp_path)
    output = tmp_path / "current"
    module.run_benchmark("baseline", "vendor/model", accounted, output_dir=output,
        task_ids=["retract_01_tree_clean"])

    def change(row):
        if part == "raw":
            row["turn"]["provider_wire"]["raw_reply_base64"] = base64.b64encode(b"tampered").decode()
        elif part == "request":
            row["turn"]["request"]["max_tokens"] = 999
        elif part == "binding":
            row["attempt_id"] = "different-attempt"
        elif part == "certificate":
            row["host_certificate"]["potential"]["A"] = 9
        else:
            row["status"] = "HOST_REJECTED"

    _rewrite_row(module, output, change)
    with pytest.raises(ValueError, match="REPLAY_"):
        module.replay_outputs(output)
    assert len(provider.calls) == 1


def test_unknown_cost_capture_cannot_be_promoted_during_replay(tmp_path):
    module = owner()
    accounted, _ = gateway(tmp_path, fault="unknown_cost")
    output = tmp_path / "current"
    module.run_benchmark("baseline", "vendor/model", accounted, output_dir=output,
        task_ids=["retract_01_tree_clean"])

    def promote(row):
        row.update(status="HOST_ACCEPTED", raw_content="VERDICT: CONSISTENT",
            verdict_emitted="CONSISTENT", matched_ground_truth=True)
        row["turn"].update(ok=True, stop=False, content="VERDICT: CONSISTENT",
            attempt_state="CompletedSettled")

    _rewrite_row(module, output, promote)
    with pytest.raises(ValueError, match="REPLAY_REFUSAL_PROMOTED"):
        module.replay_outputs(output)


@pytest.mark.parametrize("fault", ["unknown_cost", "transport"])
def test_unsettled_send_cannot_be_relabelled_zero_cost_no_dispatch(tmp_path, fault):
    module = owner()
    accounted, _ = gateway(tmp_path, fault=fault)
    output = tmp_path / "current"
    module.run_benchmark("baseline", "vendor/model", accounted, output_dir=output,
        task_ids=["retract_01_tree_clean"])
    _rewrite_row(module, output, lambda row: row.update(provider_attempted=False, cost_usd=0.0))
    path = output / "summary.json"
    summary = json.loads(path.read_text())
    summary.update(total_cost_usd=0.0, known_cost_usd=0.0, unknown_cost_count=0, provider_calls=0)
    path.write_text(json.dumps(summary))
    with pytest.raises(ValueError, match="REPLAY_COST_OR_DISPATCH_MISMATCH"):
        module.replay_outputs(output)


@pytest.mark.parametrize("field,value", [("total_cost_usd", 0.0), ("provider_calls", 0)])
def test_replay_rechecks_accounting_summary(tmp_path, field, value):
    module = owner()
    accounted, _ = gateway(tmp_path)
    output = tmp_path / "current"
    module.run_benchmark("baseline", "vendor/model", accounted, output_dir=output,
        task_ids=["retract_01_tree_clean"])
    path = output / "summary.json"
    summary = json.loads(path.read_text())
    summary[field] = value
    path.write_text(json.dumps(summary))
    with pytest.raises(ValueError, match="REPLAY_SUMMARY_MISMATCH"):
        module.replay_outputs(output)


def test_replay_refuses_source_drift_and_historical_schema(tmp_path):
    module = owner()
    output = tmp_path / "current"
    module.run_benchmark(output_dir=output)
    path = output / "summary.json"
    summary = json.loads(path.read_text())
    summary["source_pins"]["runner"] = "0" * 64
    path.write_text(json.dumps(summary))
    with pytest.raises(ValueError, match="REPLAY_SOURCE_DRIFT"):
        module.replay_outputs(output)
    summary["schema"] = "pfp008.graph-consistency-receipt.v2"
    path.write_text(json.dumps(summary))
    with pytest.raises(ValueError, match="CURRENT_V3_REPLAY_REQUIRED"):
        module.replay_outputs(output)


def test_current_cli_offline_and_replay_are_bounded(tmp_path, capsys):
    from omega_engine_pfp.entrypoints.retraction_benchmark import main
    output = tmp_path / "current"
    assert main(["--conditions", "baseline", "hinted", "--tasks", "retract_01_tree_clean",
                 "--output-dir", str(output)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["planned"] == 2 and report["provider_calls"] == 0
    assert main(["--replay", str(output)]) == 0
    assert json.loads(capsys.readouterr().out)["replayed"] == 2


def test_partial_capture_cannot_claim_complete_in_summary(tmp_path):
    module = owner()
    accounted, provider = gateway(tmp_path, fault="unknown_cost")
    output = tmp_path / "current"
    module.run_benchmark("baseline", "vendor/model", accounted, output_dir=output)
    path = output / "summary.json"
    summary = json.loads(path.read_text())
    summary["completed"] = True
    path.write_text(json.dumps(summary))
    with pytest.raises(ValueError, match="REPLAY_SUMMARY_MISMATCH"):
        module.replay_outputs(output)
    assert len(provider.calls) == 1
