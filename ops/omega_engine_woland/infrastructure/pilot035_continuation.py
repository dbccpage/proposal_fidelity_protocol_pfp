"""Explicit v2 state adapter for continuing the original finite Pilot035 task.

The original checker command and source bytes remain in historical observations.
Only an operator-selected continuation gets a successor command naming its new
state. The original task, finite checker, and durable episode ledger stay fixed.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from contextlib import closing

from . import pilot035_play as play
from . import teamwork_intelligence_host as host
from .teamwork_state import save_teamwork_state
from ..use_cases.teamwork import TeamworkRun, effective_acceptance, next_action, resume_teamwork


VERSION = "pilot035.continuation-check.v2"
MODULE = "omega_engine_woland.infrastructure.pilot035_continuation"


def _command(run: TeamworkRun, state: Path) -> tuple[str, ...]:
    original = run.acceptance_check
    if (original is None or original.checker_id != "pilot035.finite-tao.v1"
            or len(original.operation) != 7
            or original.operation[1:6] != ("-B", "-m", play.__name__, "host-check", "--state")):
        raise ValueError("PILOT035_ORIGINAL_CHECK_BINDING_REQUIRED")
    return (original.operation[0], "-B", "-m", MODULE, "host-check", "--state", str(state.resolve()))


def _current(binding):
    if (binding is None or host.bind_acceptance(binding.checker_id, binding.operation,
            source_paths=tuple(binding.check_source_paths)) != binding):
        raise ValueError("CHECKER_CHANGED: retain the selected Pilot035 checker sources")


def resume(state: Path, output: Path, *, reason: str, additional_repairs: int = 0,
           additional_actions: int = 0) -> TeamworkRun:
    """Keep the parent exact; explicitly bind the new state before any dispatch."""
    state, output = Path(state).resolve(), Path(output).resolve()
    if output == state:
        raise ValueError("CONTINUATION_PARENT_REQUIRED: choose a new state path")
    if output.exists():
        raise ValueError("CONTINUATION_OUTPUT_EXISTS")
    retained = state.read_bytes()
    run, _config, _node, _index = play._run(state)
    if TeamworkRun.model_validate_json(retained) != run:
        raise ValueError("CONTINUATION_PARENT_CHANGED")
    host.validate_continuation_parents(run)
    original = effective_acceptance(run)
    _current(original)
    if not run.episode_binding or host.bind_episode_admission(run,
            Path(run.episode_binding["path"]), existing=True) != run.episode_binding:
        raise ValueError("EPISODE_ADMISSION_REQUIRED: retain the original episode ledger")
    with closing(sqlite3.connect(run.episode_binding["path"])) as ledger:
        admitted = ledger.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
    if admitted != run.continuation_status["evaluations_used"]:
        raise ValueError("EPISODE_HISTORY_MISMATCH: resume the descendant retaining every admitted evaluation")
    successor = host.bind_acceptance(original.checker_id, _command(run, output),
        source_paths=(*original.check_source_paths, state, Path(__file__)))
    continued = resume_teamwork(run, parent_state_path=str(state),
        parent_state_sha256=sha256(retained).hexdigest(), reason=reason,
        additional_repairs=additional_repairs, additional_actions=additional_actions,
        acceptance_successor=successor)
    host.validate_resume_readback(continued)
    if state.read_bytes() != retained:
        raise ValueError("CONTINUATION_PARENT_CHANGED")
    save_teamwork_state(output, continued, new=True)
    return continued


def check_binding(run: TeamworkRun, action, state: Path | None = None) -> dict:
    """Recompute the v2 boundary also during deterministic capture replay."""
    host.validate_continuation_parents(run)
    point = next((point for point in reversed(run.continuations)
                  if point.acceptance_successor is not None), None)
    binding = effective_acceptance(run)
    if point is None or binding is None:
        raise ValueError("PILOT035_CONTINUATION_BINDING_REQUIRED")
    selected_state = Path(binding.operation[-1]).resolve() if state is None else Path(state).resolve()
    if (binding.operation != _command(run, selected_state)
            or action.check_command != binding.operation
            or action.check_source_id != binding.source_id):
        raise ValueError("PILOT035_CONTINUATION_BINDING_MISMATCH")
    parent, _config, _node, _index = play._run(Path(point.parent_state_path))
    # The generic continuation validator binds complete ancestor history. Keep an
    # adapter-specific refusal for any attempted task/config/checker replacement.
    if (run.run_id != parent.run_id or run.objective != parent.objective
            or run.acceptance_check != parent.acceptance_check or run.brief != parent.brief
            or run.episode_binding != parent.episode_binding):
        raise ValueError("PILOT035_CONTINUATION_SCOPE_CHANGED")
    predecessor = effective_acceptance(parent)
    _current(binding)
    return {"schema_version": VERSION, "action_id": action.action_id,
        "state_path": str(selected_state), "parent_state_path": point.parent_state_path,
        "parent_state_sha256": point.parent_state_sha256,
        "predecessor_check_source_id": predecessor.source_id,
        "original_check_source_id": run.acceptance_check.source_id,
        "candidate_sha256": sha256(action.candidate.encode("utf-8")).hexdigest()}


def check(state: Path) -> dict:
    run, config, node, index = play._run(Path(state))
    action = next_action(run)
    if action is None or action.kind != "recheck":
        raise ValueError("PILOT035_CHECK_NOT_PENDING")
    provenance = check_binding(run, action, state)
    host._current_artifacts(action.artifacts)
    if not run.episode_binding or host.bind_episode_admission(run,
            Path(run.episode_binding["path"]), existing=True) != run.episode_binding:
        raise ValueError("EPISODE_ADMISSION_REQUIRED")
    result = play._evaluate(config, node, index, action.candidate)
    host.validate_continuation_parents(run)
    host._current_checker(action)
    host._current_artifacts(action.artifacts)
    return {**result, "continuation_binding": provenance}


def main(args=None):
    parser = argparse.ArgumentParser(description="Continue the original finite Pilot035 in a new bound state")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("resume", "host-check"):
        command = commands.add_parser(name)
        command.add_argument("--state", type=Path, required=True)
        if name == "resume":
            command.add_argument("--output", type=Path, required=True)
            command.add_argument("--reason", required=True)
            command.add_argument("--additional-actions", type=int, default=0)
            command.add_argument("--additional-repairs", type=int, default=0)
    parsed = parser.parse_args(args)
    try:
        if parsed.command == "resume":
            run = resume(parsed.state, parsed.output, reason=parsed.reason,
                additional_actions=parsed.additional_actions, additional_repairs=parsed.additional_repairs)
            result = {"status": "CONTINUED", "adapter_version": VERSION,
                "state_path": str(parsed.output.resolve()), "run_id": run.run_id,
                "continuation": run.continuation_status, "external_provider_dispatches": 0,
                "authority_effect": "None"}
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            return 0
        result = check(parsed.state)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["accepted"] else 1
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc), "authority_effect": "None"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
