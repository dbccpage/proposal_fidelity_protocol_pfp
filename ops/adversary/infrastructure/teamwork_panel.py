"""Compose the governed panel and run its deterministic intake operation."""

from __future__ import annotations

import hashlib
import json
import os
from importlib.resources import files
from pathlib import Path
from typing import Literal

import yaml

from adversary.domain.native_gate_check import NativeGateCheck
from adversary.use_cases.teamwork import (
    HostAcceptanceRequirement,
    IntelligenceRead,
    PanelPlan,
    TaskCheck,
    TeamworkBrief,
    TeamworkObservation,
    TeamworkRun,
    build_panel_plan,
    start_teamwork,
)
from adversary.use_cases.teamwork_pfp import syntax_prefilter_preflight
from adversary.use_cases.teamwork_schedule import PanelSchedule, compile_schedule


class _PanelLoader(yaml.SafeLoader):
    """Reject ambiguous keys before the governed roster becomes a Python map."""

    def construct_mapping(self, node, deep=False):
        if not isinstance(node, yaml.MappingNode):
            raise ValueError("PANEL_RESOURCE_INVALID: expected a YAML mapping")
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if type(key) is not str:
                raise ValueError("PANEL_RESOURCE_INVALID: mapping keys must be strings")
            if key in result:
                raise ValueError("PANEL_DUPLICATE_KEY: " + key)
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def _default_native_gate_check() -> NativeGateCheck:
    """Freeze the explicit environment selection without loading optional hosts."""
    selected = os.environ.get("CORE_SYMBOL_GAME_HOST", "")
    path = Path(selected).absolute() if selected else None
    if path is None or not path.is_file() or path.is_symlink():
        return NativeGateCheck(unavailable_reason="NATIVE_HOST_INTAKE_UNAVAILABLE: select CORE_SYMBOL_GAME_HOST or an explicit native binding")
    return NativeGateCheck(binary_path=str(path), binary_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def load_panel_plan() -> PanelPlan:
    resource = files("adversary").joinpath(
        "roles", "adversary_panel.yaml")
    raw = resource.read_bytes()
    if len(raw) > 1024 * 1024:
        raise ValueError("PANEL_RESOURCE_TOO_LARGE")
    try:
        roster = yaml.load(raw, Loader=_PanelLoader)
    except yaml.YAMLError as exc:
        raise ValueError("PANEL_RESOURCE_INVALID: malformed YAML") from exc
    if (type(roster) is not dict or type(roster.get("characters")) is not list
            or any(type(member) is not dict for member in roster["characters"])):
        raise ValueError("PANEL_RESOURCE_INVALID")
    version = roster.get("version")
    if type(version) is not str or not version.strip() or version != version.strip():
        raise ValueError("PANEL_VERSION_INVALID: retain the exact declared version string")
    if roster.get("orchestrator_mode") != "NATIVE":
        raise ValueError("PANEL_ORCHESTRATOR_REQUIRED: the default workflow must be NATIVE")
    return build_panel_plan(roster["characters"], source_sha256=hashlib.sha256(raw).hexdigest(),
        source_version=version)


def load_panel_schedule(name: str, plan: PanelPlan) -> PanelSchedule:
    """Compile one declared schedule from the packaged schedule file."""
    resource = files("adversary").joinpath(
        "roles", "panel_schedules.yaml")
    raw = resource.read_bytes()
    if len(raw) > 256 * 1024:
        raise ValueError("SCHEDULE_RESOURCE_TOO_LARGE")
    try:
        declared = yaml.load(raw, Loader=_PanelLoader)
    except yaml.YAMLError as exc:
        raise ValueError("SCHEDULE_RESOURCE_INVALID: malformed YAML") from exc
    if type(declared) is not dict or type(declared.get("schedules")) is not dict:
        raise ValueError("SCHEDULE_RESOURCE_INVALID")
    if name not in declared["schedules"]:
        raise ValueError(f"SCHEDULE_UNKNOWN: {name}; declared: {sorted(declared['schedules'])}")
    order = tuple(step.role_id for step in plan.steps)
    intake = tuple(step.role_id for step in plan.steps if step.phase == "intake")
    return compile_schedule(name, declared["schedules"][name], order, intake)


def create_teamwork_run(
    objective: str, *, executor: Literal["ide", "openrouter", "anthropic"] = "ide",
    max_repairs: int = 1, run_id: str | None = None,
    intelligence: IntelligenceRead | None = None,
    checker_id: str = "", check_command: tuple[str, ...] = (),
    max_actions: int = 48, learn_after_run: bool = True,
    acceptance_check: HostAcceptanceRequirement | None = None,
    max_evaluations: int = 10,
    brief: TeamworkBrief | None = None,
    native_gate_check: NativeGateCheck | None = None,
    historical_v3: bool = False,
    density_dimension: int = 128,
    forge_organization: bool = True,
    schedule: str | None = None,
) -> TeamworkRun:
    """Create an unbound run from the packaged roster; never dispatch a model.

    NATIVE is the default orchestration policy. An explicit OpenRouter executor
    still needs its separate accounted gateway before any model turn can run.
    """
    if acceptance_check is None and not (intelligence and checker_id.strip() and check_command):
        raise ValueError("ACCEPTANCE_BINDING_REQUIRED: select the original independent host check before work")
    if historical_v3 and native_gate_check is not None:
        raise ValueError("LEGACY_NATIVE_GATE_BACKDATE_FORBIDDEN")
    if not historical_v3:
        fields = (brief or TeamworkBrief()).model_dump(mode="python")
        # New runs use the bounded evidence view. Restored actions retain their
        # absent/legacy profile, and an operator can still explicitly select it.
        fields["context_profile"] = (brief.context_profile
            if brief is not None and "context_profile" in brief.model_fields_set else "bounded-v1")
        fields.setdefault("density_dimension", density_dimension)
        fields.setdefault("forge_organization", forge_organization)
        brief = TeamworkBrief.model_validate(fields)
        if brief.forge_organization and brief.forge_preparation is None:
            from .prompt_geometry import organize_initial_seed

            brief = brief.model_copy(update={
                "forge_preparation": organize_initial_seed(objective, brief),
            })
    from .operad_binding import bind_panel_plan
    plan = load_panel_plan()
    if not historical_v3:
        plan = bind_panel_plan(plan)
    if schedule is not None:
        if historical_v3:
            raise ValueError("SCHEDULE_BACKDATE_FORBIDDEN: historical v3 runs keep the full Panel")
        plan = plan.model_copy(update={"schedule": load_panel_schedule(schedule, plan)})
        plan.validate_totality()
    return start_teamwork(
        objective, executor=executor, max_repairs=max_repairs, run_id=run_id,
        intelligence=intelligence, checker_id=checker_id, check_command=check_command,
        max_actions=max_actions, learn_after_run=learn_after_run,
        acceptance_check=acceptance_check,
        max_evaluations=max_evaluations,
        brief=brief,
        native_gate_check=None if historical_v3 else (native_gate_check or _default_native_gate_check()),
        panel_plan=plan,
    )


def run_syntax_prefilter_check(action):
    if action.role_id != "syntax_prefilter" or action.communication != "deterministic":
        raise ValueError("SYNTAX_PREFILTER_ACTION_REQUIRED")
    record = syntax_prefilter_preflight(action)
    from .prompt_geometry import observe_teamwork_seed
    geometry = observe_teamwork_seed(action)
    raw = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return TeamworkObservation(
        action_id=action.action_id, worker="Syntax Prefilter in-process syntax checker",
        summary="Checked action syntax and plan binding; task correctness remains unverified.",
        findings=tuple(record["findings"]), artifacts=action.artifacts,
        metadata={"role_id": "syntax_prefilter", "execution_kind": "deterministic",
            **({"density": {"original_seed": geometry}} if geometry else {}),
            **({'operation_execution': {**record['operation_validation'],
                'executed_operation_ids': record['operation_validation']['operation_ids'],
                'executed_guard_ids': [guard['op_id'] for guard in record['operation_validation']['guards']],
                'input_sha256': record['input_sha256'], 'outcome': 'CHECKED', 'authority_effect': 'None'}}
               if 'operation_validation' in record else {}),
            "host_tools_executed": True, "subprocess_executed": False,
            "deterministic_check": record},
        check=TaskCheck(initial_task_id=action.initial_task_id, source_id=action.plan_sha256,
            checker_id=record["checker_id"], command=("adversary", "teamwork", "check", "syntax_prefilter"),
            exit_status=1 if record["findings"] else 0,
            output_sha256=hashlib.sha256(raw).hexdigest(), artifacts=action.artifacts),
    )
