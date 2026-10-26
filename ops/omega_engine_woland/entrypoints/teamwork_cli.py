"""Thin CLI for the shared Woland use case; IDE actions run in the current host.

Origin: omega_engine_woland.entrypoints.teamwork_cli.
The printed JSON is a host status record and makes no admission claim.
AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

from omega_engine_woland.infrastructure.native import DefaultNativeOperationPort

from ..domain.native_gate_check import decode_native_json
from ..infrastructure.teamwork_retinue import create_teamwork_run
from ..infrastructure.teamwork_state import (
    default_state_path,
    prepared_saved_turn,
    save_teamwork_state,
)
from ..use_cases.teamwork import (
    POST_RUN_LEARNING_INSTRUCTIONS,
    TeamworkBrief,
    TeamworkObservation,
    TeamworkRun,
    drive_teamwork,
    next_action,
    observe,
    resume_teamwork,
    tool_unavailable,
)


def _save(path: Path, run: TeamworkRun, *, new: bool = False) -> dict:
    return save_teamwork_state(path, run, new=new)


_FINANCIAL_LIMIT_KEYS = {"pfp.fuzzy-run.v1": "max_estimated_cost_microusd",
    "pfp.anthropic-rated-run.v1": "max_estimated_cost_microusd",
    "pfp.hard-run.v1": "max_cost_microusd"}


def _expected_financial_policy(budget):
    financial_key = _FINANCIAL_LIMIT_KEYS.get(budget.get("schema"))
    if financial_key is None:
        raise ValueError("DURABLE_RUN_FINANCIAL_POLICY_MISMATCH")
    expected = dict(max_cost_microusd=None, max_estimated_cost_microusd=None,
        allow_unbounded_cost=False)
    expected[financial_key] = budget["limit_microusd"]
    return expected


def _require_resume_budget(task):
    from omega_engine_pfp.infrastructure.estimated_gateway import DurableRunGateway

    config = task.provider_binding
    if not config or not isinstance(config.get("run_budget"), dict):
        raise ValueError("OPENROUTER_RESUME_UNBOUND: original durable financial binding is required")
    budget = config["run_budget"]
    if config.get("financial_policy") != _expected_financial_policy(budget):
        raise ValueError("DURABLE_RUN_FINANCIAL_POLICY_MISMATCH")
    objective = hashlib.sha256(task.objective.encode("utf-8")).hexdigest()
    if budget.get("run_id") != task.run_id or budget.get("objective_sha256") != objective:
        raise ValueError("DURABLE_RUN_SCOPE_MISMATCH")
    # Read existing bytes before gateway construction can create a row or seek credentials.
    if DurableRunGateway.read_binding(budget["accounting_path"]) != budget:
        raise ValueError("DURABLE_RUN_SCOPE_MISMATCH")
    return config, budget


def _require_recovery_parents(config) -> None:
    for parent in config.get("recovery_parents", []):
        if hashlib.sha256(Path(parent["path"]).read_bytes()).hexdigest() != parent["sha256"]:
            raise ValueError("CONTINUATION_PARENT_CHANGED")


def _resume_pending_task(task, parsed, state_bytes):
    pending = next_action(task)
    stopped = task.work_status in ("blocked", "partial") and pending is None
    if stopped:
        return resume_teamwork(task, parent_state_path=str(parsed.state.absolute()),
            parent_state_sha256=hashlib.sha256(state_bytes).hexdigest(), reason=parsed.reason,
            additional_repairs=parsed.additional_repairs, additional_actions=parsed.additional_actions)
    if pending is None:
        raise ValueError("RUN_NOT_STOPPED")
    if parsed.additional_actions or parsed.additional_repairs:
        raise ValueError("PENDING_RECOVERY_CANNOT_ADD_WORK_ALLOWANCE")
    return task


def _with_recovery_parent(task, config, parsed, state_bytes):
    config = {**config, "recovery_parents": [*config.get("recovery_parents", []),
        dict(path=str(parsed.state.absolute()), sha256=hashlib.sha256(state_bytes).hexdigest(),
             reason=parsed.reason)]}
    return task.model_copy(update={"provider_binding": config}), config


def _recover_only_action(action, output):
    expected = action.artifacts.get(str(output.resolve())) if action else None
    changed_repair = (action and action.kind == "repair" and output.exists()
        and hashlib.sha256(output.read_bytes()).hexdigest() != expected)
    recover_only = action.action_id if action and output.exists() and (
        action.kind == "build" or changed_repair) else None
    return expected, recover_only


def _remote_template_options(config, snapshot):
    options = {}
    if snapshot is not None:
        options["pricing_snapshot"] = snapshot
    if config.get("effort") is not None:
        options["effort"] = config["effort"]
    if config.get("preset") is not None:
        options["preset"] = config["preset"]
    return options


def _resume_remote(task, parsed, state_bytes):
    from ..infrastructure.teamwork_file_host import file_text_executor
    from ..infrastructure.teamwork_remote import remote_factory

    config, budget = _require_resume_budget(task)
    _require_recovery_parents(config)
    task = _resume_pending_task(task, parsed, state_bytes)
    task, config = _with_recovery_parent(task, config, parsed, state_bytes)
    action = next_action(task)
    output = Path(config["output_path"])
    expected, recover_only = _recover_only_action(action, output)
    snapshot = _bound_pricing_snapshot(config)
    remote = remote_factory(task.executor)(config["model"], config["max_output_tokens"],
        env_file=config.get("env_file"), **config["financial_policy"],
        max_calls=budget["max_calls"], accounting_path=budget["accounting_path"],
        run_id=budget["run_id"], objective_sha256=budget["objective_sha256"],
        max_reply_repairs=config["max_reply_repairs"], recover_completed=True,
        recover_only_action_id=recover_only,
        **_remote_template_options(config, snapshot))
    if remote.gateway.binding != budget:
        raise ValueError("DURABLE_RUN_SCOPE_MISMATCH")
    if parsed.state.read_bytes() != state_bytes:
        raise ValueError("CONTINUATION_PARENT_CHANGED")
    _save(parsed.output, task, new=True)
    return drive_teamwork(task, file_text_executor(remote, output,
        expected_artifact_sha256=expected, recover_existing_artifact=bool(recover_only),
        run_reader=lambda: TeamworkRun.model_validate_json(parsed.output.read_bytes())),
        checkpoint=lambda updated: _save(parsed.output, updated))


def _bound_pricing_snapshot(config):
    """Reload the operator snapshot only when its bytes still match the run binding."""
    path, expected = config.get("pricing_snapshot_path"), config.get("pricing_snapshot_sha256")
    if path is None and expected is None:
        return None
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("PRICING_SNAPSHOT_CHANGED: the bound price snapshot bytes differ")
    return json.loads(raw)


def _saved_pending_prompt(run, state_path, pending):
    if state_path is None or not state_path.exists() or not run.brief or run.brief.density_dimension is None:
        return pending
    saved = TeamworkRun.model_validate_json(state_path.read_bytes())
    if saved.model_dump(mode="json", exclude={"pending_prompt"}) != run.model_dump(mode="json", exclude={"pending_prompt"}):
        raise ValueError("REPORT_SOURCE_CHANGED: state changed before prompt display")
    return saved.pending_prompt


def _prepare_pfp_turn(run, action, state_path):
    if action.learning_context is not None:
        from ..infrastructure.teamwork_intelligence_host import validate_learning_context

        validate_learning_context(action)
    if action.kind == "learn" and action.workflow_version in ("omega.woland.teamwork.v3", "omega.woland.teamwork.v4"):
        from ..infrastructure.teamwork_intelligence_host import validate_ddc_context

        validate_ddc_context(action)
    pending = _saved_pending_prompt(run, state_path, run.pending_prompt)
    turn = prepared_saved_turn(action, pending)
    prepared = {**turn.prompt.to_dict(), "binding": turn.binding,
        "transport": "current_ide_session" if run.executor == "ide" else run.executor,
        "cost_usd": None, "evidence_grade": "UNVERIFIED"}
    if turn.observation_metadata:
        prepared["observation_metadata"] = turn.observation_metadata
    return prepared


def _attach_reporting(extra, state_path, run) -> None:
    if state_path is None or not run.brief or run.brief.density_dimension is None:
        return
    try:
        from ..infrastructure.teamwork_reporting import read_checkpoint_reports
        extra["reporting"] = read_checkpoint_reports(state_path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        extra["reporting"] = {"status": "REPORTING_UNAVAILABLE", "detail": str(exc),
                              "task_outcome_changed": False}
    extra["state_path"] = str(state_path)


def _latest_learning(run):
    return next((item.metadata for item in reversed(run.observations)
                 if item.metadata.get("learning_stage") == "learn"), {})


def _learning_status(run, action, learning):
    if learning:
        status = "IDE_APPLICATION_REQUIRED" if learning.get("proposed_only") else "HOST_REPORTED_COMPLETE"
    elif run.work_status in ("blocked", "partial"):
        status = "HOST_ACTION_REQUIRED"
    elif action and action.kind == "learn":
        status = "PENDING_HOST_ACTION"
    elif action:
        status = "AFTER_RUN"
    else:
        status = "HOST_ACTION_REQUIRED"
    if (learning and run.feedback_policy == "semantic_digestion_v2"
            and run.continuation_status["semantic_review_pending"]):
        status = "REVIEW_PENDING"
    return status


def _report(run: TeamworkRun, *, state_path: Path | None = None, **extra: object) -> None:
    from ..use_cases.teamwork_reports import finding_dispositions

    action = next_action(run)
    prepared = _prepare_pfp_turn(run, action, state_path) if action and action.communication == "pfp" else None
    _attach_reporting(extra, state_path, run)
    learning = _latest_learning(run)
    learning_status = _learning_status(run, action, learning)
    print(json.dumps({
        "run_id": run.run_id, "executor": run.executor, "work_status": run.work_status,
        "evidence_verdict": run.evidence_verdict, "authority_effect": "None",
        "workflow_version": run.schema_version, "retinue_coverage": run.retinue_coverage,
        "native_gate_coverage": run.native_gate_coverage,
        "original_task_outcome": _original_task_outcome(run),
        "finding_dispositions": finding_dispositions(run),
        "next_action": action.model_dump(mode="json") if action else None,
        "pfp_turn": prepared,
        "continuation": run.continuation_status,
        "post_run_learning": {"status": learning_status, "enabled": run.learn_after_run,
            "skills": ["/auto-oe-autop", "/auto-learn"], "mode": "post-run",
            "instructions": POST_RUN_LEARNING_INSTRUCTIONS,
            "proposed_only": bool(learning.get("proposed_only")),
            "reported_changed_paths": learning.get("changed_paths", []),
            "no_change_reason": learning.get("no_change_reason"), "automatic_execution": False},
        **extra,
    }, ensure_ascii=False))


def _host_acceptance_item(run, item) -> bool:
    if item.check is None or item.metadata.get("execution_kind") != "host":
        return False
    checker_id = run.acceptance_check.checker_id if run.acceptance_check else run.checker_id
    return item.check.checker_id == checker_id


def _query_more_info(output):
    if type(output) is not dict or output.get("accepted") is not True:
        return None
    if output.get("outcome") != "QUERY_USER_MORE_INFO":
        return None
    if output.get("mathematical_acceptance") != "NOT_SOLVED":
        return None
    return {"outcome": "QUERY_USER_MORE_INFO", "mathematical_acceptance": "NOT_SOLVED",
        "missing_fields": output.get("missing_fields", []),
        "scope": "Original host-selected checker output, not mathematical acceptance."}


def _checked_outcome(run, item):
    if item.check.exit_status != 0:
        return {"outcome": "CHECK_REFUSED", "mathematical_acceptance": "NOT_ESTABLISHED"}
    try:
        from ..infrastructure.teamwork_native_gates import _checker_bytes

        raw = _checker_bytes(item.metadata, item.check.model_dump(mode="json"))
        if raw is None:
            return None
        return _query_more_info(decode_native_json(raw[0]))
    except (ValueError, TypeError):
        return None


def _original_task_outcome(run):
    """Report a checked clarification separately from workflow completion."""
    for item in reversed(run.observations):
        if not _host_acceptance_item(run, item):
            continue
        return _checked_outcome(run, item)
    return None


def _host_options(command) -> None:
    command.add_argument("--source", type=Path, help="Real sealed run or digestion report")
    command.add_argument("--initial-task-id")
    command.add_argument("--checker-id", default="", help="Host-selected acceptance checker identity")
    command.add_argument("--checker-source", type=Path, action="append", default=[],
                         help="Checker implementation file whose current bytes must remain bound")
    command.add_argument("--max-evaluations", type=int, choices=range(1, 11), default=10)
    command.add_argument("--response-profile", choices=("legacy-v1", "compact-v1", "compact-v2"), default="legacy-v1",
                         help="Versioned role prompt; compact enables strict provider JSON schema")
    command.add_argument("--context-profile", choices=("legacy-v1", "bounded-v1"), default=None,
                         help="Evidence view for new runs (default: bounded-v1); independent of reply format")
    command.add_argument("--density-dimension", type=int, default=128, metavar="28..1024",
                         help="Ordered-feature density observer dimension (default: 128)")
    command.add_argument("--forge-organization", choices=("on", "off"), default="on",
                         help="Organize the preserved seed once before PFP preparation")
    command.add_argument("--schedule", default=None,
                         help="Declared Retinue schedule from retinue_schedules.yaml (default: full Retinue)")
    command.add_argument("--preset", choices=("all-anthropic", "cross-family", "cheap-falsifiers"),
                         default=None, help="Declared Retinue preset mapping seat tiers to models (F4)")
    command.add_argument("--operads", type=Path, default=None,
                         help="Reviewed prompt-family operad registry; attaches each operad to its named seats")
    command.add_argument("--clarification-policy", choices=("strict-query-v1",),
                         help="Opt-in checked missing-input residual; requires compact-v2 and original checker")
    command.add_argument("--artifact-schema", type=Path,
                         help="Closed JSON-object answer schema for a compact builder/repairer")
    command.add_argument("--task-premises", type=Path, help="Explicit current task inputs; absent inputs stay absent")
    command.add_argument("--reuse-receipt", type=Path, help="Result of a checked registered reuse operation")
    command.add_argument("--reuse-receipt-sha256", default="", help="Exact current checked reuse receipt digest")
    for name in ("builder", "reviewer", "repairer", "deliverable", "scene"):
        command.add_argument("--" + name, default="", help="Task guidance; required governed roles remain")
    for name in ("constraint", "acceptance", "skill", "anti-skill"):
        command.add_argument("--" + name, action="append", default=[])
    command.add_argument("--native-host", type=Path, help="Explicit native executable pinned before model work")
    command.add_argument("--native-host-sha256", default="")
    command.add_argument("--native-gate-witness", type=Path, help="Host-selected typed native witness JSON")
    command.add_argument("--native-gate-scope", type=Path,
                         help="Host-selected JSON map of all six native checkpoints to required gate IDs")
    command.add_argument("--native-gate-source", type=Path, action="append", default=[])
    command.add_argument("--native-gate-policy", choices=("diagnostic", "require_pass"), default="diagnostic")
    command.add_argument("--native-receipts", type=Path)
    command.add_argument("--process-observer-config", type=Path,
                         help="Explicit operator JSON pinning existing observation trust and private PEM")
    command.add_argument("--kernel-check-config", type=Path,
                         help="Explicit operator JSON pinning proof artifact, Lake, statements and observation trust")
    command.add_argument("--resource-check-config", type=Path,
                         help="Opt-in pinned sandbox and limits for the original checker")
    command.add_argument("--historical-v3", action="store_true",
                         help="Explicit compatibility workflow; native gates remain unmeasured")
    command.add_argument("--check-command", nargs=argparse.REMAINDER, default=[],
                         help="Host-selected acceptance argv; place this option last")


def _gate_scope(parsed):
    scope_path = getattr(parsed, "native_gate_scope", None)
    gate_scope = decode_native_json(scope_path.read_bytes()) if scope_path is not None else None
    if scope_path is None:
        return gate_scope
    if type(gate_scope) is not dict:
        raise ValueError("NATIVE_GATE_SCOPE_INVALID: expected a checkpoint map")
    if parsed.historical_v3:
        raise ValueError("NATIVE_GATE_SCOPE_NATIVE_WORKFLOW_REQUIRED")
    return gate_scope


def _refuse_historical_native_configs(parsed) -> None:
    if parsed.process_observer_config and parsed.historical_v3:
        raise ValueError("PROCESS_OBSERVER_NATIVE_WORKFLOW_REQUIRED")
    if parsed.kernel_check_config and parsed.historical_v3:
        raise ValueError("KERNEL_CHECK_NATIVE_WORKFLOW_REQUIRED")
    if parsed.resource_check_config and parsed.historical_v3:
        raise ValueError("RESOURCE_CHECK_NATIVE_WORKFLOW_REQUIRED")


def _bound_process_observer(parsed):
    if not parsed.process_observer_config:
        return None
    from ..infrastructure.teamwork_process_observation import bind_process_observer_config

    return bind_process_observer_config(parsed.process_observer_config)


def _bound_kernel_check(parsed):
    if not parsed.kernel_check_config:
        return None
    from ..infrastructure.teamwork_kernel_observation import bind_kernel_check_config

    return bind_kernel_check_config(parsed.kernel_check_config)


def _bound_resource_check(parsed):
    if not parsed.resource_check_config:
        return None
    from ..infrastructure.teamwork_resource_observation import bind_resource_check_config

    return bind_resource_check_config(parsed.resource_check_config)


def _native_receipt_directory(parsed):
    return parsed.native_receipts or (
        parsed.state.parent / (parsed.state.stem + ".native-gates") if parsed.state else None)


def _require_bound_observers(native_check, process_observer, kernel_check, resource_check, gate_scope) -> None:
    if process_observer is not None and native_check.process_observer is None:
        raise ValueError("PROCESS_OBSERVER_NATIVE_HOST_REQUIRED")
    if kernel_check is not None and native_check.kernel_check is None:
        raise ValueError("KERNEL_CHECK_NATIVE_HOST_REQUIRED")
    if resource_check is not None and native_check.resource_check is None:
        raise ValueError("RESOURCE_CHECK_NATIVE_HOST_REQUIRED")
    if gate_scope is not None and native_check.unavailable_reason:
        raise ValueError("NATIVE_GATE_SCOPE_NATIVE_HOST_REQUIRED")


def _bind_native_check(parsed, gate_scope):
    from ..infrastructure.teamwork_native_gates import bind_native_gate_check
    from ..infrastructure.teamwork_retinue import _default_native_gate_check

    selected = parsed.native_host or _default_native_gate_check().binary_path or None
    if gate_scope is not None and not selected:
        raise ValueError("NATIVE_GATE_SCOPE_NATIVE_HOST_REQUIRED")
    directory = _native_receipt_directory(parsed)
    process_observer = _bound_process_observer(parsed)
    kernel_check = _bound_kernel_check(parsed)
    resource_check = _bound_resource_check(parsed)
    native_check = (bind_native_gate_check(binary_path=selected, witness_path=parsed.native_gate_witness,
        source_paths=parsed.native_gate_source, policy=parsed.native_gate_policy,
        receipt_directory=directory, process_observer=process_observer, kernel_check=kernel_check,
        resource_check=resource_check, gate_scope=gate_scope)
        if selected else _default_native_gate_check())
    _require_bound_observers(native_check, process_observer, kernel_check, resource_check, gate_scope)
    if parsed.native_host_sha256 and native_check.binary_sha256 != parsed.native_host_sha256:
        raise ValueError("NATIVE_GATE_BINARY_CHANGED")
    return native_check


def _new_run_id(parsed, source):
    return getattr(parsed, "run_id", None) or (parsed.initial_task_id if source is None else None)


def _new_task(parsed, objective):
    from ..infrastructure.teamwork_intelligence_host import (
        bind_acceptance,
        bind_episode_admission,
        read_intelligence,
    )

    gate_scope = _gate_scope(parsed)
    if parsed.source and not parsed.initial_task_id:
        raise ValueError("INITIAL_TASK_REQUIRED: identify the original task at intake")
    acceptance = bind_acceptance(parsed.checker_id, tuple(parsed.check_command),
                                 source_paths=parsed.checker_source)
    source = (read_intelligence(parsed.source, initial_task_id=parsed.initial_task_id)
              if parsed.source else None)
    _refuse_historical_native_configs(parsed)
    native_check = _bind_native_check(parsed, gate_scope) if not parsed.historical_v3 else None
    task = create_teamwork_run(objective, executor=getattr(parsed, "executor", "ide"),
        run_id=_new_run_id(parsed, source),
        max_repairs=parsed.max_repairs, intelligence=source, checker_id=parsed.checker_id,
        check_command=tuple(parsed.check_command), max_actions=getattr(parsed, "max_actions", 48),
        max_evaluations=parsed.max_evaluations, learn_after_run=parsed.learn_after_run,
        acceptance_check=acceptance, brief=_task_brief(parsed), native_gate_check=native_check,
        historical_v3=parsed.historical_v3, density_dimension=parsed.density_dimension,
        forge_organization=parsed.forge_organization == "on",
        schedule=getattr(parsed, "schedule", None))
    if getattr(parsed, "preset", None):
        from ..use_cases.teamwork import apply_preset_to_run

        task = apply_preset_to_run(task, parsed.preset)
    if parsed.state:
        if parsed.state.exists():
            raise ValueError("STATE_EXISTS: preserve the original run state")
        task = task.model_copy(update={"episode_binding": bind_episode_admission(
            task, parsed.state.with_suffix(".episodes.sqlite3"))})
    return task


def _learning_command(parsed) -> int:
    from ..infrastructure.report_learning_host import intake_reports, learn_from_reports

    if parsed.command == "intake":
        revision = parsed.revision
        if revision is None:
            import subprocess

            result = subprocess.run(["git", "-C", str(parsed.repo_root), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=False)
            if result.returncode:
                raise ValueError("SOURCE_REVISION_REQUIRED: use --revision for an unversioned corpus")
            revision = result.stdout.strip()
        packet = intake_reports(parsed.repo_root, parsed.source, revision=revision)
    else:
        packet = learn_from_reports(parsed.repo_root,
            json.loads(parsed.intake.read_text(encoding="utf-8")),
            json.loads(parsed.lessons.read_text(encoding="utf-8")))
    parsed.output.parent.mkdir(parents=True, exist_ok=True)
    with parsed.output.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(packet, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": packet.get("status", "OBSERVED"), "output": str(parsed.output),
        "authority_effect": "None", "coverage_gaps": packet["coverage_gaps"],
        "next_worker_brief": packet.get("next_worker_brief"),
        "post_run_learning": {"status": "HOST_ACTION_REQUIRED", "mode": "post-run",
            "skills": ["/auto-oe-autop", "/auto-learn"],
            "instructions": POST_RUN_LEARNING_INSTRUCTIONS, "automatic_execution": False}}))
    return 0


def _add_reuse(commands) -> None:
    reuse = commands.add_parser("reuse", help="Apply a registered DDC recipe with fresh host checks, no LLM")
    reuse.add_argument("--registry", type=Path, required=True)
    reuse.add_argument("--registry-sha256", required=True)
    reuse.add_argument("--recipe-id", required=True)
    reuse.add_argument("--seed", required=True)
    reuse.add_argument("--premises", type=Path, required=True)
    reuse.add_argument("--contract-sha256", required=True)
    reuse.add_argument("--output", type=Path, required=True)
    reuse.add_argument("--receipt", type=Path, required=True)
    reuse.add_argument("--check-command", nargs=argparse.REMAINDER, required=True)


def _add_start(commands) -> None:
    start = commands.add_parser("start", help="Start IDE work and return the first host action")
    start.add_argument("--state", type=Path, required=True)
    start.add_argument("--objective", required=True)
    start.add_argument("--run-id", default=None)
    start.add_argument("--max-repairs", type=int, choices=range(4), default=1)
    start.add_argument("--max-actions", type=int, default=48)
    start.add_argument("--learn-after-run", action=argparse.BooleanOptionalAction, default=True,
                       help="Finish with scoped AutoP/auto-learn in the bound host (default: enabled)")
    start.add_argument("--brief", type=Path, help="Source-bound learned report for the next worker")
    start.add_argument("--repo-root", type=Path, default=Path.cwd())
    _host_options(start)


def _add_learning_parsers(commands) -> None:
    for name in ("intake", "learn"):
        command = commands.add_parser(name, help="Read reports" if name == "intake" else "Prepare candidate lessons and a worker brief")
        command.add_argument("--repo-root", type=Path, default=Path.cwd())
        command.add_argument("--output", type=Path, required=True, help="New report path; sources are retained")
        if name == "intake":
            command.add_argument("--source", type=Path, action="append", required=True)
            command.add_argument("--revision", help="Source revision/context; defaults to repository HEAD")
        else:
            command.add_argument("--intake", type=Path, required=True)
            command.add_argument("--lessons", type=Path, required=True, help="Host-authored list using existing lesson fields")


def _add_turn_parsers(commands) -> None:
    for name in ("next", "submit", "persist"):
        command = commands.add_parser(name)
        command.add_argument("--state", type=Path, required=True)
        if name == "submit":
            submitted = command.add_mutually_exclusive_group(required=True)
            submitted.add_argument("--result", type=Path, help="Retired unchecked submission; use --raw-reply")
            submitted.add_argument("--raw-reply", type=Path, help="Exact current-IDE PFP reply bytes")
            command.add_argument("--host-result", type=Path,
                help="Separate host artifact observation; never substitutes for the PFP reply")
            command.add_argument("--worker", default="current IDE session")
        elif name == "persist":
            command.add_argument("--snapshot-key", help="Explicit new immutable bundle name; logical run ID stays unchanged")


def _add_host_parsers(commands) -> None:
    for name in ("check", "native-gates", "recheck", "digest", "ddc-store", "ddc-complete", "ddc-read"):
        command = commands.add_parser(name)
        command.add_argument("--state", type=Path, required=True)
        if name == "recheck":
            command.add_argument("--timeout-seconds", type=int, choices=range(1, 301), default=60,
                                 metavar="1..300", help="Explicit host check allowance; default: 60")
        if name == "digest":
            command.add_argument("--source", type=Path,
                                 help="Existing digestion report; otherwise digest this run's actual observations")
        if name in ("digest", "ddc-store", "ddc-complete"):
            command.add_argument("--output-dir", type=Path,
                                 help="Native DDC bundle parent; defaults to canonical Woland storage")


def _add_unavailable(commands) -> None:
    unavailable = commands.add_parser("tool-unavailable", help="Record an actual optional tool alternative for the same role")
    unavailable.add_argument("--state", type=Path, required=True)
    unavailable.add_argument("--tool", required=True)
    unavailable.add_argument("--reason", required=True)
    unavailable.add_argument("--optional", action="store_true")
    unavailable.add_argument("--alternative", default="")
    unavailable.add_argument("--operator", default="")
    unavailable.add_argument("--scene", default="")
    unavailable.add_argument("--skill", action="append", default=[])
    unavailable.add_argument("--worker", default="current IDE session")


def _add_resume(commands) -> None:
    resume = commands.add_parser("resume", help="Continue work using its original host and financial binding")
    resume.add_argument("--state", type=Path, required=True)
    resume.add_argument("--output", type=Path, required=True, help="New state path; preserve old bytes")
    resume.add_argument("--reason", required=True)
    resume.add_argument("--additional-repairs", type=int, choices=range(4), default=0)
    resume.add_argument("--additional-actions", type=int, default=0)


def _add_cleanup(commands) -> None:
    cleanup = commands.add_parser("cleanup", help="Remove explicitly named eligible disposable copies")
    cleanup.add_argument("--state", type=Path, required=True)
    cleanup.add_argument("--plan", type=Path, required=True, help="Operator-authored working-copy/retention plan")
    cleanup.add_argument("--receipt", type=Path, required=True, help="New preserved before/after receipt")


def _add_run(commands) -> None:
    run = commands.add_parser("run", help="Bind a remote provider template, or return an unbound IDE action")
    run.add_argument("--executor", choices=("ide", "openrouter", "anthropic"), default="ide")
    run.add_argument("--objective", required=True)
    run.add_argument("--state", type=Path)
    run.add_argument("--output", type=Path, help="Explicit new text artifact; remote cannot choose paths")
    run.add_argument("--model")
    run.add_argument("--max-output-tokens", type=int, default=1024)
    run.add_argument("--max-provider-calls", type=int,
                     help="Continuing call allowance: default 42 for estimates, 32 for hard policy")
    run.add_argument("--max-repairs", type=int, choices=range(4), default=1)
    run.add_argument("--max-actions", type=int, default=48)
    run.add_argument("--run-id")
    run.add_argument("--learn-after-run", action=argparse.BooleanOptionalAction, default=True,
                     help="Finish with IDE learning or explicitly proposed-only provider lessons")
    run.add_argument("--env-file", type=Path)
    run.add_argument("--pricing-snapshot", type=Path,
        help="Operator-pinned price snapshot (required by the anthropic template)")
    run.add_argument("--effort", choices=("low", "medium", "high", "xhigh", "max"),
        help="Thinking effort for templates that support it (anthropic)")
    policy = run.add_mutually_exclusive_group()
    policy.add_argument("--max-estimated-cost-microusd", type=int,
        help="Continuing estimated budget; not a vendor-enforced maximum bill")
    policy.add_argument("--max-cost-microusd", type=int,
        help="Hard ceiling (at most 50000); refuses before dispatch if transport cannot enforce it")
    policy.add_argument("--allow-unbounded-cost", action="store_true",
                        help="Retired for canonical teamwork: a run-wide ceiling is required")
    _host_options(run)


def _build_parser():
    parser = argparse.ArgumentParser(description="Woland practical teamwork: one shared backend")
    commands = parser.add_subparsers(dest="command", required=True)
    _add_reuse(commands)
    _add_start(commands)
    _add_learning_parsers(commands)
    _add_turn_parsers(commands)
    _add_host_parsers(commands)
    _add_unavailable(commands)
    _add_resume(commands)
    _add_cleanup(commands)
    _add_run(commands)
    return parser


def _command_start(parsed) -> int:
    objective = parsed.objective
    if parsed.brief:
        from ..infrastructure.report_learning_host import load_worker_brief

        objective += "\n\n" + load_worker_brief(parsed.repo_root, parsed.brief)
    task = _new_task(parsed, objective)
    _save(parsed.state, task, new=True)
    _report(task, state_path=parsed.state)
    return 2 if task.work_status == "blocked" else 0


def _run_ide(parsed, task) -> int:
    if task.brief and task.brief.density_dimension is not None:
        parsed.state = parsed.state or default_state_path(task)
    if parsed.state:
        _save(parsed.state, task, new=True)
    _report(task, state_path=parsed.state, executor_binding="IDE_SESSION_REQUIRED")
    return 0


def _open_run_remote(parsed, task, remote_factory):
    durable_scope = ({"run_id": task.run_id, "objective_sha256":
        hashlib.sha256(task.objective.encode("utf-8")).hexdigest()}
        if parsed.max_cost_microusd is not None or parsed.max_estimated_cost_microusd is not None else {})
    template_options, snapshot_raw = {}, None
    if parsed.pricing_snapshot is not None:
        snapshot_raw = parsed.pricing_snapshot.read_bytes()
        template_options["pricing_snapshot"] = json.loads(snapshot_raw)
    if parsed.effort is not None:
        template_options["effort"] = parsed.effort
    if getattr(parsed, "preset", None) is not None:
        template_options["preset"] = parsed.preset
    remote = remote_factory(parsed.executor)(
        parsed.model, parsed.max_output_tokens, env_file=parsed.env_file,
        max_cost_microusd=parsed.max_cost_microusd,
        allow_unbounded_cost=parsed.allow_unbounded_cost,
        max_estimated_cost_microusd=parsed.max_estimated_cost_microusd,
        max_calls=parsed.max_provider_calls,
        accounting_path=parsed.state.with_suffix(".budget.sqlite3"),
        max_reply_repairs=parsed.max_repairs,
        **durable_scope, **template_options,
    )
    return remote, snapshot_raw


def _run_provider_binding(parsed, remote, snapshot_raw):
    return {
        "run_budget": getattr(getattr(remote, "gateway", None), "binding", None),
        "model": remote.model, "max_output_tokens": parsed.max_output_tokens,
        "max_reply_repairs": parsed.max_repairs,
        "output_path": str(parsed.output.resolve()),
        "env_file": str(parsed.env_file.resolve()) if parsed.env_file else None,
        **({"pricing_snapshot_path": str(parsed.pricing_snapshot.resolve()),
            "pricing_snapshot_sha256": hashlib.sha256(snapshot_raw).hexdigest()}
           if snapshot_raw is not None else {}),
        **({"effort": parsed.effort} if parsed.effort is not None else {}),
        **({"preset": parsed.preset} if getattr(parsed, "preset", None) is not None else {}),
        "financial_policy": dict(max_cost_microusd=parsed.max_cost_microusd,
            max_estimated_cost_microusd=parsed.max_estimated_cost_microusd,
            allow_unbounded_cost=parsed.allow_unbounded_cost),
    }


def _run_remote(parsed, task) -> int:
    if parsed.state is None or parsed.output is None or not parsed.model:
        raise ValueError("Remote executors require --state, --output and --model")
    if parsed.output.exists() or parsed.output.resolve() == parsed.state.resolve():
        raise ValueError("OUTPUT_EXISTS_OR_CONFLICTS: choose a new artifact path")
    from ..infrastructure.teamwork_file_host import file_text_executor
    from ..infrastructure.teamwork_remote import remote_factory

    remote, snapshot_raw = _open_run_remote(parsed, task, remote_factory)
    task = task.model_copy(update={"provider_binding": _run_provider_binding(parsed, remote, snapshot_raw)})
    _save(parsed.state, task, new=True)
    task = drive_teamwork(task, file_text_executor(remote, parsed.output,
        run_reader=lambda: TeamworkRun.model_validate_json(parsed.state.read_bytes())),
        checkpoint=lambda updated: _save(parsed.state, updated))
    _report(task, state_path=parsed.state)
    return 2 if task.work_status == "blocked" else 0


def _command_run(parsed) -> int:
    if getattr(parsed, "preset", None) and not parsed.model:
        from ..use_cases.teamwork import load_retinue_preset

        parsed.model = load_retinue_preset(parsed.preset)["tier_frontier"]
    task = _new_task(parsed, parsed.objective)
    if parsed.executor == "ide":
        return _run_ide(parsed, task)
    return _run_remote(parsed, task)


def _load_continuing_task(parsed):
    from ..infrastructure.teamwork_intelligence_host import validate_continuation_parents

    state_bytes = parsed.state.read_bytes()
    task = TeamworkRun.model_validate_json(state_bytes)
    validate_continuation_parents(task)
    if task.feedback_policy is None and parsed.command in {
            "submit", "resume", "check", "native-gates", "recheck", "digest", "ddc-store", "ddc-complete", "tool-unavailable"}:
        raise ValueError("LEGACY_FEEDBACK_READ_ONLY: preserve historical observations and start current work")
    if task.schema_version in ("omega.woland.teamwork.v3", "omega.woland.teamwork.v4"):
        from ..infrastructure.teamwork_intelligence_host import bind_episode_admission

        if not task.episode_binding or bind_episode_admission(task,
                Path(task.episode_binding["path"]), existing=True) != task.episode_binding:
            raise ValueError("EPISODE_ADMISSION_REQUIRED: preserve the continuing host ledger")
    return task, state_bytes


def _command_next(parsed, task, state_bytes):
    return task, None


def _command_tool_unavailable(parsed, task, state_bytes):
    task = tool_unavailable(task, tool=parsed.tool, reason=parsed.reason,
        optional=parsed.optional, alternative=parsed.alternative, operator=parsed.operator,
        scene=parsed.scene, skills=tuple(parsed.skill), worker=parsed.worker)
    _save(parsed.state, task)
    return task, None


def _command_submit(parsed, task, state_bytes):
    if task.executor != "ide":
        raise ValueError("EXECUTOR_MISMATCH: submit is for current IDE session work")
    action = next_action(task)
    if action is None or action.communication != "pfp":
        raise ValueError("HOST_CHECK_REQUIRED: use check, recheck or digest for host operations")
    if parsed.raw_reply is None:
        raise ValueError("PFP_RAW_REPLY_REQUIRED: unchecked observations cannot submit a model turn")
    from ..infrastructure.teamwork_pfp import attach_teamwork_host_artifacts
    from ..use_cases.teamwork_pfp import check_teamwork_reply
    result = check_teamwork_reply(action, prepared_saved_turn(action, task.pending_prompt),
        parsed.raw_reply.read_bytes(), worker=parsed.worker,
        metadata={"cost_usd": None, "transport": "current_ide_session"})
    host_result = (TeamworkObservation.model_validate_json(
        parsed.host_result.read_text(encoding="utf-8"))
        if parsed.host_result and not result.blocked else None)
    result = attach_teamwork_host_artifacts(action, result, host_result)
    from ..infrastructure.teamwork_intelligence_host import validate_artifacts

    validate_artifacts(action, result)
    task = observe(task, result)
    _save(parsed.state, task)
    return task, None


def _command_resume(parsed, task, state_bytes):
    from ..infrastructure.teamwork_intelligence_host import validate_resume_readback

    if parsed.output.resolve() == parsed.state.resolve():
        raise ValueError("CONTINUATION_PARENT_REQUIRED: choose a new output state path")
    if parsed.output.exists():
        raise ValueError("CONTINUATION_OUTPUT_EXISTS")
    if task.executor != "ide":
        task = _resume_remote(task, parsed, state_bytes)
        _report(task, state_path=parsed.output)
        return task, 2 if task.work_status == "blocked" else 0
    task = resume_teamwork(task, parent_state_path=str(parsed.state.absolute()),
        parent_state_sha256=hashlib.sha256(state_bytes).hexdigest(), reason=parsed.reason,
        additional_repairs=parsed.additional_repairs, additional_actions=parsed.additional_actions)
    validate_resume_readback(task)
    if parsed.state.read_bytes() != state_bytes:
        raise ValueError("CONTINUATION_PARENT_CHANGED: state changed during resumption")
    _save(parsed.output, task, new=True)
    return task, None


def _command_check(parsed, task, state_bytes):
    from ..infrastructure.teamwork_retinue import run_hella_check

    action = next_action(task)
    if action is None:
        raise ValueError("TERMINAL_RUN: no host action is pending")
    task = observe(task, run_hella_check(action))
    _save(parsed.state, task)
    return task, None


def _command_host_action(parsed, task, state_bytes):
    from ..infrastructure.teamwork_intelligence_host import (
        admitted_recheck,
        digest_output,
        execute_host_action,
        validate_ddc_context,
    )

    action = next_action(task)
    if action is None:
        raise ValueError("TERMINAL_RUN: no host action is pending")
    if parsed.command == "ddc-read":
        program = validate_ddc_context(action, require_current_premises=action.kind == "learn")
        _report(task, ddc_readback=program)
        return task, 0
    if parsed.command.replace("-", "_") != action.kind:
        raise ValueError("HOST_ACTION_MISMATCH: choose the pending host operation")
    if parsed.command == "recheck":
        result = admitted_recheck(task, action, timeout=parsed.timeout_seconds)
    elif parsed.command == "digest" and parsed.source:
        result = digest_output(action, parsed.source)
    else:
        result = execute_host_action(task, action, output_dir=getattr(parsed, "output_dir", None))
    result = result.model_copy(update={"metadata": {**result.metadata,
        "role_id": action.role_id, "execution_kind": "host"}})
    task = observe(task, result)
    _save(parsed.state, task)
    return task, None


def _command_persist(parsed, task, state_bytes):
    if task.brief and task.brief.density_dimension is not None:
        from ..infrastructure.teamwork_reporting import checkpoint_reports
        reporting = checkpoint_reports(parsed.state, task, finalize=True)
        _report(task, state_path=parsed.state, reporting=reporting)
        return task, 2 if reporting["status"] == "REPORTING_FAILED" else 0
    return task, _persist(task, snapshot_key=parsed.snapshot_key)


def _command_cleanup(parsed, task, state_bytes):
    from omega_engine_operating_system.adapters.intelligence_custody.intelligence_root import (
        resolve_intelligence_repo_root,
    )

    from ..infrastructure.teamwork_cleanup_host import cleanup_working_intelligence

    cleanup_result = cleanup_working_intelligence(task,
        repo_root=resolve_intelligence_repo_root(), state_path=parsed.state,
        plan=json.loads(parsed.plan.read_text(encoding="utf-8")), receipt_path=parsed.receipt)
    _report(task, cleanup=cleanup_result)
    return task, 0 if cleanup_result["status"] == "deleted" else 2


_EXISTING_COMMANDS = {
    "next": _command_next,
    "tool-unavailable": _command_tool_unavailable,
    "submit": _command_submit,
    "resume": _command_resume,
    "check": _command_check,
    "native-gates": _command_host_action,
    "recheck": _command_host_action,
    "digest": _command_host_action,
    "ddc-store": _command_host_action,
    "ddc-complete": _command_host_action,
    "ddc-read": _command_host_action,
    "persist": _command_persist,
    "cleanup": _command_cleanup,
}


def _command_existing(parsed) -> int:
    task, state_bytes = _load_continuing_task(parsed)
    task, early = _EXISTING_COMMANDS[parsed.command](parsed, task, state_bytes)
    if early is not None:
        return early
    state_path = parsed.output if parsed.command == "resume" else parsed.state
    _report(task, state_path=state_path)
    return 2 if task.work_status == "blocked" else 0


def _dispatch(parsed) -> int:
    if parsed.command == "reuse":
        from .checked_reuse_cli import execute_reuse

        return execute_reuse(parsed)
    if parsed.command in ("intake", "learn"):
        return _learning_command(parsed)
    if parsed.command == "start":
        return _command_start(parsed)
    if parsed.command == "run":
        return _command_run(parsed)
    return _command_existing(parsed)


def main(args: Sequence[str] | None = None) -> int:
    parsed = _build_parser().parse_args(args)
    try:
        return _dispatch(parsed)
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "REFUSED", "error": str(exc), "authority_effect": "None"}))
        return 2


def _attached_operads(registry_path: Path) -> tuple:
    """Read the teamwork family's operads; each instruction must still match its recorded digest."""
    from ..use_cases.teamwork import AttachedOperad

    registry = decode_native_json(registry_path.read_bytes())
    if registry.get("schema_version") != "omega.woland.prompt-family-operads.v1":
        raise ValueError("OPERAD_REGISTRY_SCHEMA_REFUSED")
    root = next((p for p in registry_path.resolve().parents if (p / "omega_engine_operads").is_dir()), None)
    if root is None:
        raise ValueError("OPERAD_REGISTRY_ROOT_NOT_FOUND")
    attached = []
    for item in registry["families"].get("woland-teamwork-v4", []):
        guidance = (root / item["instruction_path"]).read_bytes().decode("utf-8")
        attached.append(AttachedOperad(skill_id=item["skill_id"], seats=tuple(item["seats"]),
            instruction_sha256=item["instruction_sha256"], guidance=guidance))
    return tuple(attached)


def _brief_text_values(parsed) -> dict:
    values = {key: getattr(parsed, key) for key in ("builder", "reviewer", "repairer", "deliverable", "scene")
              if getattr(parsed, key)}
    for singular, plural in (("constraint", "constraints"), ("acceptance", "acceptance"),
                             ("skill", "skills"), ("anti_skill", "anti_skills")):
        if getattr(parsed, singular):
            values[plural] = tuple(getattr(parsed, singular))
    return values


def _brief_profiles(parsed, values) -> None:
    if parsed.response_profile != "legacy-v1":
        values["response_profile"] = parsed.response_profile
    if getattr(parsed, "context_profile", None) is not None:
        values["context_profile"] = parsed.context_profile
    if getattr(parsed, "clarification_policy", None) is not None:
        values["clarification_policy"] = parsed.clarification_policy


def _read_bounded_json(path: Path, limit: int, error: str):
    raw = path.read_bytes()
    if len(raw) > limit:
        raise ValueError(error)
    return decode_native_json(raw)


def _reuse_matches_task(recipe, parsed, values, program_digest) -> bool:
    if recipe.target_task.seed != parsed.objective or "task_premises" not in values:
        return False
    return program_digest(values["task_premises"]) == program_digest(recipe.target_task.premises)


def _attach_reuse_receipt(parsed, values) -> None:
    if not parsed.reuse_receipt:
        return
    from ..domain.checked_reuse import BoundReuseFile, CheckedReuseResult
    from ..use_cases.checked_ddc_reuse import (
        load_checked_reuse_registry,
        validate_checked_reuse_result,
    )
    from ..use_cases.prompt_family_replay import _program_digest

    raw = parsed.reuse_receipt.read_bytes()
    if len(raw) > 1_048_576 or hashlib.sha256(raw).hexdigest() != parsed.reuse_receipt_sha256:
        raise ValueError("CHECKED_REUSE_RECEIPT_CHANGED")
    receipt = decode_native_json(raw)
    if receipt.get("ok") is not True:
        raise ValueError("CHECKED_REUSE_REQUIRED")
    result = CheckedReuseResult.model_validate_json(json.dumps(receipt["result"]))
    registry = load_checked_reuse_registry(Path(receipt["registry_path"]), receipt["registry_sha256"])
    recipe = next(row for row in registry.recipes if row.recipe_id == result.recipe_id)
    if not _reuse_matches_task(recipe, parsed, values, _program_digest):
        raise ValueError("CHECKED_REUSE_CURRENT_TASK_MISMATCH")
    result, candidate = validate_checked_reuse_result(registry_path=Path(receipt["registry_path"]),
        expected_registry_sha256=receipt["registry_sha256"], result=result, native_support=DefaultNativeOperationPort())
    values.update(checked_reuse_registry=BoundReuseFile(path=receipt["registry_path"],
        sha256=receipt["registry_sha256"]), checked_reuse_result=result,
        checked_reuse_candidate=candidate.decode("utf-8"))


def _task_brief(parsed) -> TeamworkBrief | None:
    values = _brief_text_values(parsed)
    _brief_profiles(parsed, values)
    if parsed.artifact_schema:
        values["artifact_schema"] = _read_bounded_json(
            parsed.artifact_schema, 16_384, "ARTIFACT_SCHEMA_TOO_LARGE")
    if parsed.task_premises:
        values["task_premises"] = _read_bounded_json(
            parsed.task_premises, 65_536, "TASK_PREMISES_TOO_LARGE")
    if getattr(parsed, "operads", None):
        values["operads"] = _attached_operads(parsed.operads)
    _attach_reuse_receipt(parsed, values)
    return TeamworkBrief(**values) if values else None


def _persist(task: TeamworkRun, *, snapshot_key: str | None = None) -> int:
    from datetime import datetime, timezone

    from omega_engine_operating_system.adapters.intelligence_custody.ic_routing import (
        intelligence_path,
    )
    from omega_engine_operating_system.adapters.intelligence_custody.intelligence_root import (
        resolve_intelligence_repo_root,
    )
    from omega_engine_operations.domain.rop.result import Err

    from ..use_cases.skill_run_persistence import persist_skill_run

    status = task.work_status if next_action(task) is None else "partial"
    if snapshot_key is None:
        snapshot_key = task.run_id
        if task.continuations:
            state_digest = hashlib.sha256(task.model_dump_json().encode("utf-8")).hexdigest()
            snapshot_key = f"{task.run_id[:64]}-c{len(task.continuations)}-{state_digest[:12]}"
    report = "# Woland teamwork\n\n" + task.objective + "\n\n" + "\n\n".join(
        f"{r.worker}: {r.summary}" for r in task.observations
    )
    persisted = persist_skill_run(
        intelligence_path(resolve_intelligence_repo_root(), "_intelligence/_woland"),
        task_key=snapshot_key, objective=task.objective, verdict="OPEN_RESIDUAL",
        source="woland_teamwork", novella_md=report,
        created_utc=datetime.now(timezone.utc).isoformat(), work_status=status,
        summary={"teamwork": task.model_dump(mode="json"), "original_task_outcome": _original_task_outcome(task)},
        dda_steps=[{"actor": r.worker, "action": r.summary} for r in task.observations],
        native_support=DefaultNativeOperationPort(),
    )
    if isinstance(persisted, Err):
        raise ValueError(f"{persisted.error.code}: {persisted.error.message}")
    _report(task, persisted_path=str(persisted.value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
