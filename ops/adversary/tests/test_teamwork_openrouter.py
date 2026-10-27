"""Practical provider parity without network calls or manufactured file edits."""

import base64
import hashlib
import json
import sys
import tempfile
from functools import lru_cache

import pytest

from operations.domain.rop.result import Err, Ok
from adversary.domain.providers.attempt import (
    AdmittedRequest,
    CompletionOutcome,
    ProviderFailure,
    RetryClass,
)
from adversary.domain.providers.types import CandidateRequest, CandidateResponse, Provider
from adversary.infrastructure import teamwork_openrouter as adapter
from adversary.infrastructure.teamwork_intelligence_host import (
    bind_acceptance,
    bind_episode_admission,
)
from adversary.infrastructure.teamwork_panel import load_panel_plan, run_syntax_prefilter_check
from adversary.use_cases.teamwork import (
    TeamworkObservation,
    next_action,
    observe,
    start_teamwork,
)
from adversary.use_cases.teamwork_pfp import check_teamwork_reply, prepare_teamwork_turn


@pytest.fixture(autouse=True)
def native_writable_temp(tmp_path, monkeypatch):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))


class Gateway:
    def __init__(self, content, *, failure=None, raw=False):
        self.content, self.failure, self.calls, self.raw = content, failure, [], raw
        self.bound_actions = []

    def for_action(self, action_id):
        self.bound_actions.append(action_id)
        return self

    def complete_result(self, request, **kwargs):
        self.calls.append((request, kwargs))
        if self.failure is not None:
            return Err(self.failure)
        sequence = len(self.calls)
        admitted = AdmittedRequest(f"attempt-{sequence}", "", "sha256:request", Provider.OPENROUTER,
            "vendor/model", request, 512, None, None)
        content = self.content
        if not self.raw:
            public, _end = json.JSONDecoder().raw_decode(request.user)
            answer = json.loads(content) if content.lstrip().startswith("{") else content
            content = json.dumps({key: public[key] for key in ("task_id", "attempt_id", "input_sha256")}
                | {"answer": answer})
        candidate = CandidateResponse(content, "vendor/model", "openrouter",
            input_tokens=20, output_tokens=10, generation_id=f"generation-{sequence}", transport="synthetic-unit")
        wire = json.dumps({"choices": [{"message": {"content": content}}],
            "model": candidate.model, "usage": {"prompt_tokens": 20, "completion_tokens": 10}}).encode()
        return Ok(CompletionOutcome(candidate, admitted, reply_bytes=wire))


class OfflineFixtureOpenRouterTeamworkExecutor(adapter.OpenRouterTeamworkExecutor):
    """Test-only PFP seam with explicit synthetic replies; no provider is acquired."""

    def __call__(self, pending):
        if pending.communication != "pfp":
            return super().__call__(pending)
        return self._execute_action(pending)


def test_public_direct_executor_refuses_real_unbudgeted_transport_before_dispatch():
    from adversary.infrastructure.providers.gateway import unbudgeted_gateway

    calls = []
    provider = unbudgeted_gateway(provider=Provider.OPENROUTER, model="vendor/model",
        transport=lambda *args: calls.append(args) or b"must never send", max_output_tokens=64)
    with pytest.raises(ValueError, match="ADVERSARY_RUN_BUDGET_REQUIRED"):
        adapter.OpenRouterTeamworkExecutor(provider, "vendor/model")(action())
    assert calls == []


@pytest.mark.parametrize("mutated", ["run", "objective", "ledger"])
def test_public_direct_executor_requires_actual_original_durable_scope(tmp_path, mutated):
    from pfp.tests.test_estimated_gateway import actual_gateway

    gateway, calls = actual_gateway(tmp_path)
    pending = action().model_copy(update={"run_id": "objective-a", "objective": "one original objective"})
    if mutated == "run":
        pending = pending.model_copy(update={"run_id": "another-run"})
    elif mutated == "objective":
        pending = pending.model_copy(update={"objective": "Changed original objective"})
    else:
        gateway.path.unlink()
    if mutated == "ledger":
        with pytest.raises(FileNotFoundError):
            adapter.OpenRouterTeamworkExecutor(gateway, "vendor/model")(pending)
    else:
        with pytest.raises(ValueError, match="DURABLE_RUN_SCOPE_MISMATCH"):
            adapter.OpenRouterTeamworkExecutor(gateway, "vendor/model")(pending)
    assert calls == []


def test_public_direct_executor_rejects_fake_budget_policy_flags():
    gateway = Gateway("must not be sent")
    gateway.binding = dict(schema="pfp.fuzzy-run.v1", limit_microusd=50000,
                           run_id="provider-unit-fixture", objective_sha256="a" * 64)
    with pytest.raises(ValueError, match="ADVERSARY_RUN_BUDGET_REQUIRED"):
        adapter.OpenRouterTeamworkExecutor(gateway, "vendor/model")(action())
    assert gateway.calls == [] and gateway.bound_actions == []


@lru_cache(maxsize=3)
def action(kind="build"):
    """Reach a v3 role with bound acceptance and raw checked fixture replies."""
    run = start_teamwork("write a function", run_id="provider-unit-fixture", panel_plan=load_panel_plan(),
        acceptance_check=bind_acceptance("provider.fixture.v1", (sys.executable, "-c", "raise SystemExit(0)")))
    run = observe(run, run_syntax_prefilter_check(next_action(run)))
    while (pending := next_action(run)) is not None:
        if pending.kind == kind and (kind != "review" or pending.phase == "review"):
            return pending
        answer = "def broken(): pass" if pending.kind == "build" else {
            "summary": "Concrete fixture role review",
            "findings": ["missing return"] if pending.role_id == "scope_guard" else []}
        turn = prepare_teamwork_turn(pending)
        raw = json.dumps({**{key: turn.binding[key] for key in (
            "task_id", "attempt_id", "input_sha256")}, "answer": answer}).encode()
        run = observe(run, check_teamwork_reply(pending, turn, raw, worker="offline fixture"))
    raise AssertionError(f"No fixture action of kind {kind}")


def test_build_preserves_exact_reply_and_reports_no_host_execution():
    gateway = Gateway("def answer(): return 42")
    observed = OfflineFixtureOpenRouterTeamworkExecutor(gateway, "vendor/model")(action())
    assert observed.content == "def answer(): return 42"
    assert gateway.bound_actions == [action().action_id + ":0"]
    assert observed.artifacts == {} and not observed.blocked
    assert observed.worker == "openrouter:vendor/model"
    assert observed.metadata["host_tools_executed"] is False
    assert observed.metadata["cost_usd"] is None
    assert observed.metadata["attempt_id"] == "attempt-1"
    raw = base64.b64decode(observed.metadata["raw_reply_base64"])
    completion = json.loads(raw)["choices"][0]["message"]["content"]
    assert json.loads(completion)["answer"] == observed.content
    assert observed.metadata["raw_reply_sha256"] == hashlib.sha256(raw).hexdigest()
    request, kwargs = gateway.calls[0]
    assert isinstance(request, CandidateRequest)
    assert kwargs == {"provider": Provider.OPENROUTER, "model": "vendor/model"}
    assert request.decoding.allow_fallbacks is False
    assert "missing return" in request.user


def test_review_retains_concrete_findings_after_pfp_check():
    gateway = Gateway('{"summary":"One issue", "findings":["missing return"]}')
    observed = OfflineFixtureOpenRouterTeamworkExecutor(gateway, "vendor/model")(action("review"))
    assert observed.summary == "One issue"
    assert observed.findings == ("missing return",)
    assert observed.content == "" and not observed.blocked


def test_learning_proposes_metadata_without_overwriting_original_file(tmp_path):
    from adversary.infrastructure.teamwork_file_host import file_text_executor

    output = tmp_path / "artifact.txt"
    from adversary.tests.test_teamwork_ddc_host import stored

    learning_run, _, _, _ = stored(tmp_path)
    learning_action = next_action(learning_run)
    gateway = Gateway("original artifact")
    host = file_text_executor(OfflineFixtureOpenRouterTeamworkExecutor(gateway, "vendor/model"), output)
    assert not host(action()).blocked
    gateway.content = json.dumps({"summary": "Proposed correction", "findings": ["Owner improvement"],
        "lessons": ["Reuse the existing owner"],
        "consumed_ddc_root": learning_action.ddc_program.binding.semantic_ddc_root,
        "consumed_procedure_sha256": learning_action.ddc_program.procedure_sha256})
    learned = host(learning_action)
    assert not learned.blocked and learned.content == "" and learned.findings == ("Owner improvement",)
    assert learned.metadata["proposed_only"] is True
    assert learned.metadata["installed_changes"] is False
    assert learned.metadata["lessons"] == ["Reuse the existing owner"]
    assert output.read_text() == "original artifact"
    gateway.content = "{}"
    malformed = host(learning_action)
    assert malformed.blocked and malformed.metadata["failure_code"] == "MALFORMED_LEARNING"


@pytest.mark.parametrize("reply", ["looks good", "{}", '{"summary":"ok","findings":"none"}',
    '{"summary":"ok","findings":[42]}', '{"summary":"","findings":[]}',
    '```json\n{"summary":"ok","findings":[]}\n```'])
def test_malformed_review_is_blocked_instead_of_clean_approval(reply):
    observed = OfflineFixtureOpenRouterTeamworkExecutor(Gateway(reply), "vendor/model")(action("review"))
    assert observed.blocked
    assert observed.metadata["failure_code"] == "MALFORMED_REVIEW"
    assert observed.metadata["raw_reply_base64"]


def test_ambiguous_provider_failure_never_retries_or_changes_model():
    failure = ProviderFailure("PROVIDER_TRANSPORT_OUTCOME_UNKNOWN", "provider.completion",
        RetryClass.OUTCOME_UNKNOWN, "attempt-unknown")
    gateway = Gateway("", failure=failure)
    observed = OfflineFixtureOpenRouterTeamworkExecutor(gateway, "vendor/model")(action())
    assert observed.blocked and len(gateway.calls) == 1
    assert observed.metadata["attempt_id"] == "attempt-unknown"
    assert observed.metadata["retry"] == "outcome_unknown"


@pytest.mark.parametrize("options", [{}, {"max_cost_microusd": 100, "allow_unbounded_cost": True},
    {"max_cost_microusd": 0}, {"max_cost_microusd": True}, {"max_cost_microusd": 50_001},
    {"max_estimated_cost_microusd": 50_001},
    {"max_cost_microusd": 10, "max_estimated_cost_microusd": 10}])
def test_factory_requires_one_explicit_financial_policy_before_credentials(monkeypatch, tmp_path, options):
    monkeypatch.setattr(adapter, "create_accounted_openrouter_gateway",
        lambda *a, **kw: pytest.fail("gateway constructed before admission"))
    with pytest.raises(ValueError):
        adapter.create_openrouter_executor("vendor/model", 512, accounting_path=tmp_path / "run.sqlite3",
            run_id="one-run", objective_sha256="a" * 64, **options)


@pytest.mark.parametrize("missing", ["accounting_path", "run_id", "objective_sha256"])
def test_factory_refuses_missing_durable_run_bindings(monkeypatch, tmp_path, missing):
    monkeypatch.setattr(adapter, "create_accounted_openrouter_gateway",
        lambda *a, **kw: pytest.fail("gateway constructed without durable custody"))
    bindings = {"accounting_path": tmp_path / "run.sqlite3", "run_id": "one-run", "objective_sha256": "a" * 64}
    bindings.pop(missing)
    with pytest.raises(ValueError, match="ADVERSARY_RUN_BUDGET_REQUIRED"):
        adapter.create_openrouter_executor("vendor/model", 512, max_estimated_cost_microusd=50_000, **bindings)


def test_factory_explicit_estimate_binds_one_durable_run_without_fallback(monkeypatch, tmp_path):
    calls = []
    gateway = Gateway("candidate")

    def factory(*args, **kwargs):
        calls.append((args, kwargs))
        return gateway

    monkeypatch.setattr(adapter, "create_accounted_openrouter_gateway", factory)
    path = tmp_path / "durable.sqlite3"
    executor = adapter.create_openrouter_executor("vendor/model", 512,
        max_estimated_cost_microusd=50_000, accounting_path=path,
        run_id="one-run", objective_sha256="a" * 64)
    assert executor.gateway is gateway
    assert calls == [(('vendor/model', 512), {
        "env_file": None, "max_cost_microusd": None, "allow_unbounded_cost": False,
        "max_estimated_cost_microusd": 50_000, "max_calls": 42,
        "accounting_path": path, "run_id": "one-run", "objective_sha256": "a" * 64})]


def test_factory_bounded_keeps_existing_gateway_enforcement(monkeypatch, tmp_path):
    calls = []
    failure = ProviderFailure("BUDGET_ENFORCEMENT_UNAVAILABLE", "provider.completion", RetryClass.TERMINAL)
    gateway = Gateway("", failure=failure)
    monkeypatch.setattr(adapter, "create_accounted_openrouter_gateway",
        lambda *args, **kw: calls.append(kw) or gateway)
    executor = adapter.create_openrouter_executor("vendor/model", 512, max_cost_microusd=100,
        accounting_path=tmp_path / "hard.sqlite3", run_id="hard-run", objective_sha256="b" * 64)
    observed = OfflineFixtureOpenRouterTeamworkExecutor(executor.gateway, executor.model)(action())
    assert observed.blocked and observed.metadata["failure_code"] == "BUDGET_ENFORCEMENT_UNAVAILABLE"
    assert calls[0]["max_calls"] == 32
    assert calls[0]["max_cost_microusd"] == 100
    assert calls[0]["max_estimated_cost_microusd"] is None
    assert calls[0]["allow_unbounded_cost"] is False


def test_file_host_runs_full_roster_before_and_after_actual_candidate_application(tmp_path):
    from adversary.infrastructure.teamwork_file_host import file_text_executor
    from adversary.infrastructure.teamwork_panel import create_teamwork_run
    from adversary.use_cases.teamwork import drive_teamwork

    class PanelGateway(Gateway):
        def complete_result(self, request, **kwargs):
            public, _end = json.JSONDecoder().raw_decode(request.user)
            pending = public["input"]["context"]
            if pending["kind"] == "build":
                assert not output.exists()
                self.content = "Actual provider-proposed artifact"
            elif pending["kind"] == "learn":
                program = pending["ddc_program"]
                self.content = json.dumps({"summary": "A proposed lesson", "findings": [], "lessons": [],
                    "consumed_ddc_root": program["binding"]["semantic_ddc_root"],
                    "consumed_procedure_sha256": hashlib.sha256(json.dumps(program["binding"],
                        sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()})
            else:
                if pending["phase"] == "intake":
                    assert not output.exists()
                else:
                    assert output.read_text() == "Actual provider-proposed artifact"
                self.content = '{"summary":"Concrete role review","findings":[]}'
            return super().complete_result(request, **kwargs)

    output = tmp_path / "actual.txt"
    gateway = PanelGateway("")
    run = create_teamwork_run("Write one artifact", executor="openrouter",
        acceptance_check=bind_acceptance("artifact.exists.v1", (sys.executable, "-c",
            "from pathlib import Path; import sys; raise SystemExit(not Path(sys.argv[1]).is_file())", str(output))))
    run = run.model_copy(update={"episode_binding": bind_episode_admission(run, tmp_path / "episodes.sqlite3")})
    current = [run]
    executor = file_text_executor(OfflineFixtureOpenRouterTeamworkExecutor(gateway, "vendor/model"), output,
        run_reader=lambda: current[0], ddc_output_dir=tmp_path / "native")
    completed = drive_teamwork(run, executor, checkpoint=lambda updated: current.__setitem__(0, updated))
    assert completed.work_status == "completed" and completed.panel_coverage["complete"]
    model_roles = [item.metadata["role_id"] for item in completed.observations
                   if item.metadata.get("execution_kind") == "pfp"]
    required_model_roles = [step.role_id for step in run.panel_plan.steps
                            if step.communication == "pfp"]
    assert model_roles == [*required_model_roles, "defect_hunter"]
    assert len(gateway.calls) == len(model_roles) == 22
    attempts = [item.metadata["attempt_id"] for item in completed.observations
                if item.metadata.get("execution_kind") == "pfp"]
    assert len(set(attempts)) == len(attempts)
    assert [item.metadata["role_id"] for item in completed.observations
            if item.metadata.get("execution_kind") == "host"] == [
        "host_native_gates", "host_native_gates", "host_acceptance", "host_native_gates",
        "host_ddc_store", "host_native_gates", "host_acceptance", "host_native_gates",
        "host_digestion", "host_ddc_complete"]
    build = next(item for item in completed.observations if item.metadata.get("role_id") == "bare_metal_anchor")
    assert output.read_text() == build.content == "Actual provider-proposed artifact"
    assert build.summary == "PFP-checked proposal; task correctness remains unverified."
    assert build.metadata["host_summary"] == "Python file host wrote the provider's proposed artifact text."
    assert build.metadata["host_tools_executed"] is False
    assert completed.evidence_verdict == "OPEN_RESIDUAL"


def test_existing_output_blocks_before_any_model_dispatch(tmp_path):
    from adversary.infrastructure.teamwork_file_host import file_text_executor

    output = tmp_path / "existing.txt"
    output.write_text("Preserve the original")
    gateway = Gateway("must not be called")
    executor = file_text_executor(OfflineFixtureOpenRouterTeamworkExecutor(gateway, "vendor/model"), output)
    run = start_teamwork("Write one artifact", executor="openrouter", panel_plan=load_panel_plan(),
        acceptance_check=bind_acceptance("fixture.v1", (sys.executable, "-c", "raise SystemExit(0)")))
    result = executor(next_action(run))
    assert result.blocked and result.metadata["failure_code"] == "OUTPUT_EXISTS"
    assert result.metadata["role_id"] == "syntax_prefilter" and not gateway.calls
    assert output.read_text() == "Preserve the original"


def test_file_host_rechecks_candidate_bytes_before_provider_review(tmp_path):
    from adversary.infrastructure.teamwork_file_host import file_text_executor

    output = tmp_path / "actual.txt"
    gateway = Gateway("original")
    executor = file_text_executor(OfflineFixtureOpenRouterTeamworkExecutor(gateway, "vendor/model"), output)
    assert not executor(action()).blocked
    calls = len(gateway.calls)
    output.write_text("changed by another writer")
    result = executor(action("review"))
    assert result.blocked and result.metadata["failure_code"] == "ARTIFACT_CHANGED"
    assert result.metadata["role_id"] == "defect_hunter" and len(gateway.calls) == calls


def test_file_host_rechecks_candidate_changed_during_provider_review(tmp_path):
    from adversary.infrastructure.teamwork_file_host import file_text_executor

    output = tmp_path / "actual.txt"

    class ConcurrentWriterGateway(Gateway):
        def complete_result(self, request, **kwargs):
            if self.calls:
                output.write_text("changed during the provider call")
            return super().complete_result(request, **kwargs)

    gateway = ConcurrentWriterGateway("original")
    executor = file_text_executor(OfflineFixtureOpenRouterTeamworkExecutor(gateway, "vendor/model"), output)
    assert not executor(action()).blocked
    gateway.content = '{"summary":"Claimed clear review","findings":[]}'
    result = executor(action("review"))
    assert result.blocked and result.metadata["failure_code"] == "ARTIFACT_CHANGED"
    assert output.read_text() == "changed during the provider call"


@pytest.mark.parametrize("forged_verdict", [False, True])
def test_file_host_rejects_unmediated_callback_before_creating_artifact(tmp_path, forged_verdict):
    from adversary.infrastructure.teamwork_file_host import file_text_executor

    output = tmp_path / "must-not-exist" / "candidate.txt"

    def unchecked(pending):
        metadata = {"role_id": pending.role_id}
        if forged_verdict:
            metadata.update(pfp={"schema_valid": True, "status": "HOST_ACCEPTED"})
        return TeamworkObservation(action_id=pending.action_id, worker="injected callback",
            summary="Claimed proposal", content="Unmediated model text", metadata=metadata)

    with pytest.raises(ValueError, match="PFP_"):
        file_text_executor(unchecked, output)(action())
    assert not output.exists() and not output.parent.exists()


def test_file_host_validates_checked_content_before_overwriting_existing_candidate(tmp_path):
    from adversary.infrastructure.teamwork_file_host import file_text_executor

    output = tmp_path / "candidate.txt"
    output.write_text("preserve exact bytes")
    before = output.read_bytes()
    pending = action().model_copy(update={"kind": "repair", "role_id": "primal_dual", "phase": "repair"})

    def forged_repair(action):
        gateway = Gateway("A checked proposal")
        observed = OfflineFixtureOpenRouterTeamworkExecutor(gateway, "vendor/model")(action)
        return observed.model_copy(update={"content": "Unbound replacement text"})

    executor = file_text_executor(forged_repair, output,
                                 expected_artifact_sha256=hashlib.sha256(before).hexdigest())
    with pytest.raises(ValueError, match="PFP_OBSERVATION_MISMATCH"):
        executor(pending)
    assert output.read_bytes() == before
