"""Run-wide hard accounting with native arithmetic and synthetic provider wires.

The transport's maximum liability is a fixture contract, never a vendor claim.
No external calls or live billing are used.
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256

import pytest

from operations.domain.rop.result import Err, Ok
from pfp.infrastructure.estimated_gateway import DurableRunGateway
from adversary.domain.providers.allowlist import ModelAllowlist
from adversary.domain.providers.attempt import TransportFailure
from adversary.domain.providers.budget import BudgetController, GatewayPolicy, PriceTable
from adversary.domain.providers.types import CandidateRequest, Provider, ProviderError
from adversary.infrastructure.providers.gateway import OearsLlmGateway
from adversary.infrastructure.providers.openai_compat import OpenAiCompatTransport

MODEL = "openai/gpt-4o-mini"
OTHER_MODEL = "deepseek/deepseek-v4-flash"
OBJECTIVE = sha256(b"Nontrivial original task shared by every role").hexdigest()
AT = "2026-10-12T12:00:00.000000Z"


class SyntheticTransport:
    provenance = "synthetic-durable-run"

    def __init__(self, *, liability=10_000, cost="0.001", failure=None, malformed=False):
        self.liability, self.cost = liability, cost
        self.failure, self.malformed = failure, malformed
        self.calls = []

    def maximum_liability(self, *args):
        return self.liability

    def dispatch(self, admitted):
        self.calls.append(admitted)
        if self.failure is not None:
            raise self.failure
        if self.malformed:
            return b'{"choices":invalid}'
        usage = dict(prompt_tokens=8, completion_tokens=4)
        if self.cost is not None:
            usage["cost"] = self.cost
        return json.dumps(dict(id="generation-" + admitted.attempt_id,
            model=admitted.model, choices=[dict(message=dict(content="Actual synthetic reply"))],
            usage=usage)).encode()


def bind(tmp_path, transport=None, *, limit=50_000, max_calls=8, run_id="run-a", objective=OBJECTIVE):
    transport = transport or SyntheticTransport()
    gateway = OearsLlmGateway(ModelAllowlist.builtin(),
        GatewayPolicy(PriceTable.builtin(), BudgetController(limit), 20, pricing_clock=lambda: AT),
        transport, Provider.OPENROUTER, MODEL)
    return DurableRunGateway(gateway, accounting_path=tmp_path / "run.sqlite3",
        run_id=run_id, objective_sha256=objective, max_calls=max_calls), transport


def send(bound, action, *, model=MODEL, user="Solve the original task"):
    return bound.for_action(action).complete_result(CandidateRequest("System", user),
        provider=Provider.OPENROUTER, model=model)


def generation_payload(bound, action, cost="0.001"):
    return {"data": {"id": bound.action(action)["generation_id"], "total_cost": cost}}


def test_worker_review_repair_learn_and_model_switch_share_one_fifty_millidollar_limit(tmp_path):
    bound, transport = bind(tmp_path)
    roles = ("worker:0", "review:0", "repair:0", "review:1", "learn:0")
    for number, role in enumerate(roles):
        result = send(bound, role, model=MODEL if number % 2 == 0 else OTHER_MODEL)
        assert isinstance(result, Ok)
        assert result.value.admitted.receipt.spent_after_microusd == (number + 1) * 10_000
    refused = send(bound, "extra-role:0")
    assert isinstance(refused, Err) and refused.error.code == "BUDGET_EXCEEDED"
    assert len(transport.calls) == 5 and bound.budget.spent_microusd == 50_000


def test_restart_retains_holds_and_action_claims_without_resending(tmp_path):
    bound, transport = bind(tmp_path)
    assert isinstance(send(bound, "worker:0"), Ok)
    restarted, new_transport = bind(tmp_path)
    assert restarted.budget.spent_microusd == 10_000
    assert send(restarted, "worker:0").error.code == "PFP_ACTION_ALREADY_CLAIMED"
    assert send(restarted, "worker:0", user="Changed objective").error.code == "PFP_ACTION_BINDING_MISMATCH"
    assert isinstance(send(restarted, "review:0"), Ok)
    assert len(transport.calls) == 1 and len(new_transport.calls) == 1
    assert restarted.budget.spent_microusd == 20_000


def test_wrapping_an_already_charged_memory_gateway_cannot_reset_spend(tmp_path):
    transport = SyntheticTransport()
    gateway = OearsLlmGateway(ModelAllowlist.builtin(),
        GatewayPolicy(PriceTable.builtin(), BudgetController(50_000), 20, pricing_clock=lambda: AT),
        transport, Provider.OPENROUTER, MODEL)
    assert isinstance(gateway.complete_result(CandidateRequest("System", "Task")), Ok)
    assert gateway.policy.budget.spent_microusd == 10_000
    with pytest.raises(ValueError, match="DURABLE_BUDGET_ALREADY_USED"):
        DurableRunGateway(gateway, accounting_path=tmp_path / "run.sqlite3",
            run_id="run-a", objective_sha256=OBJECTIVE)
    assert not (tmp_path / "run.sqlite3").exists()
    assert gateway.policy.budget.spent_microusd == 10_000


def test_binding_exposes_the_exact_persistable_run_and_accounting_path(tmp_path):
    bound, _ = bind(tmp_path)
    assert bound.binding == dict(schema="pfp.hard-run.v1", run_id="run-a",
        objective_sha256=OBJECTIVE, limit_microusd=50_000, max_calls=8,
        accounting_path=str((tmp_path / "run.sqlite3").resolve()))
    returned = bound.binding
    returned["limit_microusd"] = 100_000
    assert bound.binding["limit_microusd"] == 50_000


def test_existing_ledger_inspection_and_reopening_release_windows_file_handles(tmp_path):
    import gc

    from pfp.infrastructure.estimated_gateway import DurableRunGateway

    enabled = gc.isenabled()
    gc.disable()  # Connection ownership must not rely on eventual cyclic GC.
    try:
        bound, _ = bind(tmp_path)
        assert isinstance(send(bound, "worker:release"), Ok)
        path = tmp_path / "run.sqlite3"
        assert DurableRunGateway.read_binding(path) == bound.binding
        assert DurableRunGateway.read_action(path, "worker:release")["wire_bytes"] > 0
        assert DurableRunGateway.read_raw_reply(path, "worker:release")
        reopened, _ = bind(tmp_path)
        assert reopened.binding == bound.binding
        path.unlink()  # Fails immediately on Windows if any reader still owns a handle.
        assert not path.exists()
    finally:
        if enabled:
            gc.enable()


@pytest.mark.parametrize("changed", [
    {"run_id": "different-run"}, {"objective": "f" * 64}, {"limit": 40_000}, {"max_calls": 9},
])
def test_existing_allowance_cannot_reset_by_changing_run_scope(tmp_path, changed):
    bound, _ = bind(tmp_path)
    send(bound, "worker:0")
    with pytest.raises(ValueError, match="SCOPE|limit"):
        bind(tmp_path, **changed)
    assert bound.budget.spent_microusd == 10_000


def test_same_action_has_only_one_atomic_claim_under_concurrency(tmp_path):
    bound, transport = bind(tmp_path)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: send(bound, "worker:0"), range(8)))
    assert sum(isinstance(result, Ok) for result in results) == 1
    assert all(isinstance(result, Ok) or result.error.code == "PFP_ACTION_ALREADY_CLAIMED"
        for result in results)
    assert len(transport.calls) == 1 and bound.budget.spent_microusd == 10_000


def test_raw_wire_is_durable_before_provider_decode_and_host_return(tmp_path):
    bound, transport = bind(tmp_path, SyntheticTransport(malformed=True))
    refused = send(bound, "worker:0")
    assert isinstance(refused, Err)
    assert bound.raw_reply("worker:0") == b'{"choices":invalid}'
    assert bound.action("worker:0")["state"] == "outcome_unknown"
    assert send(bound, "review:0").error.code == "RUN_RECONCILIATION_REQUIRED"
    assert len(transport.calls) == 1 and bound.budget.spent_microusd == 10_000


def test_wire_custody_detects_tampering_without_resend(tmp_path):
    bound, transport = bind(tmp_path)
    send(bound, "worker:0")
    path = bound.reply_root / bound.action("worker:0")["wire_file"]
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="DURABLE_WIRE_MISMATCH"):
        bound.raw_reply("worker:0")
    assert send(bound, "worker:0").error.code == "PFP_ACTION_ALREADY_CLAIMED"
    assert len(transport.calls) == 1


def test_wire_metadata_cannot_redirect_reader_to_another_file(tmp_path):
    bound, _ = bind(tmp_path)
    send(bound, "worker:0")
    with bound.ledger.transaction(50_000) as state:
        state["action_claims"]["worker:0"]["wire_file"] = "../../different-file"
    with pytest.raises(ValueError, match="DURABLE_WIRE_MISMATCH"):
        bound.raw_reply("worker:0")


@pytest.mark.parametrize("failure", [TransportFailure("PROVIDER_TRANSPORT_OUTCOME_UNKNOWN"), KeyboardInterrupt()])
def test_unknown_send_or_cancellation_keeps_hold_and_stops_restarted_run(tmp_path, failure):
    bound, transport = bind(tmp_path, SyntheticTransport(failure=failure))
    if isinstance(failure, KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            send(bound, "worker:0")
    else:
        assert isinstance(send(bound, "worker:0"), Err)
    restarted, new_transport = bind(tmp_path)
    assert restarted.budget.spent_microusd == 10_000
    assert send(restarted, "review:0").error.code == "RUN_RECONCILIATION_REQUIRED"
    assert send(restarted, "worker:0").error.code == "PFP_ACTION_ALREADY_CLAIMED"
    assert len(transport.calls) == 1 and not new_transport.calls


def test_missing_cost_keeps_exact_reply_and_can_only_release_hold_via_generation_receipt(tmp_path):
    bound, transport = bind(tmp_path, SyntheticTransport(cost=None))
    result = send(bound, "worker:0")
    assert result.value.state == "CompletedCostUnknown"
    assert bound.raw_reply("worker:0") == result.value.reply_bytes
    assert bound.budget.spent_microusd == 10_000
    assert send(bound, "review:0").error.code == "RUN_RECONCILIATION_REQUIRED"
    assert bound.settle_generation("worker:0", generation_payload(bound, "worker:0")).status == "RECONCILED"
    assert bound.budget.spent_microusd == 1_000
    assert isinstance(send(bound, "review:0"), Ok) and len(transport.calls) == 2


def test_generation_settlement_is_durable_bound_and_idempotent(tmp_path):
    bound, transport = bind(tmp_path)
    send(bound, "worker:0")
    payload = generation_payload(bound, "worker:0")
    first = bound.settle_generation("worker:0", payload)
    restarted, new_transport = bind(tmp_path)
    assert restarted.settle_generation("worker:0", payload) == first
    assert restarted.budget.spent_microusd == 1_000
    assert send(restarted, "worker:0").error.code == "PFP_ACTION_ALREADY_CLAIMED"
    with pytest.raises(ProviderError, match="conflict"):
        restarted.settle_generation("worker:0", generation_payload(bound, "worker:0", "0.002"))
    assert restarted.budget.spent_microusd == 1_000 and len(transport.calls) == 1 and not new_transport.calls


def test_wrong_generation_and_absent_cost_never_release_money(tmp_path):
    bound, _ = bind(tmp_path)
    send(bound, "worker:0")
    assert bound.settle_generation("worker:0", {"data": {"id": "foreign", "total_cost": "0"}}).status == "UNRECONCILED"
    assert bound.settle_generation("worker:0", {"data": {"id": bound.action("worker:0")["generation_id"]}}).status == "UNRECONCILED"
    assert bound.budget.spent_microusd == 10_000


def test_reported_bill_above_admitted_liability_is_not_refunded_or_continued(tmp_path):
    bound, transport = bind(tmp_path, SyntheticTransport(cost="0.02"))
    result = send(bound, "worker:0")
    assert result.value.state == "CompletedOverAdmittedBudget"
    assert bound.budget.spent_microusd == 10_000
    assert send(bound, "review:0").error.code == "RUN_RECONCILIATION_REQUIRED"
    with pytest.raises(ProviderError, match="maximum liability"):
        bound.settle_generation("worker:0", generation_payload(bound, "worker:0", "0.02"))
    assert len(transport.calls) == 1 and bound.budget.spent_microusd == 10_000


def test_unbound_calls_cannot_escape_action_claims(tmp_path):
    bound, transport = bind(tmp_path)
    assert bound.complete_result(CandidateRequest(user="Task")).error.code == "PFP_ACTION_BINDING_REQUIRED"
    assert not transport.calls and bound.budget.spent_microusd == 0


def test_unsupported_real_transport_keeps_pre_dispatch_hard_refusal(tmp_path, monkeypatch):
    from adversary.infrastructure.providers import http

    monkeypatch.setattr(http, "post_json", lambda *args: pytest.fail("No vendor send authorized"))
    real_http = OpenAiCompatTransport(Provider.OPENROUTER, api_key="synthetic-not-a-vendor-key")
    bound, _ = bind(tmp_path, real_http)
    result = send(bound, "worker:0")
    assert isinstance(result, Err) and result.error.code == "BUDGET_ENFORCEMENT_UNAVAILABLE"
    assert bound.budget.spent_microusd == 0
    assert bound.action("worker:0")["state"] == "refused_before_dispatch"


def test_legacy_callable_cannot_gain_hard_budget_admission_by_being_wrapped(tmp_path):
    class LegacyCallable:
        calls = 0

        def maximum_liability(self, *args):
            return 1

        def __call__(self, provider, model, request):
            self.calls += 1
            pytest.fail("Legacy callable lacks admitted-request dispatch")

    transport = LegacyCallable()
    direct = OearsLlmGateway(ModelAllowlist.builtin(),
        GatewayPolicy(PriceTable.builtin(), BudgetController(50_000), 20, pricing_clock=lambda: AT),
        transport, Provider.OPENROUTER, MODEL)
    direct_result = direct.complete_result(CandidateRequest("System", "Task"))
    wrapped, _ = bind(tmp_path, transport)
    wrapped_result = send(wrapped, "worker:0")
    for result in (direct_result, wrapped_result):
        assert isinstance(result, Err)
        assert result.error.code == "BUDGET_ENFORCEMENT_UNAVAILABLE"
    assert transport.calls == 0
    assert direct.policy.budget.spent_microusd == 0 and wrapped.budget.spent_microusd == 0


def test_crash_after_atomic_claim_before_admission_never_reopens_the_action(tmp_path, monkeypatch):
    bound, transport = bind(tmp_path)
    monkeypatch.setattr(OearsLlmGateway, "complete_result", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("crash")))
    with pytest.raises(RuntimeError, match="crash"):
        send(bound, "worker:0")
    restarted, new_transport = bind(tmp_path)
    assert send(restarted, "worker:0").error.code == "PFP_ACTION_ALREADY_CLAIMED"
    assert send(restarted, "review:0").error.code == "RUN_RECONCILIATION_REQUIRED"
    assert not transport.calls and not new_transport.calls and bound.budget.spent_microusd == 0


def test_durable_factory_requires_scope_before_credentials_or_network(tmp_path, monkeypatch):
    from pfp.infrastructure import estimated_gateway

    monkeypatch.setattr(estimated_gateway, "resolve_openrouter_key", lambda *args: pytest.fail("scope admission must precede credentials"))
    with pytest.raises(ValueError, match="DURABLE_RUN_ID_REQUIRED"):
        estimated_gateway.create_accounted_openrouter_gateway(MODEL, 20,
            max_cost_microusd=50_000, accounting_path=tmp_path / "run.sqlite3")


def test_fixture_holds_are_visible_during_send(tmp_path):
    entered, release = threading.Event(), threading.Event()
    class PausedTransport(SyntheticTransport):
        def dispatch(self, admitted):
            entered.set()
            assert release.wait(15)
            return super().dispatch(admitted)
    bound, transport = bind(tmp_path, PausedTransport())
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(send, bound, "worker:0")
        assert entered.wait(15)
        assert bound.budget.spent_microusd == 10_000
        assert bound.action("worker:0")["state"] == "dispatched"
        release.set()
        assert isinstance(future.result(), Ok)
    assert len(transport.calls) == 1
