"""Original demo judges composed with the existing Adversary workflow and PFP turns.

One exchange state; no model code execution, second scheduler or receipt store.
The model proposes; a deterministic review invokes the retained source judges.
"""
from __future__ import annotations

import argparse
import json
import tempfile
import time
from decimal import Decimal
from pathlib import Path

from pfp.domain.contracts.pfp_runtime import PfpTaskPrompt
from pfp.domain.pfp_ingress import strict_json
from pfp.infrastructure.challenge_execution import (
    isolated,
    normalized_case,
    source_bindings,
)
from pfp.infrastructure.challenge_live import RUNTIME_SOURCES, choose_case
from pfp.infrastructure.estimated_gateway import create_accounted_openrouter_gateway
from pfp.use_cases.pfp_prompt import public_task_input
from pfp.use_cases.pfp_proposal import REPAIR_RULES
from adversary.infrastructure.teamwork_intelligence_host import (
    admitted_recheck,
    bind_acceptance,
    bind_episode_admission,
    complete_ddc_program,
    execute_host_action,
    store_ddc_program,
    validate_ddc_context,
)
from adversary.infrastructure.teamwork_openrouter import OpenRouterTeamworkExecutor
from adversary.infrastructure.teamwork_panel import create_teamwork_run, run_syntax_prefilter_check
from adversary.tests.pilots.challenge_suite.catalog import (
    ROOT,
    canonical,
    digest,
    load_case,
    relocated,
)
from adversary.use_cases.teamwork import (
    POST_RUN_LEARNING_INSTRUCTIONS,
    HostAcceptanceRequirement,
    TaskCheck,
    TeamworkObservation,
    TeamworkRun,
    next_action,
    observe,
)
from adversary.use_cases.teamwork_pfp import (
    check_teamwork_reply,
    prepare_teamwork_turn,
)


def context(row):
    source = ROOT / relocated(row["source"])
    challenge = (ROOT / relocated(row["challenge_path"]) if "challenge_path" in row else
        next(p for p in source.parents if p.name[:4] == row["challenge"].lower()))
    case = normalized_case(row["challenge"], load_case(row))
    task = challenge / ("TASK.md" if row["challenge"] == "C005" else "participant_packet/TASK.md")
    if row["challenge"] == "C001":
        from adversary.tests.pilots.challenge_suite.c001 import TASK_PATH
        task = TASK_PATH
    if not task.is_file():
        raise ValueError("CHALLENGE_TASK_UNAVAILABLE:" + row["challenge"])
    sources = source_bindings(challenge)
    if row["challenge"] == "C001":
        from adversary.tests.pilots.challenge_suite.c001 import SOURCE_PATHS
        sources.update({p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in SOURCE_PATHS})
    for name in (*RUNTIME_SOURCES, task.relative_to(ROOT).as_posix(),
        "pfp/infrastructure/task_turn.py",
        "adversary/use_cases/teamwork_pfp.py",
        "adversary/infrastructure/teamwork_panel.py",
        "adversary/infrastructure/teamwork_openrouter.py",
        "adversary/infrastructure/teamwork_remote.py",
        "adversary/infrastructure/teamwork_intelligence_host.py",
        "adversary/use_cases/prompt_family_replay.py",
        "adversary/domain/ddc_program.py",
        "adversary/domain/native_gate_check.py",
        "adversary/infrastructure/teamwork_native_gates.py",
        "adversary/roles/adversary_panel.yaml",
        "adversary/use_cases/teamwork.py", __file__):
        path = Path(name) if Path(name).is_absolute() else ROOT / name
        sources[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
    return case, task.read_text(encoding="utf-8-sig"), sources


def start(row, *, executor="ide", max_repairs=1, learn_after_run=True, max_actions=48,
          native_gate_check=None, historical_v3=False):
    case, task_text, sources = context(row)
    schema = {"type": "object", "minProperties": 1}
    if row["challenge"] == "C001":
        from adversary.tests.pilots.challenge_suite.c001 import answer_schema, public_case

        schema, case = answer_schema(case), public_case(case)
    elif row["challenge"] == "C005":
        from pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.schemas import (
            CONSISTENCY_JSON_SCHEMA,
            CYCLE_REPAIR_JSON_SCHEMA,
        )

        schema = (CONSISTENCY_JSON_SCHEMA if case["kind"] == "consistency"
                  else CYCLE_REPAIR_JSON_SCHEMA)["schema"]
    public = public_task_input(PfpTaskPrompt("public-challenge-input", task_text, case, schema))
    source_id = digest(canonical(sources))
    run = create_teamwork_run(
        f"Attempt {row['challenge']} case {row['case_id']} using its original finite witness contract. "
        "A checked certificate does not complete the original frozen-program or neural experiment. "
        "The build/repair answer is a JSON string containing the original certificate object; "
        "the host parses it and invokes the original independent judge. Review roles inspect that "
        "candidate and the original requirements without claiming mathematical acceptance.\n"
        "Original task contract:\n" + public["objective"] + "\nOriginal public input:\n" +
        json.dumps(public["input"], ensure_ascii=False, sort_keys=True) +
        "\nOriginal witness shape:\n" + json.dumps(schema, sort_keys=True),
        executor=executor, max_repairs=max_repairs, learn_after_run=learn_after_run, max_actions=max_actions,
        native_gate_check=native_gate_check, historical_v3=historical_v3,
        acceptance_check=bind_acceptance("demo004:" + source_id,
            ("adversary", "challenge", "check", row["challenge"], row["case_id"]),
            source_paths=tuple(ROOT / name for name in sources)))
    artifacts = Path(tempfile.mkdtemp(prefix="adversary_challenge_"))
    run = run.model_copy(update={"episode_binding": bind_episode_admission(run, artifacts / "episodes.sqlite3")})
    state = dict(schema="pfp.adversary-challenge.v3" if historical_v3 else "pfp.adversary-challenge.v4", row=row, sources=sources,
                 artifact_dir=str(artifacts), ddc_output_dir=str(artifacts / "ddc"),
                 run=run.model_dump(mode="json"))
    return _advance_host(state)


def _run(state):
    if state.get("schema") not in ("pfp.adversary-challenge.v2", "pfp.adversary-challenge.v3", "pfp.adversary-challenge.v4"):
        raise ValueError("UNSUPPORTED_CHALLENGE_STATE")
    if context(state["row"])[2] != state["sources"]:
        raise ValueError("CHALLENGE_SOURCE_DRIFT")
    run = TeamworkRun.model_validate(state["run"])
    source_id = digest(canonical(state["sources"]))
    command = ("adversary", "challenge", "check", state["row"]["challenge"], state["row"]["case_id"])
    expected = (bind_acceptance("demo004:" + source_id, command,
        source_paths=tuple(ROOT / name for name in state["sources"]))
        if state["schema"] in ("pfp.adversary-challenge.v3", "pfp.adversary-challenge.v4") else HostAcceptanceRequirement(
            source_id=source_id, checker_id="demo004:" + source_id, operation=command))
    if run.acceptance_check != expected:
        raise ValueError("CHALLENGE_ACCEPTANCE_BINDING")
    return run


def _prepare(state, action):
    _run(state)
    if action.workflow_version in ("core.adversary.teamwork.v3", "core.adversary.teamwork.v4") and action.kind == "learn":
        validate_ddc_context(action)
    return prepare_teamwork_turn(action)


def _replace_run(state, run):
    return {**state, "run": run.model_dump(mode="json")}


def _accept(state, raw, *, worker, metadata=None):
    run = _run(state)
    action = next_action(run)
    if action is None or action.communication != "pfp":
        raise ValueError("NO_PENDING_PROPOSAL")
    turn = _prepare(state, action)
    result = check_teamwork_reply(action, turn, raw, worker=worker,
        metadata={"cost_usd": None, **(metadata or {})})
    if not result.blocked and action.kind in ("build", "repair"):
        result = _retain_candidate(state, action, result)
    return _replace_run(state, observe(run, result))


def _retain_candidate(state, action, result):
    """Keep real immutable candidate bytes for mandatory DDC host readback."""
    path = Path(state["artifact_dir"]) / ("candidate_" + action.action_id + ".json")
    raw = result.content.encode("utf-8")
    with path.open("xb") as handle:
        handle.write(raw)
    return result.model_copy(update={"artifacts": {**action.artifacts, str(path): digest(raw)}})


def _review(state):
    """Actual original judge at the mandatory host acceptance operation."""
    run = _run(state)
    action = next_action(run)
    if action is None or action.communication != "host" or action.kind != "recheck":
        return state
    observed = admitted_recheck(run, action, evaluator=lambda pending: _judge_observation(state, pending))
    return _replace_run(state, observe(run, observed))


def _judge_observation(state, action):
    """Invoke the original independent challenge judge inside episode admission."""
    began = time.perf_counter()
    try:
        answer = strict_json(action.candidate)
        if type(answer) is not dict:
            raise ValueError("Candidate certificate must be an object")
    except (ValueError, TypeError):
        result = dict(status="PROVIDER_COMPLETED", failure_class="TASK_ENVELOPE")
    else:
        result = isolated(dict(kind="CHECK_ANSWER", row=state["row"], answer=answer), timeout=30)
    failure = result.get("failure_class", "CHECKER")
    unavailable = result["status"] in ("INFRASTRUCTURE_ERROR", "CHECKER_DEFECT")
    accepted = result["status"] in ("HOST_ACCEPTED", "TYPED_REFUSAL")
    findings = () if accepted or unavailable else (REPAIR_RULES.get(failure, REPAIR_RULES["CERTIFICATE"]),)
    observed = TeamworkObservation(action_id=action.action_id, worker="original source judges",
        summary="Original finite task check: " + result["status"], blocked=unavailable,
        findings=findings, artifacts=action.artifacts,
        check=TaskCheck(initial_task_id=action.initial_task_id, source_id=action.check_source_id,
            checker_id=action.checker_id, command=action.check_command,
            exit_status=0 if accepted else 1, output_sha256=digest(canonical(result)),
            artifacts=action.artifacts),
        metadata={"task_check": result, "failure_code": failure, "role_id": action.role_id,
            "execution_kind": "host", "host_tools_executed": True,
            "checker_id": action.checker_id, "candidate_sha256": digest(action.candidate.encode("utf-8")),
            "elapsed_seconds": time.perf_counter() - began, "provider_calls": 0})
    return observed


def submit(state, raw):
    if _run(state).executor != "ide":
        raise ValueError("EXECUTOR_MISMATCH")
    return _advance_host(_accept(state, raw, worker="current IDE session",
        metadata={"transport": "current_ide_session"}))


def _advance_host(state):
    """Dispatch only the fixed deterministic operations of the existing plan."""
    while (action := next_action(_run(state))) is not None and action.communication != "pfp":
        if action.communication == "deterministic":
            state = _replace_run(state, observe(_run(state), run_syntax_prefilter_check(action)))
        else:
            if action.kind == "native_gates":
                result = execute_host_action(_run(state), action, output_dir=Path(state["ddc_output_dir"]))
                state = _replace_run(state, observe(_run(state), result))
            elif action.kind in ("ddc_store", "ddc_complete"):
                host = store_ddc_program if action.kind == "ddc_store" else complete_ddc_program
                try:
                    result = host(_run(state), action, output_dir=Path(state["ddc_output_dir"]))
                except (ValueError, OSError, RuntimeError) as exc:
                    result = TeamworkObservation(action_id=action.action_id, worker="challenge DDC host",
                        summary=str(exc), blocked=True, artifacts=action.artifacts,
                        metadata={"role_id": action.role_id, "execution_kind": "host",
                            "failure_code": "DDC_HOST_UNAVAILABLE"})
                state = _replace_run(state, observe(_run(state), result))
            elif action.kind != "recheck":
                raise ValueError("UNSUPPORTED_CHALLENGE_HOST_OPERATION")
            else:
                state = _review(state)
    return state


def run_bound(state, gateway, model, *, checkpoint=None):
    """Reuse one caller-owned gateway/budget through every proposal and repair."""
    if _run(state).executor != "openrouter":
        raise ValueError("EXECUTOR_MISMATCH")
    executor = OpenRouterTeamworkExecutor(gateway, model, max_reply_repairs=0)
    state = _advance_host(state)
    while (action := next_action(_run(state))) is not None:
        if action.kind == "learn":
            _prepare(state, action)
        began = time.perf_counter()
        unsettled = next((item.metadata.get("failure_code") for item in _run(state).observations
            if item.metadata.get("failure_code") in {"CompletedCostUnknown", "CompletedOverEstimatedBudget",
                "CompletedOverAdmittedBudget", "CompletedAccountingUnavailable"}), None)
        if unsettled:
            observation = TeamworkObservation(action_id=action.action_id, worker="bound OpenRouter host",
                summary="The reserved finish cannot dispatch while charged accounting is unreconciled.",
                blocked=True, metadata={"role_id": action.role_id,
                    "failure_code": "FINISH_ACCOUNTING_UNRECONCILED", "prior_failure": unsettled})
        else:
            observation = executor(action)
        observation = observation.model_copy(update={"metadata": {**observation.metadata,
            "elapsed_seconds": time.perf_counter() - began}})
        if not observation.blocked and action.kind in ("build", "repair"):
            observation = _retain_candidate(state, action, observation)
        state = _replace_run(state, observe(_run(state), observation))
        state = _advance_host(state)
        if checkpoint:
            checkpoint(state)
    return state


def replay(state):
    final = _run(state)
    run = final.model_copy(update={"observations": ()})
    replayed = _replace_run(state, run)
    for observation in final.observations:
        action = next_action(_run(replayed))
        if action.communication == "host":
            if action.kind == "native_gates":
                from .teamwork_native_gates import replay_native_gate_reference

                if observation.metadata.get("native_gate_receipt"):
                    replay_native_gate_reference(action, observation.metadata["native_gate_receipt"])
                replayed = _replace_run(replayed, observe(_run(replayed), observation))
                continue
            if action.kind in ("ddc_store", "ddc_complete"):
                if not observation.blocked:
                    validate_ddc_context(action.model_copy(update={"ddc_program": observation.ddc_program}))
                replayed = _replace_run(replayed, observe(_run(replayed), observation))
                continue
            actual = _judge_observation(replayed, action).model_dump(mode="json")
            recorded = observation.model_dump(mode="json")
            # Timing varies; every decision and candidate/checker binding must agree.
            actual["metadata"].pop("elapsed_seconds", None)
            recorded["metadata"].pop("elapsed_seconds", None)
            if canonical(actual) != canonical(recorded):
                raise ValueError("REPLAY_JUDGE_MISMATCH")
        elif action.communication == "deterministic":
            if run_syntax_prefilter_check(action) != observation:
                raise ValueError("REPLAY_SYNTAX_PREFILTER_MISMATCH")
        elif "pfp" in observation.metadata:
            _prepare(replayed, action).replay(observation.metadata["pfp"])
        # Retain exact original observations so their action identities remain stable.
        replayed = _replace_run(replayed, observe(_run(replayed), observation))
    return dict(status="REPLAYED", provider_calls=0, authority_effect="None",
        task_check=report(replayed)["task_check"])


def report(state):
    run = _run(state)
    action = next_action(run)
    prepared = _prepare(state, action).prompt.to_dict() if action and action.communication == "pfp" else None
    result = next((o.metadata["task_check"] for o in reversed(run.observations)
        if "task_check" in o.metadata), None)
    calls = [o.metadata for o in run.observations if o.metadata.get("provider") == "openrouter"]
    costs = [item["cost_usd"] for item in calls if item.get("cost_usd") is not None]
    return dict(work_status=run.work_status, challenge=state["row"]["challenge"],
        workflow_version=run.schema_version,
        case_id=state["row"]["case_id"], run_id=run.run_id, executor=run.executor,
        next_action=action.model_dump(mode="json") if action else None,
        pfp_turn=prepared, task_check=result, authority_effect="None",
        panel_coverage=run.panel_coverage,
        native_gate_coverage=run.native_gate_coverage,
        provider_replies=len(calls), ide_submissions=sum(
            o.metadata.get("transport") == "current_ide_session" for o in run.observations),
        unknown_cost_replies=len(calls) - len(costs),
        known_cost_usd=str(sum((Decimal(str(cost)) for cost in costs), Decimal(0))) if calls else None,
        observed_elapsed_seconds=sum(o.metadata.get("elapsed_seconds", 0) for o in run.observations),
        scope="Finite candidate checking; original experiment completion remains separate.",
        post_run_learning={"status": "HOST_ACTION_REQUIRED", "instructions": POST_RUN_LEARNING_INSTRUCTIONS})


def main(args=None):
    parser = argparse.ArgumentParser(description="Adversary workflow -> PFP -> original demo judge")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("start", "run", "submit", "next", "replay"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--state", type=Path, required=True)
        if name in ("start", "run"):
            cmd.add_argument("--challenge", required=True)
            cmd.add_argument("--split", choices=("development", "held_out"), default="development")
            cmd.add_argument("--ordinal", type=int, default=0)
            cmd.add_argument("--max-repairs", type=int, choices=range(4), default=1)
            cmd.add_argument("--learn-after-run", action=argparse.BooleanOptionalAction, default=True)
        if name == "run":
            cmd.add_argument("--model", required=True)
            cmd.add_argument("--max-output-tokens", type=int, default=3000)
            cmd.add_argument("--max-provider-calls", type=int, default=42)
            cmd.add_argument("--max-estimated-cost-microusd", type=int, default=50000)
            cmd.add_argument("--env-file", type=Path)
        if name == "submit":
            cmd.add_argument("--raw-reply", type=Path, required=True)
    parsed = parser.parse_args(args)

    def save(value, *, new=False):
        parsed.state.parent.mkdir(parents=True, exist_ok=True)
        with parsed.state.open("x" if new else "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    try:
        if parsed.command == "run" and not 0 < parsed.max_estimated_cost_microusd <= 50000:
            raise ValueError("RUN_COST_CAP_INVALID: keep the run-wide ceiling within $0.05")
        if parsed.command in ("start", "run"):
            state = start(choose_case(parsed.challenge, parsed.split, parsed.ordinal),
                executor="ide" if parsed.command == "start" else "openrouter",
                max_repairs=parsed.max_repairs, learn_after_run=parsed.learn_after_run)
            save(state, new=True)
            if parsed.command == "run":
                gateway = create_accounted_openrouter_gateway(parsed.model, parsed.max_output_tokens,
                    env_file=parsed.env_file, max_estimated_cost_microusd=parsed.max_estimated_cost_microusd,
                    max_calls=parsed.max_provider_calls, accounting_path=parsed.state.with_suffix(".budget.sqlite3"),
                    run_id=_run(state).run_id,
                    objective_sha256=digest(_run(state).objective.encode("utf-8")))
                state = run_bound(state, gateway, parsed.model, checkpoint=save)
        else:
            state = json.loads(parsed.state.read_bytes())
            if parsed.command == "replay":
                print(json.dumps(replay(state)))
                return 0
            if parsed.command == "submit":
                state = submit(state, parsed.raw_reply.read_bytes())
                save(state)
        print(json.dumps(report(state)))
        return 2 if _run(state).work_status in ("blocked", "partial") else 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print(json.dumps(dict(status="REFUSED", error=str(exc), authority_effect="None")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
