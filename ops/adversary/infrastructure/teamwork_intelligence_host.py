"""Host readback/checks, not a scheduler or an authenticated evidence service.

Commands are selected by the operator at intake, never read from model output.
The existing native source/lifecycle/retention decisions remain separate.
Origin: adversary/infrastructure/teamwork_intelligence_host.py.
The claim is that host commands are operator-selected at intake, not read from model output.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

from adversary.infrastructure.native import DefaultNativeOperationPort

from ..use_cases.intelligence_digestion.archive_custody import bundle_entries
from ..use_cases.intelligence_digestion.digestion_service import (
    read_run_findings,
    read_teamwork_findings,
)
from ..use_cases.teamwork import (
    IntelligenceRead,
    TaskCheck,
    TeamworkAction,
    TeamworkObservation,
    TeamworkRun,
    intelligence_sources,
    next_action,
)


def _source_digest(path: Path) -> str:
    entries = bundle_entries(path.absolute().parent, path.absolute())
    # Named host-read profile; not RFC 8785 or a native lifecycle SourceId.
    wire = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(("adversary.host-read.v1\n" + wire).encode()).hexdigest()


def read_intelligence(path: Path, *, initial_task_id: str,
                      parent_source_id: str | None = None) -> IntelligenceRead:
    before = _source_digest(path)
    extracted = read_run_findings(path, native_support=DefaultNativeOperationPort())
    if _source_digest(path) != before:
        raise ValueError("SOURCE_CHANGED: intelligence changed during intake")
    return IntelligenceRead(initial_task_id=initial_task_id, source_id=before,
        source_locator=str(path), parent_source_id=parent_source_id,
        findings=tuple(extracted.findings),
        coverage_gaps=tuple((*extracted.coverage_gaps, *extracted.parse_residuals)))


def _current_source(action: TeamworkAction) -> None:
    for source in action.source_reads or (action.intelligence,):
        if source is None:
            continue
        if _source_digest(Path(source.source_locator)) != source.source_id:
            raise ValueError("SOURCE_CHANGED: read the changed intelligence in a new scoped task")
        current = read_intelligence(Path(source.source_locator),
            initial_task_id=source.initial_task_id, parent_source_id=source.parent_source_id)
        if (set(current.findings) != set(source.findings)
                or set(current.coverage_gaps) != set(source.coverage_gaps)):
            raise ValueError("SOURCE_INTERPRETATION_CHANGED: re-intake changed findings or coverage")


def bind_acceptance(checker_id: str, command: tuple[str, ...], *, source_paths=()):
    """Bind the operator's checker selection and any declared implementation files."""
    from ..use_cases.teamwork import HostAcceptanceRequirement

    if (not isinstance(checker_id, str) or not checker_id.strip() or not command
            or any(not isinstance(part, str) or not part.strip() for part in command)):
        raise ValueError("ACCEPTANCE_BINDING_REQUIRED: select --checker-id and --check-command")
    files = {str(Path(path).absolute()): hashlib.sha256(Path(path).read_bytes()).hexdigest()
             for path in source_paths}
    _current_artifacts(files)
    payload = {"checker_id": checker_id, "operation": list(command), "source_paths": files}
    wire = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return HostAcceptanceRequirement(checker_id=checker_id, operation=command,
        source_id=hashlib.sha256(("adversary.host-acceptance.v1\n" + wire).encode()).hexdigest(),
        check_source_paths=files)


def _current_checker(action: TeamworkAction) -> None:
    if not action.check_source_id:
        return
    _current_artifacts(action.check_source_paths)
    expected = bind_acceptance(action.checker_id, action.check_command,
                              source_paths=tuple(action.check_source_paths))
    if expected.source_id != action.check_source_id:
        raise ValueError("CHECKER_CHANGED: host acceptance command or source binding differs")


def validate_continuation_parents(run: TeamworkRun) -> None:
    for position, point in enumerate(run.continuations):
        path = Path(point.parent_state_path)
        entries = bundle_entries(path.absolute().parent, path.absolute())
        if len(entries) != 1 or entries[0]["sha256"] != "sha256:" + point.parent_state_sha256:
            raise ValueError("CONTINUATION_PARENT_CHANGED: preserve the exact stopped state")
        if point.acceptance_successor is not None:
            # Successor wrappers carry a new execution path, never a different task,
            # earlier history or budget. Historical markers keep their old reader.
            from ..domain.native_gate_check import decode_native_json

            parent = TeamworkRun.model_validate(decode_native_json(path.read_bytes()))
            excluded = {"observations", "continuations", "pending_prompt"}
            if (parent.model_dump(exclude=excluded) != run.model_dump(exclude=excluded)
                    or len(parent.observations) != point.after_observations
                    or parent.observations != run.observations[:point.after_observations]
                    or parent.continuations != run.continuations[:position]):
                raise ValueError("CONTINUATION_PARENT_SCOPE_MISMATCH: retain task, history and budget")


def validate_resume_readback(run: TeamworkRun) -> None:
    validate_continuation_parents(run)
    action = next_action(run)
    if action:
        from .teamwork_native_gates import validate_native_gate_context

        validate_native_gate_context(action)
        _current_source(action)
        _current_checker(action)
        if action.kind not in ("build", "repair"):
            _current_artifacts(action.artifacts)
        if action.ddc_program is not None:
            validate_ddc_context(action, require_current_premises=action.kind == "learn")


def _current_artifacts(artifacts: dict[str, str]) -> None:
    if not isinstance(artifacts, dict) or any(
        not isinstance(name, str) or not name or not isinstance(expected, str)
        or re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", expected) is None
        for name, expected in artifacts.items()
    ):
        raise ValueError("ARTIFACT_HASHES_INVALID: require file paths and SHA256 strings")
    for name, expected in artifacts.items():
        entries = bundle_entries(Path(name).absolute().parent, Path(name).absolute())
        if len(entries) != 1 or entries[0]["sha256"].removeprefix("sha256:") != expected.removeprefix("sha256:"):
            raise ValueError(f"ARTIFACT_CHANGED: {name}")


def validate_artifacts(action: TeamworkAction, result: TeamworkObservation) -> None:
    """Read actual output bytes at the IDE submission boundary."""
    if result.blocked:
        return
    _current_source(action)
    _current_checker(action)
    if action.phase == "learning_review":
        validate_learning_context(action)
    learning_application = action.kind == "learn" and (
        bool(result.metadata.get("changed_paths")) or bool(result.artifacts)
    )
    if action.kind not in ("build", "repair") and not learning_application:
        _current_artifacts(action.artifacts)
        if result.artifacts and result.artifacts != action.artifacts:
            raise ValueError("ARTIFACT_REBINDING: only application may change output bytes")
    _current_artifacts(result.artifacts)
    _current_source(action)


def recheck(action: TeamworkAction, *, timeout: float = 60, run=None) -> TeamworkObservation:
    """V3 execution requires the continuing run's durable admission ledger."""
    if action.workflow_version in ("core.adversary.teamwork.v3", "core.adversary.teamwork.v4"):
        if run is None:
            raise ValueError("EPISODE_ADMISSION_REQUIRED: use the bound run before host dispatch")
        return admitted_recheck(run, action, timeout=timeout)
    return _execute_recheck(action, timeout=timeout)


def _require_recheck_dispatch(action: TeamworkAction) -> None:
    if action.kind != "recheck" or not action.checker_id or not action.check_command:
        raise ValueError("RECHECK_NOT_PENDING")
    if action.workflow_version in ("core.adversary.teamwork.v3", "core.adversary.teamwork.v4") and action.evaluations_used >= action.evaluation_limit:
        raise ValueError("EVALUATION_LIMIT: stop before round eleven dispatch")


def _optional_mapping(enabled, payload: dict) -> dict:
    if not enabled:
        return {}
    return payload


def _stream_hex(exc, name: str):
    payload = getattr(exc, name, None)
    if isinstance(payload, bytes):
        return payload.hex()
    return None


def _recheck_capture_plan(action: TeamworkAction):
    process_config = getattr(action.native_gate_check, "process_observer", None)
    kernel_config = getattr(action.native_gate_check, "kernel_check", None)
    resource_config = getattr(action.native_gate_check, "resource_check", None)
    prepared_process = None
    if process_config is not None:
        from .teamwork_process_observation import prepare_process_capture

        prepared_process = prepare_process_capture(action)
    command = prepared_process["basis"]["argv"] if prepared_process else action.check_command
    started_at_ms = time.time_ns() // 1_000_000 if prepared_process else None
    return kernel_config, resource_config, prepared_process, command, started_at_ms


def _resource_unavailable_observation(action, resource_capture, resource_metadata, prepared_process, kernel_config):
    metadata = {"command": list(action.check_command),
        "role_id": action.role_id, "execution_kind": "host", "failure_code": "CHECK_UNAVAILABLE",
        **resource_metadata,
        **_optional_mapping(prepared_process, {"process_capture": {"failure_code": "ORIGINAL_CHECK_UNAVAILABLE"}}),
        **_optional_mapping(kernel_config, {"kernel_capture": {"failure_code": "ORIGINAL_CHECK_UNAVAILABLE"}})}
    return TeamworkObservation(action_id=action.action_id, worker="host acceptance command",
        summary="CHECK_UNAVAILABLE: " + str(resource_capture["failure_code"]), blocked=True,
        artifacts=action.artifacts, metadata=metadata)


def _exception_kernel_capture(exc, command, kernel_config) -> dict:
    if kernel_config is None:
        return {}
    return {"kernel_capture": {"context": None, "failure_code": "ORIGINAL_CHECK_UNAVAILABLE",
        "original_check": {"command": list(command), "exit_code": None,
            "stdout_hex": _stream_hex(exc, "stdout"), "stderr_hex": _stream_hex(exc, "stderr")}}}


def _exception_process_capture(exc, prepared_process, started_at_ms) -> dict:
    if not prepared_process:
        return {}
    return {"process_capture": {**prepared_process["basis"],
        "stdout_hex": _stream_hex(exc, "stdout"), "stderr_hex": _stream_hex(exc, "stderr"),
        "started_at_ms": started_at_ms, "completed_at_ms": None,
        "exit_code": None, "direct_child_completed": False, "shell": False}}


def _exception_unavailable_observation(action, exc, command, kernel_config, prepared_process, started_at_ms):
    metadata = {"command": action.check_command,
        "role_id": action.role_id, "execution_kind": "host", "failure_code": "CHECK_UNAVAILABLE",
        **_exception_kernel_capture(exc, command, kernel_config),
        **_exception_process_capture(exc, prepared_process, started_at_ms)}
    return TeamworkObservation(action_id=action.action_id, worker="host acceptance command",
        summary=f"CHECK_UNAVAILABLE: {type(exc).__name__}", blocked=True,
        artifacts=action.artifacts, metadata=metadata)


def _run_configured_command(action, command, timeout, resource_config, prepared_process, kernel_config):
    if resource_config is None:
        completed = subprocess.run(command, capture_output=True, timeout=timeout, shell=False)
        return ("ok", completed, {})
    from .teamwork_resource_observation import execute_resource_check

    completed, resource_capture = execute_resource_check(action, command, timeout=timeout)
    resource_metadata = {"resource_capture": resource_capture}
    if completed is None:
        return ("early", _resource_unavailable_observation(
            action, resource_capture, resource_metadata, prepared_process, kernel_config))
    return ("ok", completed, resource_metadata)


def _run_acceptance_process(action, command, timeout, resource_config, prepared_process, kernel_config, started_at_ms):
    try:
        return _run_configured_command(action, command, timeout, resource_config, prepared_process, kernel_config)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return ("early", _exception_unavailable_observation(
            action, exc, command, kernel_config, prepared_process, started_at_ms))


def _resource_failure_update(resource_metadata, failure_code) -> dict:
    if not resource_metadata:
        return {}
    return {"resource_capture": {**resource_metadata["resource_capture"], "failure_code": failure_code}}


def _kernel_original_check(kernel_config, code, command, completed) -> dict:
    if not kernel_config:
        return {}
    return {"kernel_capture": {"context": None, "failure_code": code,
        "original_check": {"command": list(command), "exit_code": completed.returncode,
            "stdout_hex": completed.stdout.hex(), "stderr_hex": completed.stderr.hex()}}}


def _binding_changed_observation(action, exc, code, resource_metadata, kernel_config, command, completed):
    metadata = {"role_id": action.role_id, "execution_kind": "host",
        "failure_code": "ORIGINAL_CHECK_BINDING_CHANGED",
        **_resource_failure_update(resource_metadata, "ORIGINAL_CHECK_BINDING_CHANGED"),
        **_kernel_original_check(kernel_config, code, command, completed)}
    return TeamworkObservation(action_id=action.action_id, worker="host acceptance command",
        summary=f"Original checker binding changed after returned child: {type(exc).__name__}",
        blocked=True, artifacts=action.artifacts, metadata=metadata)


def _kernel_binding_stub(kernel_config) -> dict:
    if kernel_config is None:
        return {}
    return {"kernel_capture": {"context": None, "failure_code": "ORIGINAL_CHECK_BINDING_CHANGED"}}


def _process_unavailable_observation(action, exc, code, resource_metadata, kernel_config, prepared_process,
                                     completed, started_at_ms, completed_at_ms):
    metadata = {"role_id": action.role_id, "execution_kind": "host",
        "failure_code": "PROCESS_OBSERVATION_UNAVAILABLE",
        **_kernel_binding_stub(kernel_config),
        **_resource_failure_update(resource_metadata, code),
        "post_execution_failure": code, "process_capture": {**prepared_process["basis"],
            "stdout_hex": completed.stdout.hex(), "stderr_hex": completed.stderr.hex(),
            "exit_code": completed.returncode, "direct_child_completed": True, "shell": False,
            "started_at_ms": started_at_ms, "completed_at_ms": completed_at_ms}}
    return TeamworkObservation(action_id=action.action_id, worker="host acceptance command",
        summary=f"PROCESS_OBSERVATION_UNAVAILABLE after returned child: {type(exc).__name__}",
        blocked=True, artifacts=action.artifacts, metadata=metadata)


def _post_child_failure(action, exc, prepared_process, kernel_config, resource_metadata, command, completed,
                        started_at_ms, completed_at_ms):
    code = str(exc).split(":", 1)[0]
    if prepared_process is None:
        return _binding_changed_observation(
            action, exc, code, resource_metadata, kernel_config, command, completed)
    return _process_unavailable_observation(
        action, exc, code, resource_metadata, kernel_config, prepared_process, completed,
        started_at_ms, completed_at_ms)


def _finish_recheck_captures(action, prepared_process, kernel_config, resource_config, completed,
                             resource_metadata, command, started_at_ms, completed_at_ms):
    try:
        _current_source(action)
        _current_checker(action)
        _current_artifacts(action.artifacts)
        if not prepared_process:
            return ("ok", None)
        from .teamwork_process_observation import finish_process_capture

        return ("ok", finish_process_capture(
            action, prepared_process, completed, started_at_ms, completed_at_ms))
    except (ValueError, OSError, TypeError, RuntimeError, ImportError) as exc:
        if prepared_process is None and kernel_config is None and resource_config is None:
            raise
        return ("early", _post_child_failure(
            action, exc, prepared_process, kernel_config, resource_metadata, command, completed,
            started_at_ms, completed_at_ms))


def _recheck_findings(completed):
    if completed.returncode == 0:
        return ()
    return (f"Original task check failed: exit {completed.returncode}",)


def _process_observations_metadata(process_observations) -> dict:
    if not process_observations:
        return {}
    return {"process_observations": process_observations}


def _kernel_metadata(action, kernel_config, timeout) -> dict:
    if kernel_config is None:
        return {}
    from .teamwork_kernel_observation import capture_kernel_observation

    return capture_kernel_observation(action, timeout=timeout)


def _stamp_ms(enabled):
    if not enabled:
        return None
    return time.time_ns() // 1_000_000


def _accepted_recheck_observation(action, completed, kernel_metadata, resource_metadata, process_observations):
    output = completed.stdout + b"\n--- stderr ---\n" + completed.stderr
    return TeamworkObservation(action_id=action.action_id, worker="host acceptance command",
        summary=f"Original-task check exited {completed.returncode}", artifacts=action.artifacts,
        findings=_recheck_findings(completed),
        check=TaskCheck(initial_task_id=action.initial_task_id,
            source_id=action.check_source_id or action.intelligence.source_id,
            checker_id=action.checker_id, command=action.check_command,
            exit_status=completed.returncode, output_sha256=hashlib.sha256(output).hexdigest(),
            artifacts=action.artifacts),
        metadata={"role_id": action.role_id, "execution_kind": "host",
                  **kernel_metadata, **resource_metadata,
                  **_process_observations_metadata(process_observations),
                  "checker_capture": {"schema_version": "adversary.unsigned-checker-capture.v1",
                      "stdout_hex": completed.stdout.hex(), "stderr_hex": completed.stderr.hex(),
                      "exit_code": completed.returncode, "command": list(action.check_command),
                      "authority_effect": "None", "authenticated": False},
                  "stdout": completed.stdout.decode("utf-8", errors="replace"),
                  "stderr": completed.stderr.decode("utf-8", errors="replace")})


def _execute_recheck(action: TeamworkAction, *, timeout: float = 60) -> TeamworkObservation:
    _require_recheck_dispatch(action)
    from .teamwork_native_gates import validate_native_gate_context

    validate_native_gate_context(action)
    _current_source(action)
    _current_checker(action)
    _current_artifacts(action.artifacts)
    kernel_config, resource_config, prepared_process, command, started_at_ms = _recheck_capture_plan(action)
    outcome = _run_acceptance_process(
        action, command, timeout, resource_config, prepared_process, kernel_config, started_at_ms)
    if outcome[0] == "early":
        return outcome[1]
    completed, resource_metadata = outcome[1], outcome[2]
    completed_at_ms = _stamp_ms(prepared_process)
    finished = _finish_recheck_captures(
        action, prepared_process, kernel_config, resource_config, completed, resource_metadata,
        command, started_at_ms, completed_at_ms)
    if finished[0] == "early":
        return finished[1]
    return _accepted_recheck_observation(
        action, completed, _kernel_metadata(action, kernel_config, timeout), resource_metadata, finished[1])


def _require_digest_pending(action: TeamworkAction) -> None:
    if action.kind != "digest" or action.intelligence is None:
        raise ValueError("DIGEST_NOT_PENDING")


def _load_digestion_report(path: Path) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict) or not isinstance(report.get("context"), dict):
        raise ValueError("DIGESTION_CONTEXT_MISMATCH: report and context must be objects")
    return report


def _require_digestion_context(context: dict, action: TeamworkAction) -> None:
    if (context.get("initial_task_id") != action.initial_task_id
            or context.get("parent_source_id") != action.intelligence.source_id
            or context.get("checker_id") != action.checker_id
            or context.get("checked_artifacts") != action.artifacts):
        raise ValueError("DIGESTION_CONTEXT_MISMATCH: bind initial task, parent, checker and checked outputs")


def _require_digestion_outputs(outputs, action: TeamworkAction, source) -> None:
    if not isinstance(outputs, dict) or not action.artifacts.keys() <= outputs.keys():
        raise ValueError("DIGESTION_OUTPUTS_MISSING: retain every original and descendant output")
    _current_artifacts(outputs)
    if not source.findings and outputs != action.artifacts:
        raise ValueError("UNCHECKED_DESCENDANT: recheck new output before closure")


def _digestion_metadata(action: TeamworkAction, source, report) -> dict:
    metadata = {"source_profile": "adversary.host-read.v1",
        "role_id": action.role_id, "execution_kind": "host"}
    if action.feedback_policy == "semantic_digestion_v2":
        metadata["digestion_review"] = _digestion_review_context(report)
    if source.coverage_gaps:
        metadata["failure_code"] = "SOURCE_COVERAGE_OPEN"
    return metadata


def digest_output(action: TeamworkAction, path: Path) -> TeamworkObservation:
    """Read an actual DigestionReceipt with the small owning task-context extension.

    A report may expose new output on failure. A clean report must cover exactly
    the already checked outputs. Old archive receipts remain valid intake sources;
    they cannot masquerade as this task's final acceptance report.
    """
    _require_digest_pending(action)
    _current_source(action)
    _current_artifacts(action.artifacts)
    before = _source_digest(path)
    report = _load_digestion_report(path)
    context = report.get("context", {})
    _require_digestion_context(context, action)
    source = read_intelligence(path, initial_task_id=action.initial_task_id,
                               parent_source_id=action.intelligence.source_id)
    if source.source_id != before:
        raise ValueError("SOURCE_CHANGED: digestion report changed during intake")
    outputs = context.get("output_artifacts")
    _require_digestion_outputs(outputs, action, source)
    _current_source(action)
    _current_artifacts(action.artifacts)
    if _source_digest(path) != source.source_id:
        raise ValueError("SOURCE_CHANGED: digestion report changed before acceptance")
    return TeamworkObservation(action_id=action.action_id, worker="host digestion readback",
        summary=f"Digested current report: {len(source.findings)} findings, {len(source.coverage_gaps)} gaps",
        findings=source.findings, artifacts=outputs, intelligence=source,
        blocked=bool(source.coverage_gaps), metadata=_digestion_metadata(action, source, report))


def _digestion_review_context(report):
    """Read actual decision fields; ancestor/native bytes retain their own paths."""
    context = report["context"]
    return {**{key: report.get(key) for key in ("receipt_id", "authority_effect", "errors", "warnings", "blocked")},
        "context": {key: context.get(key) for key in ("initial_task_id", "parent_source_id", "checker_id",
            "checked_artifacts", "output_artifacts", "decision_scope", "observed_run_sha256",
            "admitted_check", "current_findings", "coverage_gaps", "stopped_status", "stopped_reason")}}


def _learning_digest_bound(action, source) -> bool:
    return any(item.model_dump(mode="json") == source for item in action.source_reads)


def _learning_report_matches(path: Path, source, digest, before, report) -> bool:
    if before != source["source_id"] or _source_digest(path) != before:
        return False
    return digest.get("metadata", {}).get("digestion_review") == _digestion_review_context(report)


def _recorded_host_observation(action):
    expected = action.ddc_program.host_observation
    if not expected:
        return None
    return expected.model_dump(mode="json")


def validate_learning_context(action):
    """Re-read the actual reviewed digestion and captured pre-learning facts."""
    if action.feedback_policy != "semantic_digestion_v2" or action.learning_context is None:
        return
    validate_ddc_context(action, require_current_premises=action.kind == "learn")
    context = action.learning_context
    digest = context.get("digestion")
    if not isinstance(digest, dict) or not isinstance(digest.get("intelligence"), dict):
        raise ValueError("LEARNING_DIGEST_REQUIRED")
    source = digest["intelligence"]
    if not _learning_digest_bound(action, source):
        raise ValueError("LEARNING_DIGEST_BINDING_MISMATCH")
    path = Path(source["source_locator"])
    before = _source_digest(path)
    report = json.loads(path.read_bytes())
    if not _learning_report_matches(path, source, digest, before, report):
        raise ValueError("LEARNING_DIGEST_BINDING_MISMATCH")
    if context.get("host_observation") != _recorded_host_observation(action):
        raise ValueError("DDC_HOST_OBSERVATION_MISMATCH")


def _require_current_feedback(run: TeamworkRun) -> None:
    if run.schema_version not in ("core.adversary.teamwork.v3", "core.adversary.teamwork.v4") or run.feedback_policy not in ("semantic_digestion_v1", "semantic_digestion_v2"):
        raise ValueError("LEGACY_FEEDBACK_READ_ONLY: retained states cannot dispatch current host work")


def _require_digest_run(run: TeamworkRun, action: TeamworkAction) -> None:
    _require_current_feedback(run)
    if next_action(run) != action or action.kind != "digest" or action.intelligence is None:
        raise ValueError("DIGEST_NOT_PENDING")
    _current_source(action)
    _current_checker(action)
    _current_artifacts(action.artifacts)


def _require_run_sources(run: TeamworkRun):
    sources = intelligence_sources(run)
    if not sources:
        raise ValueError("RUN_INTAKE_REQUIRED")
    return sources


def _inherited_coverage_gaps(sources) -> list:
    return [gap for source in sources for gap in source.coverage_gaps]


def _digest_gaps(extraction, sources) -> list:
    return sorted({*extraction.coverage_gaps, *extraction.parse_residuals,
        *_inherited_coverage_gaps(sources)})


def _latest_role_observation(run: TeamworkRun, role_id: str):
    return next((item for item in reversed(run.observations)
        if item.metadata.get("role_id") == role_id), None)


def _fallback_check(run: TeamworkRun):
    return next((item.check for item in reversed(run.observations) if item.check is not None), None)


def _resolve_digest_check(run: TeamworkRun, stopped):
    latest = _latest_role_observation(run, "host_acceptance")
    check = latest.check if latest is not None else None
    if stopped and check is None:
        check = _fallback_check(run)
    return latest, check


def _digest_source_mismatch(action: TeamworkAction, check) -> bool:
    if check.initial_task_id != action.initial_task_id:
        return True
    expected_source = action.check_source_id or action.intelligence.source_id
    return check.source_id != expected_source


def _digest_checker_mismatch(action: TeamworkAction, check) -> bool:
    if check.checker_id != action.checker_id or check.command != action.check_command:
        return True
    return check.artifacts != action.artifacts or not check.artifacts


def _digest_check_unusable(action: TeamworkAction, check, latest) -> bool:
    if check is None or check.exit_status != 0 or latest.blocked or latest.findings:
        return True
    if _digest_source_mismatch(action, check):
        return True
    return _digest_checker_mismatch(action, check)


def _require_digest_episode(run: TeamworkRun, latest, sqlite3, closing) -> None:
    binding = run.episode_binding
    if not binding or bind_episode_admission(run, Path(binding["path"]), existing=True) != binding:
        raise ValueError("EPISODE_ADMISSION_REQUIRED")
    with closing(sqlite3.connect(binding["path"])) as ledger:
        row = ledger.execute("SELECT result FROM episodes WHERE action_id = ?", (latest.action_id,)).fetchone()
    if row is None or row[0] is None or TeamworkObservation.model_validate_json(row[0]) != latest:
        raise ValueError("DIGESTION_EPISODE_MISMATCH: a stored PASS label cannot replace admitted execution")


def _require_digest_acceptance(run, action, stopped, gaps, check, latest, sqlite3, closing) -> None:
    if stopped or gaps:
        return
    if _digest_check_unusable(action, check, latest):
        raise ValueError("DIGESTION_ACCEPTANCE_REQUIRED: retain the actual current original-task check")
    _require_digest_episode(run, latest, sqlite3, closing)


def _checked_clarification(current, action):
    clarification_context = current.get("clarification_context")
    checked_question = (clarification_context is not None
        and clarification_context == action.clarification_context)
    return clarification_context, checked_question


def _frontier_still_open(current, frontier, checked_question) -> bool:
    if frontier and not checked_question:
        return True
    return bool(current["coverage_gaps"] or current["reason"])


def _require_digest_frontier(current, stopped, gaps, frontier, checked_question) -> None:
    if stopped or gaps:
        return
    if _frontier_still_open(current, frontier, checked_question):
        raise ValueError("DIGESTION_FRONTIER_OPEN: observed current work remains unresolved")


def _admitted_check_dump(check, stopped, gaps):
    if check is None or stopped or gaps:
        return None
    return check.model_dump(mode="json")


def _observed_check_dump(check):
    if check is None:
        return None
    return check.model_dump(mode="json")


def _digest_source_reads(sources) -> list:
    return [source.model_dump(mode="json") for source in sources]


def _digest_native_diagnostics(run: TeamworkRun) -> list:
    return [{"action_id": item.action_id,
        "policy": item.metadata.get("native_gate_policy", getattr(run.native_gate_check, "policy", None)),
        "scope": "native diagnostic predicates, separate from original-task acceptance",
        "summary": item.metadata["native_gate_summary"],
        "receipt": item.metadata.get("native_gate_receipt")}
        for item in run.observations if "native_gate_summary" in item.metadata]


def _digest_context(run, action, sources, frontier, gaps, stopped, check, extraction,
                    checked_question, clarification_context) -> dict:
    context = {"initial_task_id": action.initial_task_id,
        "parent_source_id": action.intelligence.source_id, "checker_id": action.checker_id,
        "checked_artifacts": action.artifacts, "output_artifacts": action.artifacts,
        "decision_scope": "declared original-task checker and replayed observed frontier only",
        "observed_run_sha256": hashlib.sha256(run.model_dump_json().encode("utf-8")).hexdigest(),
        "admitted_check": _admitted_check_dump(check, stopped, gaps),
        "observed_check": _observed_check_dump(check),
        "source_reads": _digest_source_reads(sources),
        "current_findings": list(frontier), "coverage_gaps": gaps,
        "stopped_status": stopped, "stopped_reason": action.stopped_reason,
        "observed_findings": extraction.findings,
        "native_diagnostics": _digest_native_diagnostics(run)}
    if checked_question:
        context["clarification_context"] = clarification_context
        context["decision_scope"] = "checked request for external inputs; NOT_SOLVED; advisory findings retained"
    return context


def _digest_blocked(stopped, action, frontier) -> list:
    if not stopped:
        return []
    return [{"state": stopped, "residuals": [action.stopped_reason, *frontier]}]


def _digest_report(context, frontier, extraction, stopped, action, datetime, timezone) -> dict:
    receipt_id = hashlib.sha256(json.dumps(context, sort_keys=True, ensure_ascii=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()
    return {"receipt_id": receipt_id, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "authority_effect": "None", "total_runs_examined": 1, "total_runs_archived": 0,
        "records": [{"defects_extracted": list(frontier),
            "historical_reported_findings": extraction.findings}],
        "blocked": _digest_blocked(stopped, action, frontier),
        "errors": list(frontier), "warnings": [], "context": context}


def _payload_without_timestamp(record: dict) -> dict:
    return {key: value for key, value in record.items() if key != "timestamp_utc"}


def _refuse_changed_digest(path: Path, report: dict) -> None:
    saved = json.loads(path.read_bytes())
    if _payload_without_timestamp(saved) != _payload_without_timestamp(report):
        raise ValueError("DIGESTION_OUTPUT_EXISTS: retain the previous generation")


def _create_digest_file(path: Path, report: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=True, indent=2)
        handle.write("\n")


def _write_digest_report(run: TeamworkRun, action: TeamworkAction, report: dict, output_dir) -> Path:
    path = _ddc_output_dir(output_dir) / "digests" / f"{run.run_id[:70]}-{action.action_id[:16]}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        _refuse_changed_digest(path, report)
    else:
        _create_digest_file(path, report)
    return path


def digest_current_run(run: TeamworkRun, action: TeamworkAction, *, output_dir=None) -> TeamworkObservation:
    """Digest the admitted current task/frontier; retain history as provenance.

    The operator's original checker decides its declared task and artifact scope.
    Historical reported failures remain in their sources; this neither proves
    absence of unknown defects nor promotes native storage to task acceptance.
    """
    import sqlite3
    from contextlib import closing
    from datetime import datetime, timezone

    _require_digest_run(run, action)
    sources = _require_run_sources(run)
    # Read the actual post-learning run with the same known-profile extractor,
    # including malformed new learning fields, rather than copying prior coverage.
    extraction = read_teamwork_findings(json.loads(run.model_dump_json()))
    gaps = _digest_gaps(extraction, sources)
    current = run.continuation_status
    frontier = current["open_findings"]
    stopped = action.stopped_status
    latest, check = _resolve_digest_check(run, stopped)
    _require_digest_acceptance(run, action, stopped, gaps, check, latest, sqlite3, closing)
    # Replay all retained role/check observations rather than filtering PASS labels.
    clarification_context, checked_question = _checked_clarification(current, action)
    _require_digest_frontier(current, stopped, gaps, frontier, checked_question)
    context = _digest_context(run, action, sources, frontier, gaps, stopped, check, extraction,
        checked_question, clarification_context)
    report = _digest_report(context, frontier, extraction, stopped, action, datetime, timezone)
    path = _write_digest_report(run, action, report, output_dir)
    _current_source(action)
    _current_checker(action)
    _current_artifacts(action.artifacts)
    return digest_output(action, path)


def ddc_premises(action: TeamworkAction) -> dict:
    """The exact current-task scope a retained procedure may consume."""
    from ..use_cases.teamwork import ddc_task_premises

    return ddc_task_premises(action)


def _require_loaded_source(program, path: Path, loaded_source_id: str) -> None:
    if loaded_source_id != program.source_id or _source_digest(path) != program.source_id:
        raise ValueError("DDC_HOST_OBSERVATION_SOURCE_CHANGED")


def _require_stable_source(program, path: Path) -> None:
    if _source_digest(path) != program.source_id:
        raise ValueError("DDC_HOST_OBSERVATION_SOURCE_CHANGED")


def _observed_procedure_snapshots(loaded) -> list:
    return [step["observed_procedure"] for step in loaded["steps"] if "observed_procedure" in step]


def _observation_scope_mismatch(context, observations, snapshots, program_digest) -> bool:
    if context.get("schema_version") not in ("core.adversary.teamwork.v3", "core.adversary.teamwork.v4"):
        return True
    if type(observations) is not list or len(snapshots) != 1:
        return True
    snapshot = snapshots[0]
    return (snapshot["observation_count"] != len(observations)
        or snapshot["observations_sha256"] != program_digest(observations))


def _read_attempt_cost(record, decimal):
    cost = record.get("cost_usd")
    if cost is None:
        return None
    if type(cost) not in (int, float, str):
        raise ValueError("DDC_HOST_OBSERVATION_COST_INVALID")
    cost = decimal(str(cost))
    if not cost.is_finite() or cost < 0:
        raise ValueError("DDC_HOST_OBSERVATION_COST_INVALID")
    return cost


def _remember_attempt(attempts, record, decimal) -> None:
    attempt_id = record.get("attempt_id")
    # Before-dispatch refusals have no admitted provider attempt.
    if not attempt_id:
        return
    if type(attempt_id) is not str:
        raise ValueError("DDC_HOST_OBSERVATION_ATTEMPTS_INVALID")
    fact = (_read_attempt_cost(record, decimal), record.get("attempt_state"), record.get("raw_reply_sha256"))
    if attempt_id in attempts and attempts[attempt_id] != fact:
        raise ValueError("DDC_HOST_OBSERVATION_ATTEMPT_CONFLICT")
    attempts[attempt_id] = fact


def _attempt_records(observation) -> list:
    metadata = observation["metadata"]
    records = metadata.get("pfp_attempts", [])
    if type(records) is not list:
        raise ValueError("DDC_HOST_OBSERVATION_ATTEMPTS_INVALID")
    return [*records, metadata]


def _collect_provider_attempts(observations, decimal) -> dict:
    attempts = {}
    for observation in observations:
        for record in _attempt_records(observation):
            _remember_attempt(attempts, record, decimal)
    return attempts


def _known_costs(attempts) -> list:
    return [fact[0] for fact in attempts.values() if fact[0] is not None]


def _billing_status(unknown: int, known: list) -> str:
    if unknown:
        return "UNKNOWN_COST"
    if known:
        return "KNOWN_COST"
    return "UNOBSERVED"


def _blank_field(record, name: str) -> str:
    return record.get(name) or ""


def _host_observation_facts(program_digest, observation_type, decimal, context, observations, snapshots, attempts):
    known = _known_costs(attempts)
    unknown = len(attempts) - len(known)
    snapshot = snapshots[0]
    return observation_type(observations_sha256=program_digest(observations),
        observation_count=len(observations), executor=context["executor"],
        provider_attempt_count=len(attempts), known_cost_attempt_count=len(known),
        unknown_cost_attempt_count=unknown, known_cost_usd=format(sum(known, decimal(0)), "f"),
        billing_status=_billing_status(unknown, known),
        stopped_status=_blank_field(snapshot, "stopped_status"),
        stopped_reason=_blank_field(snapshot, "stopped_reason"))


def readback_host_observation(program, loaded):
    """Facts from the sealed observation prefix, not a bill or future learning."""
    from decimal import Decimal

    from ..use_cases.prompt_family_replay import _program_digest
    from ..use_cases.teamwork import TeamworkHostObservation

    path = Path(program.run_path)
    _require_loaded_source(program, path, loaded["source_id"])
    context = json.loads((path / "summary.json").read_bytes())["retained_context"]
    observations = context["observations"]
    snapshots = _observed_procedure_snapshots(loaded)
    if _observation_scope_mismatch(context, observations, snapshots, _program_digest):
        raise ValueError("DDC_HOST_OBSERVATION_SCOPE_MISMATCH")
    attempts = {}
    if context["executor"] != "ide":
        attempts = _collect_provider_attempts(observations, Decimal)
    facts = _host_observation_facts(
        _program_digest, TeamworkHostObservation, Decimal, context, observations, snapshots, attempts)
    _require_stable_source(program, path)
    return facts


def _ddc_binding_mismatch(action: TeamworkAction, saved, program_digest) -> bool:
    binding = saved.binding
    if binding.template_version != action.workflow_version:
        return True
    if binding.family_id != "adversary-teamwork-" + action.workflow_version.rsplit(".", 1)[1]:
        return True
    if binding.prompt_sha256 != hashlib.sha256(action.objective.encode()).hexdigest():
        return True
    return binding.premises_sha256 != program_digest(saved.premises)


def _procedure_predates_readback(source, saved, action: TeamworkAction) -> bool:
    same_path = Path(source["source_locator"]).absolute() == Path(saved.run_path).absolute()
    if not same_path or source["source_id"] != saved.source_id:
        return False
    return (source["initial_task_id"] == action.initial_task_id
        and source["parent_source_id"] is None)


def _premises_without_own_readback(current, saved, action: TeamworkAction) -> dict:
    # The procedure predates its own observed readback source. Nothing
    # else in the original task/checker/output premises is omitted.
    retained = [source for source in current["source_reads"]
        if not _procedure_predates_readback(source, saved, action)]
    return {**current, "source_reads": retained}


def _current_ddc_premises(action: TeamworkAction, saved, require_current_premises) -> None:
    if not require_current_premises:
        return
    current = ddc_premises(action)
    if getattr(action, "feedback_policy", None) in ("semantic_digestion_v1", "semantic_digestion_v2"):
        current = _premises_without_own_readback(current, saved, action)
    if saved.premises != current:
        raise ValueError("DDC_REUSE_PREMISES_MISMATCH: task, checker or candidate changed")


def _require_loaded_program(saved, loaded) -> None:
    if loaded["source_id"] != saved.source_id or loaded["steps"] != list(saved.steps):
        raise ValueError("DDC_PROGRAM_BINDING_MISMATCH: checked context changed")
    if saved.host_observation is not None and saved.host_observation != readback_host_observation(saved, loaded):
        raise ValueError("DDC_HOST_OBSERVATION_MISMATCH: captured facts differ from native readback")


def _step_letter_refused(step) -> bool:
    return step["letter"] not in {"C", "R", "I", "T"}


def _require_observed_letters(loaded) -> None:
    if any(_step_letter_refused(step) for step in loaded["steps"]):
        raise ValueError("DDC_PROGRAM_EFFECT_REFUSED: this host retains observed C/R/I/T only")


def _unchanged_artifacts(action: TeamworkAction, changed_paths) -> dict:
    return {path: digest for path, digest in action.artifacts.items() if path not in changed_paths}


def validate_ddc_context(action: TeamworkAction, *, require_current_premises=True,
                         changed_paths=()) -> dict:
    """Read the native procedure again before PFP preparation or final storage."""
    from ..use_cases.prompt_family_replay import _program_digest, load_ddc_program
    from .teamwork_native_gates import validate_native_gate_context

    validate_native_gate_context(action, changed_paths=changed_paths)
    saved = action.ddc_program
    if saved is None:
        raise ValueError("DDC_PROGRAM_REQUIRED: Scar Chronicler requires native sealed procedure readback")
    if _ddc_binding_mismatch(action, saved, _program_digest):
        raise ValueError("DDC_REUSE_PREMISES_MISMATCH")
    _current_ddc_premises(action, saved, require_current_premises)
    loaded = load_ddc_program(saved.run_path, expected=saved.binding,
                              initial_task_id=action.initial_task_id, native_support=DefaultNativeOperationPort())
    _require_loaded_program(saved, loaded)
    _require_observed_letters(loaded)
    _current_source(action)
    _current_checker(action)
    _current_artifacts(_unchanged_artifacts(action, changed_paths))
    return loaded


def _ddc_output_dir(output_dir):
    if output_dir is not None:
        return Path(output_dir)
    from operating_system.adapters.intelligence_custody.ic_routing import (
        intelligence_path,
    )
    from operating_system.adapters.intelligence_custody.intelligence_root import (
        resolve_intelligence_repo_root,
    )

    return intelligence_path(resolve_intelligence_repo_root(), "_intelligence/_adversary")


def _acceptance_identity_rejected(action: TeamworkAction, check) -> bool:
    if check.initial_task_id != action.initial_task_id or check.checker_id != action.checker_id:
        return True
    return check.command != action.check_command


def _acceptance_artifacts_rejected(action: TeamworkAction, check) -> bool:
    if check.artifacts != action.artifacts or not check.artifacts:
        return True
    return any(source.coverage_gaps for source in action.source_reads)


def _acceptance_check_rejected(action: TeamworkAction, observed, check) -> bool:
    if check is None or observed.blocked or check.exit_status != 0:
        return True
    if _acceptance_identity_rejected(action, check):
        return True
    return _acceptance_artifacts_rejected(action, check)


def _acceptance_source_matches(action: TeamworkAction, check) -> bool:
    if action.check_source_id:
        return check.source_id == action.check_source_id
    return any(source.source_id == check.source_id for source in action.source_reads)


def _admitted_episode_observation(run: TeamworkRun, observed, sqlite3, closing):
    binding = run.episode_binding
    if not binding or bind_episode_admission(run, Path(binding["path"]), existing=True) != binding:
        return None
    with closing(sqlite3.connect(binding["path"])) as ledger:
        row = ledger.execute("SELECT result FROM episodes WHERE action_id = ?", (observed.action_id,)).fetchone()
    if row is None or row[0] is None or TeamworkObservation.model_validate_json(row[0]) != observed:
        return None
    return observed


def _current_admitted_acceptance(run: TeamworkRun, action: TeamworkAction) -> TaskCheck | None:
    """Match current acceptance to actual continuing admission, never a PASS label."""
    import sqlite3
    from contextlib import closing

    observed = _latest_role_observation(run, "host_acceptance")
    check = observed.check if observed is not None else None
    if _acceptance_check_rejected(action, observed, check):
        return None
    if not _acceptance_source_matches(action, check):
        return None
    if _admitted_episode_observation(run, observed, sqlite3, closing) is None:
        return None
    return check


def _workflow_action_pending(run: TeamworkRun, action: TeamworkAction) -> bool:
    return (action.workflow_version in ("core.adversary.teamwork.v3", "core.adversary.teamwork.v4")
        and next_action(run) == action)


def _observation_dumps(run: TeamworkRun) -> list:
    return [item.model_dump(mode="json") for item in run.observations]


def _learning_metadata(item) -> dict:
    keys = ("lessons", "changed_paths", "verification", "no_change_reason", "proposed_only",
        "consumed_ddc_root", "consumed_procedure_sha256")
    return {key: item.metadata[key] for key in keys if key in item.metadata}


def _observed_operation(item) -> dict:
    recorded_check = None
    if item.check:
        recorded_check = item.check.model_dump(mode="json")
    return {"action_id": item.action_id,
        "role_id": item.metadata.get("role_id"), "blocked": item.blocked,
        "findings": list(item.findings), "check": recorded_check,
        "learning": _learning_metadata(item)}


def _observed_operations(run: TeamworkRun) -> list:
    return [_observed_operation(item) for item in run.observations]


def _procedure_snapshot(action: TeamworkAction, observed, run: TeamworkRun, program_digest) -> dict:
    return {"observations_sha256": program_digest(observed),
        "observation_count": len(observed), "artifacts": action.artifacts,
        "stopped_status": action.stopped_status, "stopped_reason": action.stopped_reason,
        "open_findings": list(action.findings), "evaluations_used": action.evaluations_used,
        "evaluation_limit": action.evaluation_limit,
        "observed_operations": _observed_operations(run)}


def _procedure_states(premises, observed, snapshot, action: TeamworkAction, program_digest) -> list:
    return ["intake:" + program_digest(premises), "observations:" + program_digest(observed),
        "residual:" + program_digest(snapshot), "retained:" + program_digest(action.artifacts),
        "terminal:" + program_digest({"action_id": action.action_id, "status": "OPEN_RESIDUAL"})]


def _procedure_witness(letter: str, explanation: str, snapshot, retained_context, program_digest):
    if letter != "R":
        return explanation, None
    evidence = {"teamwork_procedure": snapshot,
        "retained_context_sha256": program_digest(retained_context)}
    return explanation + " Retained context SHA256: " + evidence["retained_context_sha256"], evidence


def _record_procedure_steps(logger, action, states, snapshot, retained_context, program_digest) -> None:
    explanations = (
        "Host reread the bound task, checker sources and candidate bytes.",
        "Host projected actual retained observations and unresolved findings.",
        "Host integrated the current artifact and check observations; correctness remains unverified.",
        "Host retained scoped progress through native sealing/readback; no exact repair is asserted.")
    for index, (letter, explanation) in enumerate(zip(("C", "R", "I", "T"), explanations)):
        witness, evidence = _procedure_witness(letter, explanation, snapshot, retained_context, program_digest)
        logger.record_step(letter, "host:" + action.kind + ":" + letter,
            states[index], states[index + 1], witness, evidence=evidence)


def _open_obligations(run: TeamworkRun, action: TeamworkAction):
    if _current_admitted_acceptance(run, action) is None:
        return None
    return list(action.findings)


def _persist_sealed_procedure(run, action, output_dir, premises, observed, snapshot, retained_context,
                              program_digest, temporary_directory, trace_logger, persist_ddc_program):
    task_key = f"{run.run_id[:70]}-{action.kind}-{action.action_id[:16]}"
    with temporary_directory(prefix="adversary-ddc-") as temporary:
        logger = trace_logger(task_key, trace_dir=Path(temporary), auto_lifecycle=False)
        states = _procedure_states(premises, observed, snapshot, action, program_digest)
        _record_procedure_steps(logger, action, states, snapshot, retained_context, program_digest)
        return persist_ddc_program(output_dir=_ddc_output_dir(output_dir),
            task_key=task_key, trace_path=logger.jsonl_path, prompt_text=action.objective,
            family_id="adversary-teamwork-" + action.workflow_version.rsplit(".", 1)[1],
            template_version=action.workflow_version,
            premises=premises, recover_existing=True, retained_context=retained_context,
            current_open_obligations=_open_obligations(run, action),
            native_support=DefaultNativeOperationPort())


def _sealed_program(binding, path, loaded, premises, program_digest, teamwork_ddc_program):
    program = teamwork_ddc_program(binding=binding, run_path=str(path.absolute()),
        source_id=loaded["source_id"], steps=tuple(loaded["steps"]), premises=premises,
        learning_reply_binding={"consumed_ddc_root": binding.semantic_ddc_root,
            "consumed_procedure_sha256": program_digest(binding.model_dump(mode="json"))})
    return program.model_copy(update={"host_observation": readback_host_observation(program, loaded)})


def _seal_teamwork_procedure(run: TeamworkRun, action: TeamworkAction, *, output_dir):
    import tempfile

    from operads.skill_operad.ddc_trace_logger import TraceLogger

    from ..use_cases.prompt_family_replay import (
        _program_digest,
        load_ddc_program,
        persist_ddc_program,
    )
    from ..use_cases.teamwork import TeamworkDdcProgram

    _require_current_feedback(run)
    if not _workflow_action_pending(run, action):
        raise ValueError("DDC_ACTION_MISMATCH: storage must consume the actual pending action")
    from .teamwork_native_gates import validate_native_gate_context

    validate_native_gate_context(action)
    _current_source(action)
    _current_checker(action)
    _current_artifacts(action.artifacts)
    premises = ddc_premises(action)
    observed = _observation_dumps(run)
    retained_context = run.model_dump(mode="json")
    # These mutable host custody bindings are retained in their own ledgers.
    # Recovery parents may change without changing the semantic pending action.
    retained_context.pop("provider_binding", None)
    retained_context.pop("episode_binding", None)
    snapshot = _procedure_snapshot(action, observed, run, _program_digest)
    path, binding = _persist_sealed_procedure(
        run, action, output_dir, premises, observed, snapshot, retained_context, _program_digest,
        tempfile.TemporaryDirectory, TraceLogger, persist_ddc_program)
    _current_source(action)
    _current_checker(action)
    _current_artifacts(action.artifacts)
    loaded = load_ddc_program(path, expected=binding, initial_task_id=action.initial_task_id,
        native_support=DefaultNativeOperationPort())
    program = _sealed_program(binding, path, loaded, premises, _program_digest, TeamworkDdcProgram)
    return TeamworkObservation(action_id=action.action_id, worker="native DDC host",
        summary="Sealed and read back the observed current-task C/R/I/T procedure.",
        artifacts=dict(action.artifacts), ddc_program=program,
        metadata={"role_id": action.role_id, "execution_kind": "host",
            "native_sealed_readback": True, "billing_status": "UNOBSERVED", "cost_usd": None,
            "final_current_source_checked": action.kind == "ddc_complete"})


def store_ddc_program(run: TeamworkRun, action: TeamworkAction, *, output_dir=None):
    if action.kind != "ddc_store":
        raise ValueError("DDC_STORE_NOT_PENDING")
    result = _seal_teamwork_procedure(run, action, output_dir=output_dir)
    if getattr(run, "feedback_policy", None) in ("semantic_digestion_v1", "semantic_digestion_v2") and not intelligence_sources(run):
        source = read_intelligence(Path(result.ddc_program.run_path), initial_task_id=run.run_id)
        if source.source_id != result.ddc_program.source_id:
            raise ValueError("DDC_PROGRAM_BINDING_MISMATCH: native intake readback differs")
        result = result.model_copy(update={"intelligence": source,
            "blocked": bool(source.coverage_gaps), "metadata": {**result.metadata,
                **({"failure_code": "SOURCE_COVERAGE_OPEN"} if source.coverage_gaps else {})}})
    return result


def _failed_attempt_stopped(learned, action: TeamworkAction) -> bool:
    return learned is not None and learned.blocked and action.stopped_status


def _consumption_missing(learned, action: TeamworkAction, program_digest) -> bool:
    if learned is None or learned.blocked:
        return True
    binding = action.ddc_program.binding
    if learned.metadata.get("consumed_ddc_root") != binding.semantic_ddc_root:
        return True
    return learned.metadata.get("consumed_procedure_sha256") != program_digest(binding.model_dump(mode="json"))


def complete_ddc_program(run: TeamworkRun, action: TeamworkAction, *, output_dir=None):
    from ..use_cases.prompt_family_replay import _program_digest

    if action.kind != "ddc_complete":
        raise ValueError("DDC_COMPLETE_NOT_PENDING")
    validate_ddc_context(action, require_current_premises=False)
    learned = _latest_role_observation(run, "scar_chronicler")
    if _failed_attempt_stopped(learned, action):
        # Preserve the failed attempt and terminal obstruction. Native sealing
        # records that failure; it does not assert successful DDC consumption.
        return _seal_teamwork_procedure(run, action, output_dir=output_dir)
    if _consumption_missing(learned, action, _program_digest):
        raise ValueError("DDC_CONSUMPTION_REQUIRED: retain Scar Chronicler's checked procedure binding")
    return _seal_teamwork_procedure(run, action, output_dir=output_dir)


def bind_episode_admission(run: TeamworkRun, path: Path, *, existing=False) -> dict:
    """Open the continuing host episode ledger; missing resume state is refused."""
    import sqlite3
    from contextlib import closing

    from ..use_cases.prompt_family_replay import _program_digest

    scope = {"run_id": run.run_id, "objective_sha256": hashlib.sha256(run.objective.encode()).hexdigest(),
        "acceptance": run.acceptance_check.model_dump(mode="json") if run.acceptance_check else None,
        "checker_id": run.checker_id, "check_command": list(run.check_command),
        "max_evaluations": run.max_evaluations,
        "intelligence": run.intelligence.model_dump(mode="json") if run.intelligence else None}
    if run.schema_version == "core.adversary.teamwork.v4":
        scope.update(workflow_version=run.schema_version,
                     native_gate_check=run.native_gate_check.model_dump(mode="json"))
    binding = {"schema": "adversary.host-episodes.v1", "path": str(path.absolute()),
               "scope_sha256": _program_digest(scope), "scope": scope}
    if existing and not path.is_file():
        raise ValueError("EPISODE_LEDGER_MISSING: resumption cannot reset admitted rounds")
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as ledger, ledger:
        ledger.execute("CREATE TABLE IF NOT EXISTS scope (binding TEXT NOT NULL)")
        ledger.execute("CREATE TABLE IF NOT EXISTS episodes (action_id TEXT PRIMARY KEY, ordinal INTEGER UNIQUE NOT NULL, result TEXT)")
        rows = ledger.execute("SELECT binding FROM scope").fetchall()
        if not rows:
            if existing:
                raise ValueError("EPISODE_LEDGER_MISSING")
            ledger.execute("INSERT INTO scope VALUES (?)", (json.dumps(binding, sort_keys=True),))
        elif len(rows) != 1 or json.loads(rows[0][0]) != binding:
            raise ValueError("EPISODE_SCOPE_MISMATCH")
    return binding


def _require_episode_binding(run: TeamworkRun) -> dict:
    binding = run.episode_binding
    if not binding or binding.get("schema") != "adversary.host-episodes.v1":
        raise ValueError("EPISODE_ADMISSION_REQUIRED: retain the original durable host ledger")
    if bind_episode_admission(run, Path(binding["path"]), existing=True) != binding:
        raise ValueError("EPISODE_SCOPE_MISMATCH")
    return binding


def _require_recheck_action(run: TeamworkRun, action: TeamworkAction) -> None:
    if next_action(run) != action or action.kind != "recheck":
        raise ValueError("RECHECK_NOT_PENDING")


def _claim_new_episode(ledger, run: TeamworkRun, action: TeamworkAction) -> None:
    count = ledger.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
    if count >= run.max_evaluations or count >= 10:
        raise ValueError("EVALUATION_LIMIT: stop before round eleven dispatch")
    if count != action.evaluations_used:
        raise ValueError("EPISODE_HISTORY_MISMATCH: the stopped state cannot reset admitted rounds")
    ledger.execute("INSERT INTO episodes (action_id, ordinal) VALUES (?, ?)", (action.action_id, count + 1))
    ledger.commit()


def _claim_episode(ledger, run: TeamworkRun, action: TeamworkAction):
    row = ledger.execute("SELECT result FROM episodes WHERE action_id = ?", (action.action_id,)).fetchone()
    if not row:
        _claim_new_episode(ledger, run, action)
        return None
    ledger.commit()
    if row[0] is None:
        raise ValueError("EPISODE_RECONCILIATION_REQUIRED: an interrupted evaluation remains claimed")
    return TeamworkObservation.model_validate_json(row[0])


def _admitted_failure_code(exc) -> str:
    observed_code = str(exc).split(":", 1)[0]
    if observed_code in {"ARTIFACT_CHANGED", "SOURCE_CHANGED", "CHECKER_CHANGED", "ACTION_MISMATCH"}:
        return observed_code
    return "CHECK_UNAVAILABLE"


def _admitted_failure_observation(action: TeamworkAction, exc) -> TeamworkObservation:
    code = _admitted_failure_code(exc)
    return TeamworkObservation(action_id=action.action_id, worker="admitted host checker",
        summary=f"Admitted evaluation unavailable: {code} ({type(exc).__name__})", blocked=True,
        artifacts=dict(action.artifacts), metadata={"role_id": action.role_id,
            "execution_kind": "host", "failure_code": code})


def _invoke_admitted_evaluator(action: TeamworkAction, timeout, evaluator):
    result = _execute_recheck(action, timeout=timeout) if evaluator is None else evaluator(action)
    if result.action_id != action.action_id:
        raise ValueError("ACTION_MISMATCH: the host evaluator must bind its admitted action")
    return result


def _run_admitted_evaluator(action: TeamworkAction, timeout, evaluator) -> TeamworkObservation:
    try:
        result = _invoke_admitted_evaluator(action, timeout, evaluator)
        _current_source(action)
        _current_checker(action)
        _current_artifacts(action.artifacts)
        return result
    except (ValueError, OSError, RuntimeError, TypeError) as exc:
        return _admitted_failure_observation(action, exc)


def _record_episode_timeout(result: TeamworkObservation, timeout) -> TeamworkObservation:
    if timeout == 60:
        return result
    return result.model_copy(update={"metadata": {**result.metadata, "host_check_timeout_seconds": timeout}})


def _store_episode_result(binding, action, result, timeout, sqlite3, closing) -> TeamworkObservation:
    with closing(sqlite3.connect(binding["path"])) as ledger, ledger:
        result = _record_episode_timeout(result, timeout)
        ledger.execute("UPDATE episodes SET result = ? WHERE action_id = ? AND result IS NULL",
                       (result.model_dump_json(), action.action_id))
    return result


def admitted_recheck(run: TeamworkRun, action: TeamworkAction, *, timeout=60, evaluator=None):
    """Claim the actual evaluation before dispatch; recovery never sends it twice."""
    import sqlite3
    from contextlib import closing

    _require_current_feedback(run)
    binding = _require_episode_binding(run)
    _require_recheck_action(run, action)
    from .teamwork_native_gates import validate_native_gate_context

    validate_native_gate_context(action)
    _current_source(action)
    _current_checker(action)
    _current_artifacts(action.artifacts)
    with closing(sqlite3.connect(binding["path"], isolation_level=None)) as ledger:
        ledger.execute("BEGIN IMMEDIATE")
        existing = _claim_episode(ledger, run, action)
    if existing is not None:
        return existing
    result = _run_admitted_evaluator(action, timeout, evaluator)
    return _store_episode_result(binding, action, result, timeout, sqlite3, closing)


def execute_host_action(run: TeamworkRun, action: TeamworkAction, *, output_dir=None):
    _require_current_feedback(run)
    if action.kind == "native_gates":
        from .teamwork_native_gates import execute_native_gates

        return execute_native_gates(run, action, output_dir=output_dir)
    if action.kind == "recheck":
        return admitted_recheck(run, action)
    if action.kind == "digest":
        return digest_current_run(run, action, output_dir=output_dir)
    if action.kind == "ddc_store":
        return store_ddc_program(run, action, output_dir=output_dir)
    if action.kind == "ddc_complete":
        return complete_ddc_program(run, action, output_dir=output_dir)
    raise ValueError("HOST_ACTION_REQUIRED: select the actual host check, digestion or DDC operation")
