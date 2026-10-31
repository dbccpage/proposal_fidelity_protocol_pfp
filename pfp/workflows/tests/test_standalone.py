"""Standalone CLI, resource and budget controls. Replies are scripted fixtures only."""

import importlib
import json
import sys
from pathlib import Path

import pytest

from adversary.infrastructure.providers.rust_budget import NativeBudgetUnavailable, RustBudgetRuntime
from pfp.infrastructure import workflow_accounting
from pfp.infrastructure.workflow_runtime import source_bytes
from pfp.workflows.tests.fixtures import SPEC
from pfp.workflows.tests.gateways import make_gateway


def test_real_provider_composition_accepts_injected_wire_without_native_backend(tmp_path, monkeypatch):
    from operations.domain.rop.result import Ok
    from pfp.infrastructure import estimated_gateway
    from pfp.workflows.wf0001.runner import runtime
    from pfp.workflows.wf0001 import workflow
    model = "meta-llama/llama-3.3-70b-instruct"
    calls = []

    def wire(provider, selected, request):
        calls.append(request)
        public = json.loads(request.user)
        reply = {key: public[key] for key in ("task_id", "attempt_id", "input_sha256")}
        reply["answer"] = {"total": 38}
        return json.dumps({"id": "fixture-wire-one", "model": selected,
                           "choices": [{"message": {"content": json.dumps(reply)}, "finish_reason": "stop"}],
                           "usage": {"prompt_tokens": 10, "completion_tokens": 8, "cost": .000001}}).encode()

    monkeypatch.setattr(estimated_gateway, "resolve_openrouter_key", lambda path: Ok("fixture-only-secret"))
    monkeypatch.setattr(estimated_gateway, "snapshot_pricing", lambda *args, **kwargs: {
        "catalog_sha256": "fixture-rates", "row": {"id": model,
        "pricing": {"prompt": "0.0000001", "completion": "0.00000032"}}})
    task = json.loads(workflow.resource_text("examples/integer_sum.task.json"))
    root = tmp_path / "wire-run"
    runtime.prepare_run(task, root)
    gateway = workflow_accounting.create_accounted_openrouter_gateway(
        model, 256, transport=wire, max_estimated_cost_microusd=4999, max_calls=1,
        accounting_path=root / "accounting.sqlite3", run_id="wire-fixture",
        objective_sha256=workflow.prepare_task(task).binding["input_sha256"])
    checked = runtime.run_accounted(task, root, gateway=gateway, model=model, max_output_tokens=256)
    assert checked["status"] == "HOST_ACCEPTED" and len(calls) == 1
    assert checked["provider"]["accounting_state"] == "CompletedSettled"
    assert runtime.replay_run(root)["replay_verified"] is True


def test_gateway_composition_keeps_settled_cost_and_exhausted_call_allowance(tmp_path, monkeypatch):
    from adversary.domain.providers.types import CandidateRequest, Provider
    original, provider = make_gateway(tmp_path, max_calls=1, raw_content="fixture")
    request = CandidateRequest("s", json.dumps({"task_id": "fixture", "attempt_id": "one", "input_sha256": "fixture"}))
    original.for_action("spent").complete_result(request,
                                                provider=Provider.OPENROUTER, model=original.model)
    monkeypatch.setattr(workflow_accounting, "canonical_gateway", lambda *args, **kwargs: original)
    resumed = workflow_accounting.create_accounted_openrouter_gateway(
        original.model, 256, accounting_path=tmp_path / "budget.sqlite3")
    assert resumed.scope == original.scope and resumed.limit == 4999
    with resumed.ledger.transaction(resumed.limit) as state:
        assert state["spent"] == 1 and len(state["attempts"]) == 1
    rejected = resumed.for_action("next").complete_result(request,
                                                         provider=Provider.OPENROUTER, model=original.model)
    assert rejected.error.code == "CALL_ALLOWANCE_EXHAUSTED" and len(provider.calls) == 1


@pytest.mark.parametrize("number", [1, 2, 3, 4, 5])
def test_cli_runs_accounted_pipeline_and_readonly_replay(tmp_path, monkeypatch, number, capsys):
    runner = importlib.import_module(f"pfp.workflows.wf{number:04}.runner")
    calls = []
    if number < 3:
        workflow = runner.workflow
        task = json.loads(workflow.resource_text("examples/integer_sum.task.json"))
        if number == 2:
            from pfp.workflows.wf0002.tests.test_wf0002 import candidate
            answer = candidate()
        else:
            answer = {"total": 38}

        def provider_factory(root, model, tokens):
            bound, provider = make_gateway(root, model=model, max_calls=1, answer=answer,
                                           max_output_tokens=tokens)
            calls.append(provider)
            return bound
    elif number == 3:
        from pfp.workflows.wf0003.tests.test_wf0003 import factory_for
        task = json.loads(runner.workflow.resource_text("examples/integer_sum.task.json"))
        provider_factory = factory_for(calls)
    elif number == 4:
        from pfp.workflows.wf0004.tests.test_wf0004 import scripted_factory
        task, provider_factory = SPEC, scripted_factory(calls)
    else:
        from pfp.workflows.wf0005.tests.test_wf0005 import factory_for
        task, provider_factory = SPEC, factory_for(calls)

    def accounted(model, tokens, **options):
        return provider_factory(Path(options["accounting_path"]).parent, model, tokens)

    if number < 3:
        monkeypatch.setattr(workflow_accounting, "create_accounted_openrouter_gateway", accounted)
    else:
        monkeypatch.setattr(runner, "create_accounted_openrouter_gateway", accounted)
    task_path, output = tmp_path / "task.json", tmp_path / "run"
    task_path.write_text(json.dumps(task), encoding="utf-8")
    if number < 3:
        args = ["run", str(task_path), "--output", str(output), "--model",
                "meta-llama/llama-3.3-70b-instruct", "--max-output-tokens", "256",
                "--max-estimated-cost-microusd", "4999"]
        replay = ["replay", str(output)]
    elif number == 3:
        args = ["run", str(task_path), "--output", str(output), "--model",
                "meta-llama/llama-3.3-70b-instruct", "--budget-microusd", "4999"]
        replay = ["replay", str(output)]
    else:
        args = ["run", "--task", str(task_path), "--output", str(output),
                "--budget-microusd", "4999"]
        replay = ["replay", "--run", str(output)]
    assert runner.main(args) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "HOST_ACCEPTED"
    before = {p.relative_to(output).as_posix(): p.read_bytes() for p in output.rglob("*") if p.is_file()}
    assert runner.main(replay) == 0
    assert json.loads(capsys.readouterr().out)["replay_verified"] is True
    assert before == {p.relative_to(output).as_posix(): p.read_bytes() for p in output.rglob("*") if p.is_file()}
    assert len(calls) == [1, 1, 2, 6, 6][number - 1]


@pytest.mark.parametrize("number", [1, 2])
@pytest.mark.parametrize("cap", [0, -1, 5000, 50000])
def test_single_call_cli_refuses_budget_increase_before_preparation(tmp_path, number, cap):
    runner = importlib.import_module(f"pfp.workflows.wf{number:04}.runner")
    output = tmp_path / "refused"
    assert runner.main(["run", str(tmp_path / "not-read.json"), "--output", str(output),
                        "--model", "meta-llama/llama-3.3-70b-instruct",
                        "--max-output-tokens", "256", "--max-estimated-cost-microusd", str(cap)]) == 2
    assert not output.exists()


@pytest.mark.parametrize("path", ["pfp/../secret", "C:/secret", "pfp/", "unknown/foo", "pfp/../../x"])
def test_source_resource_resolver_refuses_escaping_paths(path):
    with pytest.raises(ValueError, match="WORKFLOW_SOURCE_PATH_INVALID"):
        source_bytes(path)


def test_resource_identity_uses_installed_package_not_current_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert b"class PfpTaskPrompt" in source_bytes("pfp/domain/contracts/pfp_runtime.py")
    assert b"class SqliteBudgetLedger" in source_bytes("adversary/infrastructure/providers/budget_ledger.py")


def test_missing_optional_native_budget_is_a_typed_refusal(monkeypatch):
    monkeypatch.setitem(sys.modules, "operating_system", None)
    runtime = RustBudgetRuntime()
    assert runtime.utc_now().endswith("Z")
    with pytest.raises(NativeBudgetUnavailable, match="NATIVE_BUDGET_UNAVAILABLE"):
        runtime.invoke("state")
