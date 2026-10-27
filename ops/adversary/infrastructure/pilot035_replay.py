"""Prefix-aware public replay; retain the checker-pinned Pilot035 source bytes."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path

from . import pilot035_play as play
from . import teamwork_intelligence_host as host
from .teamwork_native_gates import replay_native_gate_reference
from ..use_cases.teamwork import next_action, observe


def _historical_artifacts(artifacts, verified_snapshots):
    """Use only path/digest pairs from native batches already replayed here."""
    retained = tuple(path for path, digest in artifacts.items()
        if (path, digest.removeprefix("sha256:")) in verified_snapshots)
    host._current_artifacts({path: digest for path, digest in artifacts.items() if path not in retained})
    return retained


def _reproduce_not_pending(run, action, captured, decoded, stderr):
    """Reproduce the v1 state-path refusal; it never becomes finite acceptance."""
    command = action.check_command
    if (captured["exit_code"] != 2 or stderr
            or run.acceptance_check is None or command != run.acceptance_check.operation
            or len(command) != 7
            or command[1:6] != ("-B", "-m", play.__name__, "host-check", "--state")
            or decoded != {"status": "REFUSED", "reason": "PILOT035_CHECK_NOT_PENDING",
                           "authority_effect": "None"}):
        raise ValueError("PILOT035_REPLAY_CAPTURE_MISMATCH")
    target = Path(command[-1]).resolve()
    point = next((point for point in run.continuations
                  if Path(point.parent_state_path).resolve() == target), None)
    if point is None:
        raise ValueError("PILOT035_REPLAY_REFUSAL_PARENT_REQUIRED")
    host.validate_continuation_parents(run)
    parent, _config, _node, _index = play._run(target)
    if (parent.run_id != run.run_id or parent.objective != run.objective
            or parent.acceptance_check != run.acceptance_check
            or parent.episode_binding != run.episode_binding
            or parent.observations != run.observations[:point.after_observations]):
        raise ValueError("PILOT035_REPLAY_REFUSAL_PARENT_MISMATCH")
    pending = next_action(parent)
    if pending is not None and pending.kind == "recheck":
        raise ValueError("PILOT035_REPLAY_REFUSAL_NOT_REPRODUCED")


def replay(state: Path):
    """Replay the same captured checks with only then-effective continuations."""
    final, config, node, index = play._run(state)
    run = final.model_copy(update={"observations": (), "continuations": ()})
    # A replay reconstructs recorded execution, not present deliverable validity.
    # Live checks still require current bytes through the ordinary host boundary.
    latest_artifacts = {}
    for observation in final.observations:
        latest_artifacts.update(observation.artifacts)
    verified_snapshots = set()
    checks = accepted_checks = unavailable_checks = 0
    for position, observation in enumerate(final.observations):
        run = run.model_copy(update={"continuations": tuple(point for point in final.continuations
            if point.after_observations <= position)})
        action = next_action(run)
        if action is None:
            raise ValueError("PILOT035_REPLAY_EXTRA_OBSERVATION")
        host._current_checker(action)
        if action.kind == "native_gates" and observation.metadata.get("native_gate_receipt"):
            full = replay_native_gate_reference(action, observation.metadata["native_gate_receipt"])
            # Replay validates the complete snapshot set and each exact digest
            # against this action before any historical artifact is reused.
            verified_snapshots.update((path, digest.removeprefix("sha256:"))
                for path, digest in action.artifacts.items() if path in full["artifact_snapshots"])
        historical_paths = _historical_artifacts(action.artifacts, verified_snapshots)
        if action.kind in ("ddc_store", "ddc_complete") and not observation.blocked:
            retained_action = action.model_copy(update={"ddc_program": observation.ddc_program})
            if historical_paths:
                host.validate_ddc_context(retained_action, changed_paths=historical_paths)
            else:
                host.validate_ddc_context(retained_action)
        if action.kind == "recheck" and observation.check is not None:
            captured = observation.metadata.get("checker_capture", {})
            raw = bytes.fromhex(captured["stdout_hex"])
            stderr = bytes.fromhex(captured["stderr_hex"])
            if (captured.get("command") != list(action.check_command)
                    or type(captured.get("exit_code")) is not int
                    or captured["exit_code"] != observation.check.exit_status
                    or captured.get("authority_effect") != "None"
                    or captured.get("authenticated") is not False
                    or sha256(raw + b"\n--- stderr ---\n" + stderr).hexdigest()
                        != observation.check.output_sha256):
                raise ValueError("PILOT035_REPLAY_CAPTURE_MISMATCH")
            decoded = play._load_text(raw.decode("utf-8"))
            if captured["exit_code"] == 2:
                _reproduce_not_pending(run, action, captured, decoded, stderr)
                unavailable_checks += 1
            else:
                actual = play._evaluate(config, node, index, action.candidate)
                if "adversary.infrastructure.pilot035_continuation" in action.check_command:
                    from .pilot035_continuation import check_binding

                    actual = {**actual, "continuation_binding": check_binding(run, action)}
                if captured["exit_code"] != (0 if actual["accepted"] else 1):
                    raise ValueError("PILOT035_REPLAY_CAPTURE_MISMATCH")
                if decoded != actual:
                    raise ValueError("PILOT035_REPLAY_CHECK_MISMATCH")
                accepted_checks += int(actual["accepted"])
            checks += 1
        run = observe(run, observation)
    if not checks:
        raise ValueError("PILOT035_REPLAY_NO_ORIGINAL_CHECK")
    # Include a continuation exactly at the final prefix, and let the existing
    # coordinator reject any marker beyond the retained observation boundary.
    run = run.model_copy(update={"continuations": final.continuations})
    historical_paths = _historical_artifacts(latest_artifacts, verified_snapshots)
    return dict(status="REPLAYED", original_checks=checks, external_provider_dispatches=0,
        panel_coverage=run.panel_coverage, work_status=run.work_status, authority_effect="None",
        **({"artifact_readback_scope": "HISTORICAL_EXECUTION_ONLY",
            "retained_artifact_paths": list(historical_paths)} if historical_paths else {}),
        **({"accepted_checks": accepted_checks, "reproduced_unavailable_checks": unavailable_checks}
           if unavailable_checks else {}))


def main(args=None):
    parser = argparse.ArgumentParser(description="Replay retained Pilot035 through the shared Adversary boundary")
    parser.add_argument("--state", type=Path, required=True)
    parsed = parser.parse_args(args)
    try:
        result = replay(parsed.state.resolve())
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc), "authority_effect": "None"}))
        return 2
