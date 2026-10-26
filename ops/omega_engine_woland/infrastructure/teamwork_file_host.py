"""Apply one operator-selected text file for a bound remote executor.

The remote proposes artifact text or a review. This host writes only the path
the operator selected. It does not choose paths or execute model-supplied commands.
``execution_mode`` is the bound remote executor's provider template name.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from omega_engine_woland.infrastructure.native import DefaultNativeOperationPort
from omega_engine_woland.use_cases.checked_ddc_reuse import validate_checked_reuse_dispatch
from omega_engine_woland.use_cases.teamwork import TeamworkAction, TeamworkObservation
from omega_engine_woland.use_cases.teamwork_pfp import validate_teamwork_observation


def file_text_executor(remote, output: Path, *, expected_artifact_sha256=None,
                       recover_existing_artifact=False, run_reader=None, ddc_output_dir=None):
    """Host-owned single-file application, never arbitrary model tool execution."""
    expected_digest = expected_artifact_sha256

    def blocked(action, code, summary):
        return TeamworkObservation(action_id=action.action_id, worker="Python file host", blocked=True,
            summary=summary, metadata={"role_id": action.role_id, "failure_code": code})

    def execute(action: TeamworkAction) -> TeamworkObservation:
        nonlocal expected_digest
        if action.feedback_policy is None:
            return blocked(action, "LEGACY_FEEDBACK_READ_ONLY", "Historical actions cannot dispatch new work.")
        if action.communication == "host":
            if run_reader is not None and action.kind in ("native_gates", "recheck", "digest", "ddc_store", "ddc_complete"):
                from .teamwork_intelligence_host import execute_host_action

                return execute_host_action(run_reader(), action, output_dir=ddc_output_dir)
            return blocked(action, "HOST_ACTION_REQUIRED", "Use the bound host check or digestion operation.")
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
        validate_checked_reuse_dispatch(action, native_support=DefaultNativeOperationPort())
        if action.kind == "learn" and action.workflow_version in ("omega.woland.teamwork.v3", "omega.woland.teamwork.v4"):
            validate_ddc_context(action)
        before_candidate = (action.communication == "deterministic" or action.phase == "intake")
        if (output.exists() and not recover_existing_artifact
                and (action.kind == "build" or before_candidate and expected_digest is None)):
            return blocked(action, "OUTPUT_EXISTS",
                "OUTPUT_EXISTS: refusing a new provider dispatch for an existing artifact")
        recover_applied = False
        before_digest = None
        needs_readback = action.kind != "build" and not before_candidate and (
            expected_digest is not None or bool(action.artifacts))
        if needs_readback:
            try:
                raw = output.read_bytes()
            except OSError:
                return blocked(action, "ARTIFACT_UNAVAILABLE",
                    "ARTIFACT_UNAVAILABLE: cannot read the recorded candidate")
            before_digest = hashlib.sha256(raw).hexdigest()
            recover_applied = (action.kind == "repair" and before_digest != expected_digest
                and recover_existing_artifact
                and getattr(remote, "recover_only_action_id", None) == action.action_id)
            if before_digest != expected_digest and not recover_applied:
                return blocked(action, "ARTIFACT_CHANGED",
                    "ARTIFACT_CHANGED: file differs from the recorded candidate")
        result = remote(action)
        _current_source(action)
        _current_checker(action)
        validate_checked_reuse_dispatch(action, native_support=DefaultNativeOperationPort())
        reason = None
        if result.action_id != action.action_id:
            reason = "ACTION_MISMATCH: provider result does not bind the pending action"
        elif result.metadata.get("role_id") != action.role_id:
            reason = "RETINUE_ROLE_MISMATCH: provider result does not bind the pending role"
        elif needs_readback:
            try:
                if hashlib.sha256(output.read_bytes()).hexdigest() != before_digest:
                    reason = "ARTIFACT_CHANGED: file changed during the provider call"
            except OSError:
                reason = "ARTIFACT_UNAVAILABLE: file disappeared during the provider call"
        if reason:
            return result.model_copy(update={
                "action_id": action.action_id, "blocked": True, "summary": reason,
                "metadata": {**result.metadata, "reported_action_id": result.action_id,
                    "role_id": action.role_id, "failure_code": reason.split(":", 1)[0]},
            })
        if not result.blocked:
            # A caller can inject a remote callback. Reject its unmediated text
            # before the designated artifact is created or overwritten.
            validate_teamwork_observation(action, result)
        if not result.blocked and action.kind in ("build", "repair"):
            try:
                output.parent.mkdir(parents=True, exist_ok=True)
                if (action.kind == "build" and output.exists()) or recover_applied:
                    if (not recover_existing_artifact or not result.metadata.get("replayed_raw_reply")
                            or output.read_bytes() != result.content.encode("utf-8")):
                        raise ValueError("RECOVERED_ARTIFACT_MISMATCH")
                else:
                    with output.open("x" if action.kind == "build" else "w",
                                     encoding="utf-8", newline="\n") as handle:
                        handle.write(result.content)
                        handle.flush()
                        os.fsync(handle.fileno())
                expected_digest = hashlib.sha256(output.read_bytes()).hexdigest()
                result = result.model_copy(update={
                    "artifacts": {str(output.resolve()): expected_digest},
                    "metadata": {**result.metadata, "applied_by": "Python file host",
                        "host_summary": ("Python file host applied the acknowledged checked DDC candidate."
                            if action.brief and action.brief.checked_reuse_result is not None else
                            "Python file host wrote the provider's proposed artifact text.")},
                })
            except (OSError, ValueError) as exc:
                result = result.model_copy(update={
                    "blocked": True, "summary": f"ARTIFACT_WRITE_FAILED: {type(exc).__name__}",
                    "metadata": {**result.metadata, "role_id": action.role_id,
                        "failure_code": "ARTIFACT_WRITE_FAILED"},
                })
        return result

    execute.execution_mode = getattr(remote, "execution_mode", "openrouter")
    return execute
