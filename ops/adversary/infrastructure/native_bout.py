"""Adversary API: marshal DTOs to the native seven-act composition root.

The operating-system host owns the process boundary. Routing, exact arithmetic,
seat execution, journal recovery and run persistence execute in Rust.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from operating_system.adapters.intelligence_custody.ic_routing import (
    IcMigrationRefusal,
    intelligence_path,
)
from operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from operations.domain.rop.result import Err, Ok, Refusal, Result
from adversary.domain.models import (
    SymbolGameRequestV1,
    AdversaryBoutOutcomeV1,
    AdversaryBoutRequestV1,
)
from adversary.stage.domain.run import SwarmRunStateV1
from adversary.infrastructure.seat_routing_loader import DEFAULT_CONFIG_PATH

from ..domain.native import wire_json

_LOCUS = "adversary.infrastructure.native_bout"


class LiveSchedulerStart:
    """A live scheduler and the state ``start`` returned. ``to_dict`` is that state."""

    def __init__(self, scheduler: Any, state: Any, packet: Any) -> None:
        self.scheduler = scheduler
        self.state = state
        self.packet = packet

    def to_dict(self) -> dict[str, Any]:
        return self.state.to_dict()


def _provider_environ(environ: Mapping[str, str] | None) -> dict[str, str] | None:
    if environ is None:
        return None
    result = dict(os.environ)
    result.pop("OPENROUTER_API_KEY", None)
    if environ.get("OPENROUTER_API_KEY"):
        result["OPENROUTER_API_KEY"] = environ["OPENROUTER_API_KEY"]
    return result


def bind_live_stage_scheduler(
    *,
    task_key: str,
    objective: str,
    panel_mode: str,
    budget_units: int,
) -> Result[Any, Refusal]:
    """Start the same ``stage_scheduler`` the live runtime uses.

    A failed council load or start refuses the bout before ``adversary_bout``.
    """
    try:
        if type(panel_mode) is not str or panel_mode not in ("core", "full"):
            raise ValueError("panel mode must be core or full")
        if type(budget_units) is not int or budget_units < 1:
            budget_units = 1
        from adversary.profile.profile_loader import load_adversary_council_profile
        from adversary.stage.application.scheduler import stage_scheduler
        from adversary.stage.domain.packets import WorkPacketV1

        definition, graph, profile, plan, stop = load_adversary_council_profile(
            panel_mode=panel_mode
        )
        scheduler = stage_scheduler(
            definition,
            profile,
            graph,
            plan,
            stop,
            live=True,
            panel_mode=panel_mode,
        )
        units = budget_units if budget_units <= stop.max_total_budget else stop.max_total_budget
        epoch = "sha256:" + hashlib.sha256(
            f"{task_key}\n{objective}\n{panel_mode}".encode("utf-8")
        ).hexdigest()
        packet = WorkPacketV1(
            task_key=task_key,
            scene_id=graph.entry_scene_id,
            objective=objective,
            input_artifact_refs=(),
            acceptance_criteria=("Start the live bout on the entry scene.",),
            budget_units=units,
            evaluator_epoch_id=epoch,
        )
        state = scheduler.start(task_key, packet)
    except (AttributeError, OSError, RuntimeError, TypeError, ValueError) as exc:
        return Err(Refusal("ADVERSARY_SCHEDULER_START_REFUSED", str(exc), _LOCUS))
    return Ok(LiveSchedulerStart(scheduler, state, packet))


def run_native_bout(
    task_key: str,
    objective: str,
    *,
    repo_root: Path | str,
    ledger_path: Path | str,
    bout_id: str,
    live: bool = False,
    config_path: Path | str = DEFAULT_CONFIG_PATH,
    env_file: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
    max_rounds: int = 4,
    request_external_admission: bool = False,
    journal_path: Path | str | None = None,
    carrier_context: Mapping[str, object] | None = None,
    ablation_flags: Mapping[str, object] | None = None,
    learning_guidance: str = "",
    instruction_plan: Mapping[str, object] | None = None,
    symbol_game_request: SymbolGameRequestV1 | None = None,
    model_override: str | None = None,
    residuals: list[Refusal] | None = None,
    instruction_admission: Mapping[str, object] | None = None,
    compute_budget: int = 100,
    swarm_type: str = "open-topic",
    max_cost_microusd: int | None = None,
    max_output_tokens: int = 4096,
    selected_characters: tuple[str, ...] | None = None,
    panel_mode: str = "core",
    output_dir: Path | str | None = None,
    scheduler_preflight: Mapping[str, object] | None = None,
) -> Result[AdversaryBoutOutcomeV1, Refusal]:
    """Run the seven-act native circuit; every live model turn uses native PFP."""
    if live and instruction_plan is None:
        return Err(Refusal("NATIVE_INSTRUCTION_PLAN_UNBOUND", "live Adversary requires an operator-signed instruction plan", _LOCUS))
    if live and instruction_admission is None:
        return Err(Refusal("NATIVE_INSTRUCTION_ADMISSION_UNBOUND", "native signature and source custody required", _LOCUS))
    if symbol_game_request is not None and type(symbol_game_request) is not SymbolGameRequestV1:
        return Err(
            Refusal(
                "ADVERSARY_SYMBOL_GAME_REQUEST_INVALID",
                "an exact SymbolGameRequestV1 is required",
                _LOCUS,
            )
        )
    repo_root = Path(repo_root).absolute()
    try:
        canonical_output = intelligence_path(repo_root, "_intelligence/_adversary")
        output_dir = Path(output_dir).absolute() if output_dir is not None else canonical_output
        if output_dir.resolve() != canonical_output.resolve():
            return Err(
                Refusal(
                    "ADVERSARY_OUTPUT_CUSTODY_INVALID",
                    "output must use the canonical _ic/adversary directory",
                    _LOCUS,
                )
            )
    except IcMigrationRefusal as exc:
        return Err(Refusal(exc.code, str(exc), _LOCUS))
    process_environ = _provider_environ(environ)
    carrier = dict(carrier_context or {})
    if isinstance(carrier.get("cochains"), Mapping):
        carrier["cochains"] = {str(key): value for key, value in carrier["cochains"].items()}
    payload = {
        "task_key": task_key,
        "objective": objective,
        "repo_root": str(repo_root),
        "adversary_output_dir": str(output_dir.resolve()),
        "resources_root": str(Path(__file__).resolve().parents[2]),
        "ledger_path": str(ledger_path),
        "bout_id": bout_id,
        "live": live,
        "config_path": str(config_path),
        "env_file": str(env_file) if env_file is not None else None,
        "max_rounds": max_rounds,
        "compute_budget": compute_budget,
        "swarm_type": swarm_type,
        "max_cost_microusd": max_cost_microusd,
        "max_output_tokens": max_output_tokens,
        "selected_characters": list(selected_characters)
        if selected_characters is not None
        else None,
        "panel_mode": panel_mode,
        "instruction_admission": dict(instruction_admission)
        if instruction_admission is not None
        else None,
        "carrier_context": json.loads(wire_json(carrier)),
        "ablation_flags": dict(ablation_flags or {}),
        "learning_guidance": learning_guidance,
        "instruction_plan": dict(instruction_plan) if instruction_plan is not None else None,
        "symbol_game_request": asdict(symbol_game_request)
        if symbol_game_request is not None
        else None,
        "model_override": model_override,
        "request_external_admission": request_external_admission,
        "journal_path": str(journal_path) if journal_path is not None else None,
        "scheduler_preflight": dict(scheduler_preflight)
        if scheduler_preflight is not None
        else None,
    }
    response = RustSymbolGameHost(process_environ=process_environ).invoke_runtime(
        "adversary_bout", payload
    )
    if isinstance(response, Err):
        return response
    wire = response.value
    if not wire["success"]:
        return Err(Refusal("ADVERSARY_NATIVE_DISPATCH_FAILED", str(wire.get("error")), _LOCUS))
    result = wire["result"]
    refusal = result.get("refusal")
    if refusal is not None:
        return Err(
            Refusal(
                code=refusal["code"],
                message=refusal["message"],
                locus=refusal.get("locus", _LOCUS),
                details=tuple(refusal.get("details", {}).items()),
            )
        )
    outcome = dict(result["outcome"])
    outcome.pop("schema_version", None)
    journal_residuals = outcome.pop("journal_residuals", [])
    recovery = outcome.pop("recovery_residuals", None)
    if residuals is not None:
        for value in [*journal_residuals, *([recovery] if recovery else [])]:
            residuals.append(Refusal(value["code"], value["message"], _LOCUS))
    try:
        return Ok(AdversaryBoutOutcomeV1(**outcome))
    except (TypeError, ValueError) as exc:
        return Err(Refusal("ADVERSARY_NATIVE_OUTCOME_INVALID", str(exc), _LOCUS))


class NativeBoutExecutionAdapter:
    """Composition port: Rust owns acts, model routing, journal and artifact custody."""

    def __init__(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
        symbol_game_request: SymbolGameRequestV1 | None = None,
        instruction_ingress: object | None = None,
        routing_config: Path | str = DEFAULT_CONFIG_PATH,
        env_file: Path | str | None = None,
        output_dir: Path | str | None = None,
        max_cost_microusd: int | None = None,
        max_output_tokens: int = 4096,
        selected_characters: tuple[str, ...] | None = None,
        panel_mode: str = "core",
    ) -> None:
        if symbol_game_request is not None and type(symbol_game_request) is not SymbolGameRequestV1:
            raise TypeError("an exact SymbolGameRequestV1 is required")
        self.symbol_game_request = symbol_game_request
        self.instruction_ingress = instruction_ingress
        self.routing_config = routing_config
        self.env_file = env_file
        self.output_dir = output_dir
        self.max_cost_microusd = max_cost_microusd
        self.max_output_tokens = max_output_tokens
        self.selected_characters = selected_characters
        self.panel_mode = panel_mode
        self.provider = provider
        self.model = model
        self.residuals: list[Refusal] = []

    def execute_bout(
        self,
        request: AdversaryBoutRequestV1,
        *,
        repo_root: Path,
        learning_guidance: str,
        instruction_plan: Mapping[str, object] | None = None,
    ) -> Result[AdversaryBoutOutcomeV1 | SwarmRunStateV1, Refusal]:
        if not request.fixture_mode and self.provider != "openrouter":
            return Err(Refusal("EXECUTION_UNAVAILABLE", "no model executor is configured", _LOCUS))
        admission = None
        if not request.fixture_mode:
            verifier = getattr(self.instruction_ingress, "native_admission", None)
            if verifier is None:
                return Err(
                    Refusal(
                        "NATIVE_INSTRUCTION_ADMISSION_UNBOUND",
                        "native signature material is required",
                        _LOCUS,
                    )
                )
            admitted = verifier(request)
            if isinstance(admitted, Err):
                return admitted
            admission = admitted.value
        try:
            ledger_path = intelligence_path(repo_root, "_intelligence/_adversary/seat_calls.jsonl")
        except IcMigrationRefusal as exc:
            return Err(Refusal(exc.code, str(exc), _LOCUS))
        bound = bind_live_stage_scheduler(
            task_key=request.task_key,
            objective=request.objective,
            panel_mode=self.panel_mode,
            budget_units=request.compute_budget,
        )
        if isinstance(bound, Err):
            return bound
        preflight = bound.value.to_dict() if bound.value is not None else None
        outcome = run_native_bout(
            request.task_key,
            request.objective,
            repo_root=repo_root,
            ledger_path=ledger_path,
            bout_id=uuid4().hex,
            live=not request.fixture_mode,
            max_rounds=request.max_rounds,
            request_external_admission=request.request_external_admission,
            carrier_context=request.carrier_context,
            ablation_flags=request.ablation_flags,
            learning_guidance=learning_guidance,
            instruction_plan=instruction_plan,
            symbol_game_request=self.symbol_game_request,
            model_override=self.model,
            residuals=self.residuals,
            instruction_admission=admission,
            compute_budget=request.compute_budget,
            swarm_type=request.swarm_type.value,
            config_path=self.routing_config,
            env_file=self.env_file,
            output_dir=self.output_dir,
            max_cost_microusd=self.max_cost_microusd,
            max_output_tokens=self.max_output_tokens,
            selected_characters=self.selected_characters,
            panel_mode=self.panel_mode,
            scheduler_preflight=preflight,
        )
        if isinstance(outcome, Err) or not isinstance(bound.value, LiveSchedulerStart):
            return outcome
        from adversary.stage.application.scheduler import finish_bout

        completed = finish_bout(bound.value.scheduler, bound.value.state, bound.value.packet)
        return completed


__all__ = [
    "LiveSchedulerStart",
    "NativeBoutExecutionAdapter",
    "bind_live_stage_scheduler",
    "run_native_bout",
]
