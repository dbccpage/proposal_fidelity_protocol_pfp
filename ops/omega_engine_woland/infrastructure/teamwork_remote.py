"""Remote text executors for Woland teamwork, built from one base provider template.

A template states what differs between providers: the executor name recorded in
the run, the provider enum, the accepted durable budget schemas, the per-run
ceiling, how a teamwork action maps to decoding parameters, and how the
accounted gateway is composed. Everything else (PFP preparation, reply checking,
raw custody, refusal handling) is shared. A new provider adds one template.

Estimated or rated admission is conservative accounting, not a vendor bill.
AuthorityEffect: None.
"""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from omega_engine_operations.domain.rop.result import Err
from omega_engine_pfp.use_cases.pfp_proposal import REPAIR_RULES
from omega_engine_woland.domain.providers.types import (
    CandidateRequest,
    DecodingParamsV1,
    Provider,
)
from omega_engine_woland.use_cases.teamwork import TeamworkAction, TeamworkObservation
from omega_engine_woland.use_cases.teamwork_pfp import (
    check_teamwork_reply,
    prepare_teamwork_turn,
)

from .prompt_geometry import observe_teamwork_reply, observe_text

COMPACT_PROFILES = ("compact-v1", "compact-v2")
EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")
UNSETTLED_STATES = frozenset({"CompletedCostUnknown", "CompletedOverEstimatedBudget",
    "CompletedOverAdmittedBudget", "CompletedAccountingUnavailable"})


def compact_profile(action) -> bool:
    return bool(action.brief and action.brief.response_profile in COMPACT_PROFILES)


def strict_schema(turn) -> dict:
    return {"type": "json_schema", "json_schema": {
        "name": "woland_pfp_turn", "strict": True, "schema": turn.prompt.response_schema}}


@dataclass(frozen=True)
class RemoteProviderTemplate:
    """Base template. Subclasses override only the provider-specific parts."""

    name: str
    provider: Provider
    budget_schemas: frozenset
    ceiling_microusd: int
    ceiling_label: str
    default_calls_estimated: int = 42

    def decoding(self, action, turn, *, effort=None) -> DecodingParamsV1:
        raise NotImplementedError

    def gateway(self, model, max_output_tokens, **options):
        raise NotImplementedError

    def resolve_model(self, model: str, *, preset: str | None = None) -> str:
        return model

    def effective_ceiling_microusd(self, *, preset: str | None = None) -> int:
        from omega_engine_pfp.infrastructure.estimated_gateway import (
            ANTHROPIC_RUN_CEILING_MICROUSD,
        )

        return ANTHROPIC_RUN_CEILING_MICROUSD if preset is not None else self.ceiling_microusd

    def check_ceiling(self, ceiling, *, preset: str | None = None) -> None:
        limit = self.effective_ceiling_microusd(preset=preset)
        if type(ceiling) is not int or not 0 < ceiling <= limit:
            raise ValueError("WOLAND_RUN_BUDGET_REQUIRED: bind a durable run-wide ceiling at most "
                             + ("$4.00" if preset is not None else self.ceiling_label))

    def rated_cost(self, gateway, attempt_id):
        """Host-rated estimate from the ledger; None when the template has no rating."""
        return None


REMOTE_EXECUTOR_MODULES = {
    "openrouter": "omega_engine_woland.infrastructure.teamwork_openrouter",
    "anthropic": "omega_engine_woland.infrastructure.teamwork_anthropic",
}
REMOTE_EXECUTORS = tuple(REMOTE_EXECUTOR_MODULES)


def remote_factory(name: str):
    """Return the provider module's executor factory, looked up at call time."""
    import importlib

    try:
        module = importlib.import_module(REMOTE_EXECUTOR_MODULES[name])
    except KeyError:
        raise ValueError(f"REMOTE_EXECUTOR_UNSUPPORTED: {name}") from None
    return getattr(module, "create_" + name + "_executor")


def _captured_geometry(action, turn, *, provider_raw=None, completion=None):
    """Keep actual captures even when provider or UTF-8 admission refuses them."""
    dimension = action.brief.density_dimension if action.brief is not None else None
    if dimension is None:
        return {}
    density = dict(turn.observation_metadata.get("density", {}))
    if provider_raw is not None:
        density["provider_wire"] = observe_text(provider_raw, dimension=dimension,
            role_id=action.role_id, field="provider.raw_reply", trust_level="untrusted-provider")
    if completion is not None:
        density["reply"] = observe_teamwork_reply(action, completion.encode("utf-8", errors="surrogatepass"))
    return {"density":density, "pfp_prepared_prompts":{
        "system":turn.prompt.system, "user":turn.prompt.user,
        "response_schema":turn.prompt.response_schema, "binding":turn.binding}}


@dataclass
class RemoteTeamworkExecutor:
    """Shared PFP dispatch; a provider subclass fixes ``template``."""

    template: ClassVar[RemoteProviderTemplate]
    gateway: object
    model: str
    max_reply_repairs: int = 1
    recover_completed: bool = False
    recover_only_action_id: str | None = None
    effort: str | None = None
    preset: str | None = None

    @property
    def execution_mode(self) -> str:
        return self.template.name

    def __call__(self, action: TeamworkAction) -> TeamworkObservation:
        if action.feedback_policy is None:
            raise ValueError("LEGACY_FEEDBACK_READ_ONLY: historical actions cannot dispatch new work")
        if action.communication == "deterministic":
            from .teamwork_retinue import run_hella_check

            return run_hella_check(action)
        if action.communication == "host":
            raise ValueError("HOST_ACTION_REQUIRED: host operations cannot dispatch a provider")
        from omega_engine_pfp.infrastructure.estimated_gateway import (
            DurableRunGateway,
            EstimatedBudgetGateway,
        )

        gateway = self.gateway
        if type(gateway) not in (DurableRunGateway, EstimatedBudgetGateway):
            raise ValueError("WOLAND_RUN_BUDGET_REQUIRED: direct execution requires the accounted gateway owner")
        binding = gateway.binding
        template = self.template
        if (binding.get("schema") not in template.budget_schemas
                or type(binding.get("limit_microusd")) is not int
                or not 0 < binding["limit_microusd"] <= template.effective_ceiling_microusd(preset=self.preset)
                or binding.get("run_id") != action.run_id
                or binding.get("objective_sha256") != hashlib.sha256(action.objective.encode()).hexdigest()
                or DurableRunGateway.read_binding(binding["accounting_path"]) != binding
                or (type(gateway) is EstimatedBudgetGateway and gateway.model != self.model)
                or (type(gateway) is EstimatedBudgetGateway and gateway.provider != template.provider)):
            raise ValueError("DURABLE_RUN_SCOPE_MISMATCH: retain the original run, model and "
                             + template.ceiling_label + " ceiling")
        return self._execute_action(action)

    def _execute_action(self, action: TeamworkAction) -> TeamworkObservation:
        """Internal PFP processing; public dispatch first validates real accounting."""
        if action.workflow_version in ("omega.woland.teamwork.v3", "omega.woland.teamwork.v4"):
            from .teamwork_intelligence_host import (
                _current_checker,
                _current_source,
                validate_ddc_context,
            )

            _current_source(action)
            if action.learning_context is not None:
                from .teamwork_intelligence_host import validate_learning_context

                validate_learning_context(action)
            _current_checker(action)
            if action.kind == "learn":
                validate_ddc_context(action)
        if type(self.max_reply_repairs) is not int or not 0 <= self.max_reply_repairs <= 3:
            raise ValueError("INVALID_REPLY_REPAIR_LIMIT")
        attempts = []
        for attempt in range(self.max_reply_repairs + 1):
            observed = self._attempt(action, attempt, attempts)
            if not observed.blocked or observed.metadata.get("failure_code") not in {
                "PFP_TASK_ENVELOPE", "MALFORMED_REVIEW", "MALFORMED_LEARNING"}:
                return observed
        return observed

    def _attempt(self, action, attempt, attempts):
        template = self.template
        turn = prepare_teamwork_turn(action, attempt=attempt,
            feedback=REPAIR_RULES["TASK_ENVELOPE"] if attempt else None)
        request = CandidateRequest(system=turn.prompt.system, user=turn.prompt.user,
            decoding=template.decoding(action, turn, effort=self.effort))
        gateway = self.gateway
        bind_action = getattr(gateway, "for_action", None)
        if callable(bind_action):
            gateway = bind_action(turn.binding["attempt_id"])
        active_model = (template.resolve_model(getattr(action, "assigned_model", "") or self.model, preset=self.preset)
                        if self.preset is not None else self.model)
        replayed = False
        if self.recover_only_action_id == action.action_id:
            recover = getattr(gateway, "recover_result", None)
            if not callable(recover):
                raise ValueError("RUN_RECONCILIATION_REQUIRED")
            result = recover(request, provider=template.provider, model=active_model)
            replayed = True
        else:
            result = gateway.complete_result(request, provider=template.provider, model=active_model)
            if (self.recover_completed and isinstance(result, Err)
                    and result.error.code == "PFP_ACTION_ALREADY_CLAIMED"):
                result = gateway.recover_result(request, provider=template.provider, model=active_model)
                replayed = True
        worker = template.name + ":" + active_model
        if isinstance(result, Err):
            failure = result.error
            failure_metadata = failure.response_metadata() if hasattr(failure, "response_metadata") else {}
            captured_raw = (base64.b64decode(failure_metadata["raw_reply_base64"], validate=True)
                if "raw_reply_base64" in failure_metadata else None)
            return TeamworkObservation(action_id=action.action_id, worker=worker, blocked=True,
                summary="Provider action unavailable: " + failure.code,
                metadata={"role_id": action.role_id, "execution_kind": "pfp",
                    "failure_code": failure.code, "attempt_id": failure.attempt_id,
                    "retry": failure.retry.value, "host_tools_executed": False,
                    "pfp_attempts": list(attempts), "reply_repairs_used": attempt,
                    **failure_metadata, **_captured_geometry(action, turn, provider_raw=captured_raw)})
        outcome, response = result.value, result.value.candidate
        admitted, raw = outcome.admitted, outcome.reply_bytes
        metadata = {
            "role_id": action.role_id, "execution_kind": "pfp", "pfp_attempt": attempt,
            "raw_reply_base64": base64.b64encode(raw).decode("ascii"),
            "raw_reply_sha256": hashlib.sha256(raw).hexdigest(),
            "attempt_id": admitted.attempt_id, "request_digest": admitted.request_digest,
            "reservation_id": admitted.reservation_id,
            "budget_receipt": admitted.receipt.to_dict() if admitted.receipt is not None else None,
            "estimated_microusd": admitted.estimated_microusd, "cost_usd": response.cost_usd,
            "rated_cost_usd": template.rated_cost(self.gateway, turn.binding["attempt_id"]),
            "generation_id": response.generation_id, "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens, "model": response.model,
            "provider": response.provider, "transport": response.transport,
            "effort": self.effort, "remote_executor": template.name,
            "attempt_state": outcome.state, "host_tools_executed": False,
            "run_budget": getattr(self.gateway, "binding", None),
            "replayed_raw_reply": replayed,
            **_captured_geometry(action, turn, provider_raw=raw, completion=response.content),
        }
        if (response.provider != template.provider.value or response.transport == "fixture"
                or response.authority_effect != "None"):
            return TeamworkObservation(action_id=action.action_id, worker=worker, blocked=True,
                summary="Provider returned an incompatible execution mode or authority claim.",
                metadata={**metadata, "failure_code": "PROVIDER_MODE_MISMATCH"})
        try:
            completion_bytes = response.content.encode("utf-8")
        except UnicodeEncodeError:
            return TeamworkObservation(action_id=action.action_id, worker=worker, blocked=True,
                summary="Provider completion is not valid UTF-8; no proposal consumed.",
                metadata={**metadata, "failure_code": "INVALID_COMPLETION_UTF8",
                    "pfp_attempts": list(attempts), "reply_repairs_used": attempt})
        observed = check_teamwork_reply(action, turn, completion_bytes,
            worker=worker, metadata=metadata, observe=False)
        attempts.append(dict(metadata, pfp=observed.metadata["pfp"]))
        if outcome.state in UNSETTLED_STATES:
            observed = observed.model_copy(update={"blocked": True,
                "summary": "Provider accounting requires reconciliation; no further dispatch.",
                "metadata": {**observed.metadata, "failure_code": outcome.state}})
        return observed.model_copy(update={"metadata": {**observed.metadata,
            "pfp_attempts": list(attempts), "reply_repairs_used": attempt}})


def build_remote_executor(
    executor_class: type[RemoteTeamworkExecutor], model: str, max_output_tokens: int, *,
    env_file: Path | str | None = None, max_cost_microusd: int | None = None,
    allow_unbounded_cost: bool = False, max_estimated_cost_microusd: int | None = None,
    max_calls: int | None = None, accounting_path: Path | str | None = None,
    max_reply_repairs: int = 1, run_id: str | None = None, objective_sha256: str | None = None,
    recover_completed: bool = False, recover_only_action_id: str | None = None,
    pricing_snapshot: dict | None = None, effort: str | None = None,
    preset: str | None = None,
) -> RemoteTeamworkExecutor:
    """Require the template's run-wide ceiling before constructing any transport."""
    template = executor_class.template
    if preset is not None:
        model = template.resolve_model(model, preset=preset)
    ceiling = (max_cost_microusd if max_cost_microusd is not None
               else max_estimated_cost_microusd)
    if (allow_unbounded_cost or (max_cost_microusd is not None and max_estimated_cost_microusd is not None)
            or accounting_path is None or run_id is None or objective_sha256 is None):
        raise ValueError("WOLAND_RUN_BUDGET_REQUIRED: bind a durable run-wide ceiling at most "
                         + template.ceiling_label)
    template.check_ceiling(ceiling, preset=preset)
    if max_calls is None:
        max_calls = template.default_calls_estimated if max_estimated_cost_microusd is not None else 32
    extra = {"preset": preset} if preset is not None else {}
    gateway = template.gateway(model, max_output_tokens,
        env_file=env_file, max_cost_microusd=max_cost_microusd,
        allow_unbounded_cost=allow_unbounded_cost,
        max_estimated_cost_microusd=max_estimated_cost_microusd,
        max_calls=max_calls, accounting_path=accounting_path,
        run_id=run_id, objective_sha256=objective_sha256, pricing_snapshot=pricing_snapshot,
        **extra)
    return executor_class(gateway, model, max_reply_repairs=max_reply_repairs,
        recover_completed=recover_completed, recover_only_action_id=recover_only_action_id,
        effort=effort, preset=preset)
